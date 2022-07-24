import os
import random
import shutil
import subprocess
import time

import demjson
import numpy as np
import pydub
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pydub import AudioSegment as audio

from website.views import token_check, sendNotification, simpleUserInfo, upload_file
from ..forms import PronunciationForm
from ..models import Word, Character, Pronunciation, split
from django.utils import timezone
from word import translate
import requests
from pydub.silence import split_on_silence
from AudioCompare.main import audio_matcher, Arg
from .dto.pronunciation_all import pronunciation_all
from .dto.pronunciation_normal import pronunciation_normal


@csrf_exempt
def searchPronunciations(request):
    try:
        # PN0201 发音的批量获取
        if request.method == "GET":
            if ("token" in request.headers) and token_check(
                request.headers["token"], settings.JWT_KEY, -1
            ):
                pronunciations = Pronunciation.objects.all()
            else:
                pronunciations = Pronunciation.objects.filter(visibility=True)
            if "verifier" in request.GET:
                pronunciations = pronunciations.filter(
                    verifier__id=request.GET["verifier"]
                )
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
        elif request.method == "POST":
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY)
            if user:
                body = demjson.decode(request.body)
                body = body["pronunciation"]
                pronunciation_form = PronunciationForm(body)
                if pronunciation_form.is_valid():
                    pronunciation = pronunciation_form.save(commit=False)
                    pronunciation.word = Word.objects.get(id=body["word"])
                    pronunciation.contributor = user
                    pronunciation.save()
                    return JsonResponse({"id": pronunciation.id}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


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


@csrf_exempt
def managePronunciation(request, id):
    try:
        pronunciation = Pronunciation.objects.filter(id=id)
        if pronunciation.exists():
            pronunciation = pronunciation[0]
            # PN0101 获取发音信息
            if request.method == "GET":
                pronunciation.views += 1
                pronunciation.save()
                return JsonResponse(
                    {"pronunciation": pronunciation_all(pronunciation)},
                    status=200,
                )
            # PN0103 更改发音信息
            elif request.method == "PUT":
                token = request.headers["token"]
                if token_check(token, settings.JWT_KEY, pronunciation.contributor.id):
                    body = demjson.decode(request.body)
                    body = body["pronunciation"]
                    pronunciation_form = PronunciationForm(body)
                    for key in body:
                        if (key != "word") and len(pronunciation_form[key].errors.data):
                            return JsonResponse({}, status=400)
                    for key in body:
                        if key != "word":
                            setattr(pronunciation, key, body[key])
                        else:
                            pronunciation.word = Word.objects.get(id=body[key])
                    pronunciation.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
            # PN0104 删除发音
            elif request.method == "DELETE":
                token = request.headers["token"]
                user = token_check(
                    token, settings.JWT_KEY, pronunciation.contributor.id
                )
                if user:
                    if user != pronunciation.contributor:
                        body = demjson.decode(request.body)
                        message = body["message"] if "message" in body else "管理员操作"
                        content = (
                            f"您的语音(id = {pronunciation.id}) 已被删除，理由是：\n\t{message}"
                        )
                        sendNotification(
                            None,
                            [pronunciation.contributor],
                            content,
                            target=pronunciation,
                            title="【通知】语音处理结果",
                        )
                    pronunciation.delete()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
            else:
                return JsonResponse({}, status=405)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def managePronunciationVisibility(request, id):
    """
    管理员管理发音的visibility字段
    :param request:
    :return:
    """
    try:
        # PN0105 更改审核结果 PN0106审核语音
        if request.method in ["PUT", "POST"]:
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY, -1)
            if user:
                pro = Pronunciation.objects.filter(id=id)
                if pro.exists():
                    body = demjson.decode(request.body) if len(request.body) else {}
                    pro = pro[0]
                    if "result" in body:
                        pro.visibility = body["result"]
                    else:
                        pro.visibility ^= True
                    pro.verifier = user
                    if pro.visibility:
                        extra = f"，理由是:\n\t{body['reason']}" if "reason" in body else ""
                        content = f"恭喜您的语音(id ={id}) 已通过审核" + extra
                    else:
                        msg = body["reason"] if "reason" in body else body["message"]
                        content = f"很遗憾，您的语音(id = {id}) 没通过审核，理由是:\n\t{msg}"
                    sendNotification(
                        None,
                        [pro.contributor],
                        content=content,
                        target=pro,
                        title="【通知】语音审核结果",
                    )
                    pro.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=404)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


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
                        os.path.join(settings.SAVED_PINYIN, "submit")
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
