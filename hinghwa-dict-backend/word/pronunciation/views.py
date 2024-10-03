import os
import shutil
import time
import datetime
import demjson3
import numpy as np
import pydub
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import caches
from django.db.models import Q, Count, Max
from django.core.paginator import Paginator
from pydub import AudioSegment as audio
from rewards.transactions.dto import transactions_all
from user.models import User
from utils.token import get_request_user, token_pass, token_user
from user.dto.user_simple import user_simple
from utils.exception.types.bad_request import (
    BadRequestException,
    RankWithoutDays,
    InvalidPronunciation,
)
from utils.exception.types.not_found import (
    PronunciationNotFoundException,
    WordNotFoundException,
)

from website.views import token_check, sendNotification, simpleUserInfo, upload_file
from ..forms import PronunciationForm
from ..models import Word, Character, Pronunciation, split
from django.utils import timezone
from word.utils import translate
from pydub.silence import split_on_silence
from AudioCompare.main import audio_matcher, Arg
from .dto.pronunciation_all import pronunciation_all
from .dto.pronunciation_normal import pronunciation_normal
from utils.Rewards_action import (
    manage_points_in_pronunciation,
    revert_points_in_pronunciation,
)
from rewards.transactions.dto import transactions_all


# 从id中获取单条语音
def get_pronunciation_by_id(id: int) -> Pronunciation:
    pronunciations = Pronunciation.objects.filter(id=id)
    if not pronunciations.exists():
        raise PronunciationNotFoundException(id)
    return pronunciations[0]


class SearchPronunciations(View):
    # PN0201 发音的批量获取
    def get(self, request) -> JsonResponse:
        if ("token" in request.headers) and token_check(
            request.headers["token"], settings.JWT_KEY, -1
        ):
            pronunciations = Pronunciation.objects.all()
        else:
            pronunciations = Pronunciation.objects.filter(visibility=True)
        if "visibility" in request.GET:
            pronunciations = pronunciations.filter(
                visibility=request.GET["visibility"] == "true"
            )
        if "verifier" in request.GET:
            pronunciations = pronunciations.filter(verifier__id=request.GET["verifier"])
        if "granted" in request.GET:
            pronunciations = pronunciations.filter(
                verifier__isnull=request.GET["granted"] != "true"
            )
        if "word" in request.GET:
            pronunciations = pronunciations.filter(word__id=request.GET["word"])
        if "contributor" in request.GET:
            pronunciations = pronunciations.filter(
                contributor__id=request.GET["contributor"]
            )
        pronunciations = list(pronunciations)
        pronunciations.sort(key=lambda item: item.id)
        total = len(pronunciations)
        if ("order" in request.GET) and request.GET["order"] == "1":
            pronunciations.reverse()
        if "pageSize" in request.GET:
            pageSize = int(request.GET["pageSize"])
            page = int(request.GET["page"])
            r = min(len(pronunciations), page * pageSize)
            l = min(len(pronunciations) + 1, (page - 1) * pageSize)
            pronunciations = pronunciations[l:r]
        result = []
        for pronunciation in pronunciations:
            result.append(
                {
                    "pronunciation": pronunciation_normal(pronunciation),
                    "contributor": simpleUserInfo(pronunciation.contributor),
                }
            )
        return JsonResponse({"pronunciation": result, "total": total}, status=200)

    # PN0102 增加一条语音
    def post(self, request) -> JsonResponse:
        token = token_pass(request.headers)
        user = token_user(token)
        body = demjson3.decode(request.body)
        body = body["pronunciation"]
        pronunciation_form = PronunciationForm(body)
        if not pronunciation_form.is_valid():
            raise InvalidPronunciation()
        pronunciation = pronunciation_form.save(commit=False)
        try:
            pronunciation.word = Word.objects.get(id=body["word"])
        except:
            raise WordNotFoundException(body["word"])
        pronunciation.contributor = user
        pronunciation.save()
        return JsonResponse({"id": pronunciation.id}, status=200)


@csrf_exempt
def combinePronunciation(request, ipa):
    try:
        # PN0202 获取ipa发音
        if request.method == "GET":
            submit_list = os.listdir(os.path.join(settings.SAVED_PINYIN, "submit"))
            available = []
            for file in submit_list:
                if file.endswith(".mp3"):
                    available.append(file.replace(".mp3", ""))
            available = set(available)
            ipa = split(ipa)
            ans = [
                (len(p.ipa), p.contributor.username, p.source)
                for p in Pronunciation.objects.filter(ipa=ipa).filter(visibility=True)
            ]
            ans.sort(key=lambda x: x[0])
            # 这部分直接拷贝下面的V2的代码
            inputs = []
            for ipa1 in ipa.split(" "):
                inputs.append({translate.IPA_to_pinyin(ipa1)})
            results = []
            for alt_pinyin in inputs:
                if len(alt_pinyin & available) > 0:
                    result = {
                        "pinyin": list(alt_pinyin & available)[0],
                        "dir": os.path.join(settings.SAVED_PINYIN, "submit"),
                    }
                else:
                    result = {
                        "pinyin": list(alt_pinyin)[0],
                        "dir": os.path.join(settings.SAVED_PINYIN, "combine"),
                    }
                results.append(result)
            dir = os.path.join(settings.MEDIA_ROOT, "audio", "public")
            if not os.path.exists(dir):
                os.makedirs(dir)
            time = timezone.now().__format__("%Y_%m_%d")
            filename = (
                time + "_" + ("".join([item["pinyin"] for item in results])) + ".mp3"
            )
            path = os.path.join(dir, filename)
            result = MergeAudio(results, path)
            if result == 0:
                key = "files/audio/public/" + filename.replace("_", "/")
                tts = upload_file(path, key)
            else:
                tts = "null"

            if len(ans):
                ans = ans[0]
                return JsonResponse(
                    {"contributor": ans[1], "url": ans[2], "tts": tts}, status=200
                )
            else:
                return JsonResponse(
                    {"contributor": "null", "url": "null", "tts": tts}, status=200
                )
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


def MergeAudio(pinyins, path):
    """
    根据拼音列表剪辑mp3文件
    :param pinyins:拼音列表[{pinyin,dir}]
    :return: 返回结果0表示成功
    """
    try:
        target = pydub.AudioSegment.silent(duration=100, frame_rate=44100)
        for item in pinyins:
            file = os.path.join(item["dir"], item["pinyin"] + ".mp3")
            music = audio.from_file(file)
            music.set_frame_rate(44100)
            target += music
        target.export(path, format="mp3")
        return 0
    except Exception as msg:
        return str(msg)


@csrf_exempt
def combinePronunciationV2(request):
    try:
        # PN0203 获取发音
        if request.method == "GET":
            submit_list = os.listdir(os.path.join(settings.SAVED_PINYIN, "submit"))
            # secondary 即保证拼音对，不保证音调的正确性
            available = []
            secondary_list = []
            for file in submit_list:
                if file.endswith(".mp3"):
                    available.append(file.replace(".mp3", ""))
                    secondary_list.append(file.replace(".mp3", "")[:-1])
            available = set(available)
            secondary = set(secondary_list)
            inputs = []
            secondary_inputs = []
            if "words" in request.GET:
                result = Character.objects.filter(character__in=request.GET["words"])
                dic = {}
                dic1 = {}
                for character in request.GET["words"]:
                    dic[character] = set()
                    dic1[character] = set()
                for character in result:
                    dic[character.character].add(character.pinyin)
                    dic1[character.character].add(character.pinyin[:-1])
                for character in request.GET["words"]:
                    inputs.append(dic[character])
                    secondary_inputs.append(dic1[character])
            elif "ipas" in request.GET:
                ipas = split(request.GET["ipas"]).split(" ")
                for ipa in ipas:
                    inputs.append({translate.IPA_to_pinyin(ipa)})
                    secondary_inputs.append({translate.IPA_to_pinyin(ipa)[:-1]})
            elif "pinyins" in request.GET:
                pinyins = split(request.GET["pinyins"]).split(" ")
                for pinyin in pinyins:
                    inputs.append({pinyin})
                    secondary_inputs.append({pinyin[:-1]})
            results = []
            for alt_pinyin, secondary_pinyin in zip(inputs, secondary_inputs):
                if len(alt_pinyin & available) > 0:
                    result = {
                        "pinyin": list(alt_pinyin & available)[0],
                        "dir": os.path.join(settings.SAVED_PINYIN, "submit"),
                    }
                elif len(secondary_pinyin & secondary) > 0:
                    temp = list(secondary_pinyin & secondary)
                    a = list(alt_pinyin)
                    mi = 8
                    for x in temp:
                        shengdiaos = []
                        for y in a:
                            if y.startswith(x):
                                shengdiaos.append(int(y[-1]))
                        for i in range(1, 8):
                            pinyin = x + str(i)
                            if pinyin in available:
                                for shengdiao in shengdiaos:
                                    if abs(shengdiao - i) < mi:
                                        mi = abs(shengdiao - i)
                                        optimize_pinyin = pinyin
                    result = {
                        "pinyin": optimize_pinyin,
                        "dir": os.path.join(settings.SAVED_PINYIN, "submit"),
                    }
                else:
                    result = {
                        "pinyin": list(alt_pinyin)[0],
                        "dir": os.path.join(settings.SAVED_PINYIN, "combine"),
                    }
                results.append(result)
            dir = os.path.join(settings.MEDIA_ROOT, "audio", "public")
            if not os.path.exists(dir):
                os.makedirs(dir)
            time = timezone.now().__format__("%Y_%m_%d")
            filename = (
                time + "_" + ("".join([item["pinyin"] for item in results])) + ".mp3"
            )
            path = os.path.join(dir, filename)
            result = MergeAudio(results, path)
            if result == 0:
                key = "files/audio/public/" + filename.replace("_", "/")
                url = upload_file(path, key)
                return JsonResponse({"url": url}, status=200)
            else:
                return JsonResponse({"msg": f"Merge fail,msg:{result}"}, status=500)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


class ManagePronunciation(View):
    # PN0101 获取发音信息
    def get(self, request, id):
        pronunciation = get_pronunciation_by_id(id)
        pronunciation.views += 1
        pronunciation.save()
        return JsonResponse(
            {"pronunciation": pronunciation_all(pronunciation)},
            status=200,
        )

    # PN0103 更改发音信息
    def put(self, request, id):
        token_pass(request.headers, -1)
        pronunciation = get_pronunciation_by_id(id)
        body = demjson3.decode(request.body) if len(request.body) else {}
        if "pronunciation" not in body:
            return BadRequestException("缺少pronunciation字段")
        pronunciation_form = PronunciationForm(body["pronunciation"])
        for key in body["pronunciation"]:
            if (key != "word") and len(pronunciation_form[key].errors.data):
                return BadRequestException()
        for key in body["pronunciation"]:
            if key != "word":
                setattr(pronunciation, key, body["pronunciation"][key])
            else:
                pronunciation.word = Word.objects.get(id=body["pronunciation"][key])
        pronunciation.save()
        return JsonResponse({}, status=200)

    # PN0104 删除发音
    def delete(self, request, id):
        token_pass(request.headers, -1)
        pronunciation = get_pronunciation_by_id(id)
        body = demjson3.decode(request.body) if len(request.body) else {}
        if "message" in body:
            message = body["message"]
        else:
            return BadRequestException("缺失改变审核结果的理由")
        pronunciation.delete()
        sendNotification(
            get_request_user(request),
            [pronunciation.contributor],
            f"您的语音(id={pronunciation.id}) 已被删除，理由是：\n\t{message}",
            action_object=pronunciation,
            title=f"【通知】语音{pronunciation.word.word}被删除",
        )

        return JsonResponse({}, status=200)


class ManageApproval(View):
    # PN0106 审核语音
    def post(self, request, id):
        token_pass(request.headers, -1)
        verifier = get_request_user(request)
        body = demjson3.decode(request.body) if len(request.body) else {}
        if "result" in body:
            result = body["result"]
        else:
            return BadRequestException("缺失审核结果")
        if "reason" in body:
            reason = "，理由是" + body["reason"] + "。"
        else:
            if result == False:
                return BadRequestException("缺失审核不通过的理由")
            reason = ""
        pronunciation = get_pronunciation_by_id(id)
        pronunciation.visibility = result
        pronunciation.verifier = verifier
        pronunciation.save()
        pro = f"语音(id={id})"
        contributor = pronunciation.contributor
        if result:
            content = f"恭喜您，您的语音{pro}审核通过"
            transaction = manage_points_in_pronunciation(contributor.id)
        else:
            content = f"很遗憾，您的语音{pro}审核未通过"
        sendNotification(
            verifier,
            [contributor],
            content=content + reason,
            action_object=pronunciation,
            title=f"【通知】语音（{pronunciation.word.word}）审核结果",
        )
        return JsonResponse(transaction, status=200)

    # PN0105 更改审核结果
    def put(self, request, id):
        token_pass(request.headers, -1)
        verifier = get_request_user(request)
        body = demjson3.decode(request.body) if len(request.body) else {}
        if "message" in body:
            message = body["message"]
        else:
            return BadRequestException("缺失改变审核结果的理由")
        pronunciation = get_pronunciation_by_id(id)
        pronunciation.visibility ^= True
        pronunciation.verifier = verifier
        pronunciation.save()
        pro = f"语音(id={id})"
        contributor = pronunciation.contributor
        if pronunciation.visibility:
            content = f"恭喜您，您的语音{pro}其审核已变更为通过"
            transaction_info = manage_points_in_pronunciation(contributor.id)
        else:
            content = f"很遗憾，您的语音{pro}其审核已变更为未通过"
            transaction_info = revert_points_in_pronunciation(contributor.id)
        sendNotification(
            verifier,
            [contributor],
            content=content + f"，理由是:{message}。",
            action_object=pronunciation,
            title=f"【通知】语音（{pronunciation.word.word}）审核结果变更",
        )
        return JsonResponse(transaction_info, status=200)


def split_silence(music, rate=0.22):
    musics = np.nan_to_num(
        sorted([db.dBFS for db in music[:]], reverse=True), neginf=-90
    )
    thresh = musics.mean() + 1.8 * musics.std()
    results = split_on_silence(
        music, silence_thresh=thresh, keep_silence=0, min_silence_len=11
    )
    # for idx, result in enumerate(results):
    #     result.export(f'{idx}.mp3', format='mp3')
    return results


import pickle


@csrf_exempt
def translatePronunciation(request):
    try:
        # PN0204 以音查字
        if request.method == "POST":
            # path = os.path.join(settings.BASE_DIR, 'temp')
            # if not os.path.exists(path):
            #     submit_list = os.listdir(os.path.join(settings.SAVED_PINYIN, 'submit'))
            #     available_pinyin = {}
            #     for file in submit_list:
            #         if file.endswith('.mp3'):
            #             music = audio.from_file(os.path.join(settings.SAVED_PINYIN, 'submit', file))
            #             pinyin = file.replace('.mp3', '')
            #             available_pinyin[pinyin] = [db.dBFS for db in music[:]]
            #     with open(path, 'wb') as f:
            #         pickle.dump(available_pinyin, f)
            # else:
            #     with open(path, 'rb') as f:
            #         available_pinyin = pickle.load(f)
            file = request.FILES.get("file")
            music = audio.from_file(file)
            music.set_frame_rate(44100)
            videos = split_silence(music)
            ans = ""
            workingdir = os.path.join(settings.MEDIA_ROOT, "audio", "temp")
            if not os.path.exists(workingdir):
                os.makedirs(workingdir)
            ls = []
            for video in videos:
                filename = str(int(time.time() * 1000000)) + ".wav"
                video.export(os.path.join(workingdir, filename), format="wav")
                ls.append(filename)
            # command = f'{os.path.join(settings.BASE_DIR, "AudioCompare", "main.py")}' \
            #           f' -d {os.path.join(settings.MEDIA_ROOT, "audio", "temp")}' \
            #           f' -d {os.path.join(settings.BASE_DIR, "AudioCompare", "submit")}'
            # process = subprocess.Popen('python ' + command, stdout=subprocess.PIPE, shell=False,
            #                            cwd=f'{os.path.join(settings.BASE_DIR, "AudioCompare")}')
            # process.wait()
            result = audio_matcher(
                Arg(
                    [
                        os.path.join(settings.MEDIA_ROOT, "audio", "temp"),
                        os.path.join(settings.SAVED_PINYIN, "submit"),
                        # os.path.join(settings.BASE_DIR, "AudioCompare", "submit")
                    ]
                )
            )
            for key in ls:
                if result[key]:
                    word = Character.objects.filter(pinyin=result[key].split(".")[0])
                    if word.exists():
                        ans += word[0].character
                    else:
                        ans += "?"
                else:
                    ans += "?"
            shutil.rmtree(workingdir)
            return JsonResponse({"word": ans}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


class PronunciationRanking(View):
    # PN0205 语音上传榜单
    def get(self, request) -> JsonResponse:
        days = request.GET["days"]  # 要多少天的榜单
        page = request.GET.get("page", 1)  # 获取页面数，默认为第1页
        pagesize = request.GET.get("pageSize", 10)  # 获取每页显示数量，默认为10条
        if not days:
            raise RankWithoutDays()
        days = int(days)
        try:
            token = token_pass(request.headers)
            user: User = token_user(token)
            my_id = user.id
        except:
            my_id = 0
        my_amount = 0
        my_rank = 0
        rank_count = 0
        result_json_list = []
        paginator = Pages(self.get_rank_queries(days), pagesize)
        current_page = paginator.get_page(page)
        adjacent_pages = list(
            paginator.get_adjacent_pages(current_page, adjancent_pages=3)
        )

        for rank_q in self.get_rank_queries(days):
            con_id = rank_q["contributor_id"]
            amount = rank_q["pronunciation_count"]
            rank_count = rank_count + 1
            if con_id == my_id:
                my_amount = amount
                my_rank = rank_count
            result_json_list.append(
                {
                    "contributor": user_simple(User.objects.filter(id=con_id)[0]),
                    "amount": amount,
                }
            )
        # 发送给前端
        return JsonResponse(
            {
                "ranking": result_json_list,
                "me": {"amount": my_amount, "rank": my_rank},
                "pagination": {
                    "total_pages": paginator.num_pages,
                    "current_page": current_page.number,
                    "page_size": pagesize,
                    "previous_page": current_page.has_previous(),
                    "next_page": current_page.has_next(),
                    "adjacent_pages": adjacent_pages,
                },
            },
            status=200,
        )

    @classmethod
    def get_rank_queries(cls, days):
        rank_cache = caches["pronunciation_ranking"]
        rank_queries = rank_cache.get(str(days))
        if rank_queries is None:
            # 发现缓存中没有要查询的天数的榜单，更新榜单，并把更新的表格录入到数据库缓存中pronunciation_ranking表的对应位置
            rank_queries = cls.update_rank(days)
            rank_cache.set(str(days), rank_queries)
        return rank_queries

    @classmethod
    def update_rank(cls, search_days):  # 不包括存储在数据库中
        if search_days != 0:
            start_date = timezone.now() - datetime.timedelta(days=search_days)
            # 查询上传时间不是空的并且上传时间在规定开始时间之后的
            result = (
                Pronunciation.objects.filter(
                    Q(upload_time__isnull=False)
                    & Q(upload_time__gt=start_date)
                    & Q(visibility=True)
                )
                .values("contributor_id")
                .annotate(
                    pronunciation_count=Count("contributor_id"),
                    last_date=Max("upload_time"),
                )
                .order_by("-pronunciation_count", "-last_date")
            )
        else:
            result = (
                Pronunciation.objects.filter(visibility=True)
                .values("contributor_id")
                .annotate(
                    pronunciation_count=Count("contributor_id"),
                    last_date=Max("upload_time"),
                )
                .order_by("-pronunciation_count", "-last_date")
            )
        return result  # 返回的是Queries


class Pages(Paginator):
    # 对原有的Paginator类进行扩展，获取当前页的相邻页面
    def get_adjacent_pages(self, current_page, adjancent_pages=3):
        current_page = current_page.number
        start_page = max(current_page - adjancent_pages, 1)  # 前面的页码数
        end_page = min(current_page + adjancent_pages, self.num_pages)  # 后面的页码数
        return range(start_page, end_page + 1)
