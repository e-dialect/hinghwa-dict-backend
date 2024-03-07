import os
import re

import demjson
import xlrd
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .dto.character_simple import character_simple
from website.views import token_check, filterInOrder
from ..forms import CharacterForm
from ..models import Word, Character, Pronunciation
from .dto.character_normal import character_normal
from .dto.character_all import character_all


@csrf_exempt
def searchCharacters(request):
    try:
        if request.method == "GET":
            characters = Character.objects.all()
            if "shengmu" in request.GET:
                characters = characters.filter(shengmu=request.GET["shengmu"])
            if "yunmu" in request.GET:
                characters = characters.filter(yunmu=request.GET["yunmu"])
            if "shengdiao" in request.GET:
                characters = characters.filter(shengdiao=request.GET["shengdiao"])
            characters = [character.id for character in characters]
            return JsonResponse({"characters": characters}, status=200)
        elif request.method == "POST":
            body = demjson.decode(request.body)
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY, -1)
            if user:
                body = body["character"]
                character_form = CharacterForm(body)
                if character_form.is_valid():
                    character = character_form.save(commit=False)
                    if "type" in body:
                        character.type = body["type"]
                    character.save()
                    return JsonResponse({"id": character.id}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        elif request.method == "PUT":
            body = demjson.decode(request.body)
            result = Character.objects.filter(id__in=body["characters"])
            characters = []
            result = filterInOrder(result, body["characters"])
            for character in result:
                characters.append({character_normal(character)})
            return JsonResponse({"characters": characters}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


def searchCharactersPinyin(request):
    """
    其实就是seachCharacters方法的get接口不够用了，要增加多一个功能类似但是返回不同的
    """
    try:
        if request.method == "GET":
            characters = Character.objects.all()
            if "shengmu" in request.GET:
                characters = characters.filter(shengmu=request.GET["shengmu"])
            if "yunmu" in request.GET:
                characters = characters.filter(yunmu=request.GET["yunmu"])
            if "shengdiao" in request.GET:
                characters = characters.filter(shengdiao=request.GET["shengdiao"])
            result = {}
            pinyin_list = []
            for item in characters:
                if ((item.pinyin, item.character) not in result) or (
                        item.town == "城里" and item.county == "莆田"
                ):
                    result[(item.pinyin, item.character, item.traditional)] = item
                    pinyin_list.append(item.pinyin)
            # 实现逻辑是将所有Word和Pronunciation按pinyin归类
            # 然后将result的pinyin去匹配他们，要求语音的pinyin一致，字词的pinyin和character一致
            # 提前归类有利于减少索引负载
            result1 = {}
            words_dict = {}
            pronunciations_dict = {}
            for item in Word.objects.filter(standard_pinyin__in=pinyin_list).filter(
                    visibility=True
            ):
                if item.standard_pinyin not in words_dict:
                    words_dict[item.standard_pinyin] = []
                words_dict[item.standard_pinyin].append(item)
            for item in Pronunciation.objects.filter(pinyin__in=pinyin_list).filter(
                    visibility=True
            ):
                if item.pinyin not in pronunciations_dict:
                    pronunciations_dict[item.pinyin] = item
            t = 0
            for (pinyin, character, traditional), item in result.items():
                if pinyin not in result1:
                    pronunciation = (
                        pronunciations_dict[pinyin].source
                        if pinyin in pronunciations_dict
                        else None
                    )
                    result1[pinyin] = {
                        "pinyin": pinyin,
                        "source": pronunciation,
                        "characters": [],
                    }
                word = None
                if pinyin in words_dict:
                    for item in words_dict[pinyin]:
                        if item.word == character:
                            word = item.id
                            break
                result1[pinyin]["characters"].append(
                    {"character": character, "word": word, "traditional": traditional}
                )
                unique_result = []
                exist_set = set()
                for item in result1.values():
                    if item["pinyin"] not in exist_set:
                        unique_result.append(item)
                        exist_set.add(item["pinyin"])
            return JsonResponse({"result": list(result1.values())}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def searchEach(request):
    try:
        if request.method == "GET":
            search = request.GET["search"]
            result = Character.objects.filter(character__in=search)
            dic = {}
            for character in search:
                dic[character] = []
            for character in result:
                dic[character.character].append({character_normal(character)})
            ans = []
            for character in dic.keys():
                ans.append({"label": character, "characters": dic[character]})
            return JsonResponse({"characters": ans}, status=200)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def searchEachV2(request):
    try:
        if request.method == "GET":
            search = request.GET["search"]
            result = Character.objects.filter(
                Q(character__in=search) | Q(traditional__in=search)
            )
            dic = {}
            scores = {}
            for idx, character in enumerate(search):
                if character not in scores:
                    scores[character] = idx * 10
            for character in result:
                word = Word.objects.filter(standard_pinyin=character.pinyin).filter(
                    word=character.character
                )
                word = word[0].id if word.exists() else None
                source = Pronunciation.objects.filter(pinyin=character.pinyin)
                source = source[0].source if source.exists() else None
                if character.character not in scores:
                    scores[character.character] = 1000
                if character.traditional not in scores:
                    scores[character.traditional] = 1000
                score = min(scores[character.character], scores[character.traditional])
                if (score, character.character, character.traditional) not in dic:
                    dic[(score, character.character, character.traditional)] = []
                dic[(score, character.character, character.traditional)].append(
                    character_all(character, word, source)
                )
            ans = []
            dict_list = sorted(dic.keys())
            for score, character, traditional in dict_list:
                new_dic = {}
                for item in dic[(score, character, traditional)]:
                    if (item["county"], item["town"]) not in new_dic:
                        new_dic[(item["county"], item["town"])] = []
                    new_dic[(item["county"], item["town"])].append(item)
                result = []
                for (county, town), value in new_dic.items():
                    result.append({"county": county, "town": town, "characters": value})
                ans.append(
                    {
                        "label": character,
                        "traditional": traditional,
                        "characters": result,
                    }
                )
            return JsonResponse({"characters": ans}, status=200)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def manageCharacter(request, id):
    try:
        character = Character.objects.filter(id=id)
        if character.exists():
            character = character[0]
            if request.method == "GET":
                return JsonResponse(
                    {"character": character_normal(character)},
                    status=200,
                )
            elif request.method == "PUT":
                body = demjson.decode(request.body)
                token = request.headers["token"]
                if token_check(token, settings.JWT_KEY, -1):
                    body = body["character"]
                    character_form = CharacterForm(body)
                    for key in body:
                        if len(character_form[key].errors.data):
                            return JsonResponse({}, status=400)
                    for key in body:
                        setattr(character, key, body[key])
                    character.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
            elif request.method == "DELETE":
                token = request.headers["token"]
                if token_check(token, settings.JWT_KEY, -1):
                    character.delete()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
            else:
                return JsonResponse({}, status=405)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@require_POST
@csrf_exempt
def load_character(request):
    try:
        body = demjson.decode(request.body)
        token = request.headers["token"]
        user = token_check(token, settings.JWT_KEY, -1)
        if user:
            file = body["file"]
            flush = body["flush"]
            if flush:
                Character.objects.all().delete()
            sheet = xlrd.open_workbook(
                os.path.join("material", "character", file)
            ).sheet_by_index(0)
            lines = sheet.nrows
            col = sheet.ncols
            title = sheet.row(0)
            for line in range(1, lines):
                info = sheet.row(line)
                dic = {}
                for i in range(col):
                    dic[title[i].value] = info[i].value
                character_form = CharacterForm(dic)
                if character_form.is_valid():
                    character = character_form.save(commit=True)
                    if character.id % 100 == 0:
                        print("load character {}".format(character.id))
                else:
                    raise Exception("add fail in {}".format(dic))
            return JsonResponse({}, status=200)
        else:
            return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


def searchCharactersPinYinV2(request):
    try:
        if request.method == "GET":
            content = request.GET["search"]
            search = re.findall(r"[a-zA-Z]+\d*", content)
            result = []
            for key in search:
                characters = Character.objects.filter(pinyin__icontains=key)
                for character in characters:
                    result.append(character_simple(character))
            return JsonResponse(
                {"total": len(result), "characters": result}, status=200
            )
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)
