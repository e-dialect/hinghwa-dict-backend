import csv
import os

import demjson
import xlrd
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from article.models import Article
from website.views import evaluate, token_check, sendNotification, simpleUserInfo, filterInOrder
from .forms import WordForm, CharacterForm, PronunciationForm, ApplicationForm
from .models import Word, Character, Pronunciation, User, Application
from django.db.models import Q


@csrf_exempt
def searchWords(request):
    try:
        if request.method == 'GET':
            words = Word.objects.filter(visibility=True)
            if 'contributor' in request.GET:
                words = words.filter(contributor=request.GET['contributor'])
            if 'search' in request.GET:
                result = []
                key = request.GET['search'].replace(' ', '')
                if not key[0].isalnum():
                    weights = [3.5, 2.5, 2, 1, 0.5, 0.5]
                    alpha = 1
                else:
                    weights = [2, 1, 0.5, 0.5, 3, 3]
                    alpha = 1
                for word in words:
                    if word.id == 4086:
                        t = 1
                    score = evaluate(list(zip([word.word, word.definition, word.mandarin,
                                               word.annotation, word.standard_pinyin, word.standard_ipa], weights))
                                     , key, alpha=alpha)
                    if score > 0:
                        result.append((word, score))
                result.sort(key=lambda a: a[1], reverse=True)
                if len(result) > 200:
                    result = result[:200]
                words = list(zip(*result))[0]
            result = [{'id': word.id, 'word': word.word, 'definition': word.definition,
                       'annotation': word.annotation, 'mandarin': eval(word.mandarin) if word.mandarin else [],
                       'standard_ipa': word.standard_ipa, 'standard_pinyin': word.standard_pinyin} for word in words]
            words = [word.id for word in words]
            return JsonResponse({"result": result, "words": words}, status=200)
        elif request.method == 'POST':
            body = demjson.decode(request.body)
            token = request.headers['token']
            user = token_check(token, 'dxw', -1)
            if user:
                body = body['word']
                word_form = WordForm(body)
                if word_form.is_valid() and isinstance(body['mandarin'], list):
                    for id in body['related_articles']:
                        Article.objects.get(id=id)
                    for id in body['related_words']:
                        Word.objects.get(id=id)
                    word = word_form.save(commit=False)
                    word.contributor = user
                    word.visibility = True
                    word.save()
                    for id in body['related_articles']:
                        article = Article.objects.get(id=id)
                        word.related_articles.add(article)
                    for id in body['related_words']:
                        wordx = Word.objects.get(id=id)
                        word.related_words.add(wordx)
                    return JsonResponse({'id': word.id}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        elif request.method == "PUT":
            body = demjson.decode(request.body)
            words = []
            result = Word.objects.filter(id__in=body['words'])
            result = filterInOrder(result, body['words'])
            for word in result:
                pronunciations = word.pronunciation.filter(ipa__iexact=word.standard_ipa.strip()) \
                    .filter(visibility=True)
                if pronunciations.exists():
                    pronunciation = pronunciations[0].source
                else:
                    pronunciations = Pronunciation.objects.filter(ipa__iexact=word.standard_ipa.strip()) \
                        .filter(visibility=True)
                    if pronunciations.exists():
                        pronunciation = pronunciations[0].source
                    else:
                        pronunciation = 'null'
                words.append({'word': {"id": word.id, 'word': word.word, 'definition': word.definition,
                                       "contributor": word.contributor.id, "annotation": word.annotation,
                                       "standard_ipa": word.standard_ipa,
                                       "standard_pinyin": word.standard_pinyin,
                                       "mandarin": eval(word.mandarin) if word.mandarin else [],
                                       "views": word.views},
                              'contributor': simpleUserInfo(word.contributor),
                              'pronunciation': {
                                  'url': pronunciation,
                                  'tts': 'null'
                              }})
            return JsonResponse({"words": words}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def manageWord(request, id):
    try:
        word = Word.objects.filter(id=id)
        if word.exists():
            word = word[0]
            if request.method == 'GET':
                related_words = [{"id": word.id, 'word': word.word} for word in word.related_words.all()]
                related_articles = [{"id": article.id, 'title': article.title}
                                    for article in word.related_articles.all()]
                word.views = word.views + 1
                word.save()
                user = word.contributor
                source = Pronunciation.objects.filter(ipa=word.standard_ipa).filter(visibility=True)
                source = source[0].source if source.exists() else None
                return JsonResponse({"word": {"id": word.id, 'word': word.word, 'definition': word.definition,
                                              "contributor": {"id": user.id, 'username': user.username,
                                                              'nickname': user.user_info.nickname,
                                                              'email': user.email,
                                                              'telephone': user.user_info.telephone,
                                                              'registration_time': user.date_joined.__format__(
                                                                  '%Y-%m-%d %H:%M:%S'),
                                                              'login_time': user.last_login.__format__(
                                                                  '%Y-%m-%d %H:%M:%S') if user.last_login else '',
                                                              'birthday': user.user_info.birthday,
                                                              'avatar': user.user_info.avatar,
                                                              'county': user.user_info.county,
                                                              'town': user.user_info.town,
                                                              'is_admin': user.is_superuser},
                                              "annotation": word.annotation,
                                              "standard_ipa": word.standard_ipa,
                                              "standard_pinyin": word.standard_pinyin,
                                              "mandarin": eval(word.mandarin) if word.mandarin else [],
                                              "related_words": related_words, "related_articles": related_articles,
                                              "views": word.views,
                                              'source': source}}, status=200)
            elif request.method == 'PUT':
                body = demjson.decode(request.body)
                token = request.headers['token']
                if token_check(token, 'dxw', word.contributor.id):
                    body = body['word']
                    word_form = WordForm(body)
                    for key in body:
                        if (key in word_form) and len(word_form[key].errors.data):
                            return JsonResponse({}, status=400)
                    for key in body:
                        if key != 'related_words' and key != 'related_articles':
                            setattr(word, key, body[key])
                        elif key == 'related_words':
                            for id in body['related_words']:
                                Word.objects.get(id=id)
                            word.related_words.clear()
                            for id in body['related_words']:
                                wordx = Word.objects.get(id=id)
                                word.related_words.add(wordx)
                        elif key == 'related_articles':
                            for id in body['related_articles']:
                                Article.objects.get(id=id)
                            word.related_articles.clear()
                            for id in body['related_articles']:
                                article = Article.objects.get(id=id)
                                word.related_articles.add(article)
                    word.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
            elif request.method == 'DELETE':
                token = request.headers['token']
                if token_check(token, 'dxw', word.contributor.id):
                    word.delete()
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
def searchCharacters(request):
    try:
        if request.method == 'GET':
            characters = Character.objects.all()
            if 'shengmu' in request.GET:
                characters = characters.filter(shengmu=request.GET['shengmu'])
            if 'yunmu' in request.GET:
                characters = characters.filter(yunmu=request.GET['yunmu'])
            if 'shengdiao' in request.GET:
                characters = characters.filter(shengdiao=request.GET['shengdiao'])
            characters = [character.id for character in characters]
            return JsonResponse({"characters": characters}, status=200)
        elif request.method == 'POST':
            body = demjson.decode(request.body)
            token = request.headers['token']
            user = token_check(token, 'dxw', -1)
            if user:
                body = body['character']
                character_form = CharacterForm(body)
                if character_form.is_valid():
                    character = character_form.save(commit=False)
                    character.save()
                    return JsonResponse({'id': character.id}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        elif request.method == "PUT":
            body = demjson.decode(request.body)
            result = Character.objects.filter(id__in=body['characters'])
            characters = []
            result = filterInOrder(result, body['characters'])
            for character in result:
                characters.append({"id": character.id, 'shengmu': character.shengmu, 'ipa': character.ipa,
                                   'pinyin': character.pinyin, 'yunmu': character.yunmu,
                                   'shengdiao': character.shengdiao,
                                   'character': character.character, 'county': character.county,
                                   'town': character.town, 'traditional': character.traditional})
            return JsonResponse({"characters": characters}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


def searchCharactersPinyin(request):
    '''
        其实就是seachCharacters方法的get接口不够用了，要增加多一个功能类似但是返回不同的
    '''
    try:
        if request.method == 'GET':
            characters = Character.objects.all()
            if 'shengmu' in request.GET:
                characters = characters.filter(shengmu=request.GET['shengmu'])
            if 'yunmu' in request.GET:
                characters = characters.filter(yunmu=request.GET['yunmu'])
            if 'shengdiao' in request.GET:
                characters = characters.filter(shengdiao=request.GET['shengdiao'])
            result = {}
            pinyin_list = []
            for item in characters:
                if ((item.pinyin, item.character) not in result) or \
                        (item.town == '城里' and item.county == '莆田'):
                    result[(item.pinyin, item.character, item.traditional)] = item
                    pinyin_list.append(item.pinyin)
            # 实现逻辑是将所有Word和Pronunciation按pinyin归类
            # 然后将result的pinyin去匹配他们，要求语音的pinyin一致，字词的pinyin和character一致
            # 提前归类有利于减少索引负载
            result1 = {}
            words_dict = {}
            pronunciations_dict = {}
            for item in Word.objects.filter(standard_pinyin__in=pinyin_list).filter(visibility=True):
                if item.standard_pinyin not in words_dict:
                    words_dict[item.standard_pinyin] = []
                words_dict[item.standard_pinyin].append(item)
            for item in Pronunciation.objects.filter(pinyin__in=pinyin_list).filter(visibility=True):
                if item.pinyin not in pronunciations_dict:
                    pronunciations_dict[item.pinyin] = item
            t = 0
            for (pinyin, character, traditional), item in result.items():
                if pinyin not in result1:
                    pronunciation = pronunciations_dict[pinyin].source if pinyin in pronunciations_dict else None
                    result1[pinyin] = {'pinyin': pinyin, 'source': pronunciation, "characters": []}
                word = None
                if pinyin in words_dict:
                    for item in words_dict[pinyin]:
                        if item.word == character:
                            word = item.id
                            break
                result1[pinyin]['characters'].append({'character': character, 'word': word, 'traditional': traditional})
            return JsonResponse({"result": list(result1.values())}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def searchEach(request):
    try:
        if request.method == 'GET':
            search = request.GET['search']
            result = Character.objects.filter(character__in=search)
            dic = {}
            for character in search:
                dic[character] = []
            for character in result:
                dic[character.character].append({"id": character.id, 'shengmu': character.shengmu, 'ipa': character.ipa,
                                                 'pinyin': character.pinyin, 'yunmu': character.yunmu,
                                                 'shengdiao': character.shengdiao, 'character': character.character,
                                                 'county': character.county, 'town': character.town,
                                                 'traditional': character.traditional})
            ans = []
            for character in dic.keys():
                ans.append({'label': character, 'characters': dic[character]})
            return JsonResponse({'characters': ans}, status=200)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=500)


@csrf_exempt
def searchEachV2(request):
    try:
        if request.method == 'GET':
            search = request.GET['search']
            result = Character.objects.filter(Q(character__in=search)
                                              | Q(traditional__in=search))
            dic = {}
            scores = {}
            for idx, character in enumerate(search):
                scores[character] = idx * 10
            for character in result:
                word = Word.objects.filter(standard_pinyin=character.pinyin).filter(word=character.character)
                word = word[0].id if word.exists() else None
                source = Pronunciation.objects.filter(pinyin=character.pinyin)
                source = source[0].source if source.exists() else None
                if character.character not in scores:
                    scores[character.character] = 1000
                if character.traditional not in scores:
                    scores[character.traditional] = 1000
                score = scores[character.character] + scores[character.traditional]
                if (score, character.character, character.traditional) not in dic:
                    dic[(score, character.character, character.traditional)] = []
                dic[(score, character.character, character.traditional)].append(
                    {"id": character.id, 'pinyin': character.pinyin, 'ipa': character.ipa,
                     'shengmu': character.shengmu, 'yunmu': character.yunmu, 'shengdiao': character.shengdiao,
                     'character': character.character, 'traditional': character.traditional,
                     'county': character.county, 'town': character.town,
                     'word': word, 'source': source})
            ans = []
            dict_list = sorted(dic.keys())
            for score, character, traditional in dict_list:
                new_dic = {}
                for item in dic[(score, character, traditional)]:
                    if (item['county'], item['town']) not in new_dic:
                        new_dic[(item['county'], item['town'])] = []
                    new_dic[(item['county'], item['town'])].append(item)
                result = []
                for (county, town), value in new_dic.items():
                    result.append({'county': county, 'town': town, 'characters': value})
                ans.append({'label': character, 'traditional': traditional, 'characters': result})
            return JsonResponse({'characters': ans}, status=200)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=500)


@csrf_exempt
def manageCharacter(request, id):
    try:
        character = Character.objects.filter(id=id)
        if character.exists():
            character = character[0]
            if request.method == 'GET':
                return JsonResponse(
                    {'character': {"id": character.id, 'shengmu': character.shengmu, 'ipa': character.ipa,
                                   'pinyin': character.pinyin, 'yunmu': character.yunmu,
                                   'shengdiao': character.shengdiao,
                                   'character': character.character, 'county': character.county,
                                   'town': character.town, 'traditional': character.traditional}}, status=200)
            elif request.method == 'PUT':
                body = demjson.decode(request.body)
                token = request.headers['token']
                if token_check(token, 'dxw', -1):
                    body = body['character']
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
            elif request.method == 'DELETE':
                token = request.headers['token']
                if token_check(token, 'dxw', -1):
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


@csrf_exempt
def searchPronunciations(request):
    try:
        if request.method == 'GET':
            if ('token' in request.headers) and token_check(request.headers['token'], 'dxw', -1):
                pronunciations = Pronunciation.objects.all()
            else:
                pronunciations = Pronunciation.objects.filter(visibility=True)
            if 'word' in request.GET:
                pronunciations = pronunciations.filter(word__id=request.GET['word'])
            if 'contributor' in request.GET:
                pronunciations = pronunciations.filter(contributor__id=request.GET['contributor'])
            pronunciations = list(pronunciations)
            pronunciations.sort(key=lambda item: item.id)
            total = len(pronunciations)
            if ('order' in request.GET) and request.GET['order'] == '1':
                pronunciations.reverse()
            if 'pageSize' in request.GET:
                pageSize = int(request.GET['pageSize'])
                page = int(request.GET['page'])
                r = min(len(pronunciations), page * pageSize)
                l = min(len(pronunciations) + 1, (page - 1) * pageSize)
                pronunciations = pronunciations[l:r]
            result = []
            for pronunciation in pronunciations:
                result.append({'pronunciation': {"id": pronunciation.id, 'word_id': pronunciation.word.id,
                                                 'word_word': pronunciation.word.word, 'source': pronunciation.source,
                                                 'ipa': pronunciation.ipa, 'pinyin': pronunciation.pinyin,
                                                 'contributor': pronunciation.contributor.id,
                                                 'county': pronunciation.county, 'town': pronunciation.town,
                                                 'visibility': pronunciation.visibility},
                               'contributor': simpleUserInfo(pronunciation.contributor)})
            return JsonResponse({"pronunciation": result, 'total': total}, status=200)
        elif request.method == 'POST':
            token = request.headers['token']
            user = token_check(token, 'dxw')
            if user:
                body = demjson.decode(request.body)
                body = body['pronunciation']
                pronunciation_form = PronunciationForm(body)
                if pronunciation_form.is_valid():
                    pronunciation = pronunciation_form.save(commit=False)
                    pronunciation.word = Word.objects.get(id=body['word'])
                    pronunciation.contributor = user
                    pronunciation.save()
                    return JsonResponse({'id': pronunciation.id}, status=200)
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
        if request.method == 'GET':
            ipa = str(ipa).strip()
            ans = [(len(p.ipa), p.contributor.username, p.source) for p in
                   Pronunciation.objects.filter(ipa=ipa).filter(visibility=True)]
            ans.sort(key=lambda x: x[0])
            if len(ans):
                ans = ans[0]
                return JsonResponse({'contributor': ans[1], 'url': ans[2], 'tts': 'null'}, status=200)
            else:
                return JsonResponse({'contributor': 'null', 'url': 'null', 'tts': 'null'}, status=200)
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
            if request.method == 'GET':
                pronunciation.views += 1
                pronunciation.save()
                user = pronunciation.contributor
                return JsonResponse(
                    {"pronunciation": {"id": pronunciation.id, 'word_id': pronunciation.word.id,
                                       'word_word': pronunciation.word.word, 'source': pronunciation.source,
                                       'ipa': pronunciation.ipa, 'pinyin': pronunciation.pinyin,
                                       'contributor': {"id": user.id, 'username': user.username,
                                                       'nickname': user.user_info.nickname,
                                                       'email': user.email, 'telephone': user.user_info.telephone,
                                                       'registration_time': user.date_joined.__format__(
                                                           '%Y-%m-%d %H:%M:%S'),
                                                       'login_time': user.last_login.__format__('%Y-%m-%d %H:%M:%S')
                                                       if user.last_login else '',
                                                       'birthday': user.user_info.birthday,
                                                       'avatar': user.user_info.avatar,
                                                       'county': user.user_info.county, 'town': user.user_info.town,
                                                       'is_admin': user.is_superuser}, 'county': pronunciation.county,
                                       'town': pronunciation.town, 'visibility': pronunciation.visibility}}, status=200)
            elif request.method == 'PUT':
                token = request.headers['token']
                if token_check(token, 'dxw', pronunciation.contributor.id):
                    body = demjson.decode(request.body)
                    body = body['pronunciation']
                    pronunciation_form = PronunciationForm(body)
                    for key in body:
                        if (key != 'word') and len(pronunciation_form[key].errors.data):
                            return JsonResponse({}, status=400)
                    for key in body:
                        if key != 'word':
                            setattr(pronunciation, key, body[key])
                        else:
                            pronunciation.word = Word.objects.get(id=body[key])
                    pronunciation.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
            elif request.method == 'DELETE':
                token = request.headers['token']
                user = token_check(token, 'dxw', pronunciation.contributor.id)
                if user:
                    if user != pronunciation.contributor:
                        body = demjson.decode(request.body)
                        message = body["message"] if "message" in body else "管理员操作"
                        content = f'您的语音(id = {pronunciation.id}) 已被删除，理由是：\n\t{message}'
                        sendNotification(None, [pronunciation.contributor], content, target=pronunciation,
                                         title='【通知】语音处理结果')
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


@require_POST
@csrf_exempt
def load_character(request):
    try:
        body = demjson.decode(request.body)
        token = request.headers['token']
        user = token_check(token, 'dxw', -1)
        if user:
            file = body['file']
            flush = body['flush']
            if flush:
                Character.objects.all().delete()
            sheet = xlrd.open_workbook(os.path.join('material', 'character', file)).sheet_by_index(0)
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
                        print('load character {}'.format(character.id))
                else:
                    raise Exception('add fail in {}'.format(dic))
            return JsonResponse({}, status=200)
        else:
            return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@require_POST
@csrf_exempt
def load_word(request):
    try:
        body = demjson.decode(request.body)
        file = body['file']
        sheet = open(os.path.join('material', 'word', file))
        lines = sheet.readlines()
        title = ['word', 'definition']
        col = 2
        for line in lines:
            info = line.split(',', 1)
            dic = {}
            for i in range(col):
                dic[title[i]] = info[i] if info[i] else '【待更新】'
            word_form = WordForm(dic)
            if word_form.is_valid():
                word = word_form.save(commit=False)
                word.contributor = User.objects.get(username='root')
                word.save()
                if word.id % 100 == 0:
                    print('load character {}'.format(word.id))
            else:
                raise Exception('add fail in {}'.format(dic))
        return JsonResponse({}, status=200)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def record(request):
    if request.method == 'GET':
        words = Word.objects.filter(
            Q(standard_ipa__isnull=False) &
            Q(standard_pinyin__isnull=False) &
            Q(visibility=True)
        )
        pageSize = int(request.GET['pageSize']) if 'pageSize' in request.GET else 15
        page = int(request.GET['page']) if 'page' in request.GET else 1
        r = min(len(words), page * pageSize)
        l = min(len(words) + 1, (page - 1) * pageSize)
        result = [{'word': word.id, 'ipa': word.standard_ipa, 'pinyin': word.standard_pinyin,
                   'count': word.pronunciation.count(), 'item': word.word, 'definition': word.definition}
                  for word in words[l:r]]

        return JsonResponse({
            'records': result,
            "total": {
                "item": len(words),
                "page": (len(words) - 1) // pageSize + 1
            }
        }, status=200)
    else:
        return JsonResponse({}, status=405)


@csrf_exempt
def upload_standard(request):
    '''
    通过excel上传word的standard_pinyin，standard_ipa，分为三列，为别为id,pinyin,ipa，有表头
    :return: 返回名为conflict的csv，展示与数据库冲突的word字段，为5列，id,init_ipa,init_pinyin,ipa,pinyin
    '''
    try:
        if request.method == 'POST':
            token = request.headers['token']
            user = token_check(token, 'dxw', -1)
            if user:
                file = request.FILES.get("file")

                sheet = xlrd.open_workbook(file_contents=file.read()).sheet_by_index(0)  # 错误
                line = sheet.nrows
                col = sheet.ncols
                ids = [int(x.value) for x in sheet.col(0)[1:]]
                words = sorted(list(Word.objects.filter(id__in=ids)), key=lambda w: w.id)

                # 将输入excel的词条按id从小到大排序
                infos = []
                for i in range(1, line):
                    info = sheet.row(i)
                    infos.append([int(info[0].value), info[1:]])
                infos.sort(key=lambda a: a[0])

                def conflict(x, y):
                    return x and y and x != y

                conflicts = []
                j = 0
                for i in range(line):
                    while j < len(words) and words[j].id < infos[i][0]:
                        j += 1
                    if j < len(words) and words[j].id == infos[i][0]:
                        if conflict(words[j].standard_ipa, infos[i][1][1].value) or \
                                conflict(words[j].standard_pinyin, infos[i][1][0].value):
                            conflicts.append(
                                [words[j].id, words[j].standard_ipa, words[j].standard_pinyin,
                                 infos[i][1][1].value, infos[i][1][0].value])
                        words[j].standard_ipa = infos[i][1][1].value
                        words[j].standard_pinyin = infos[i][1][0].value
                        words[j].save()
                        j += 1
                        if j % 100 == 0:
                            print(j)

                response = HttpResponse(content_type='text/csv', status=200, encoding='ANSI')
                response["Content-Disposition"] = "attachment; filename=conflict.csv"
                title = ['单词ID', '原IPA', '原拼音', '现IPA', '现拼音']
                file = csv.writer(response)
                file.writerow(title)
                file.writerows(conflicts)
                return response
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=500)


@csrf_exempt
def managePronunciationVisibility(request, id):
    '''
    管理员管理发音的visibility字段
    :param request:
    :return:
    '''
    try:
        if request.method == 'PUT':
            token = request.headers['token']
            user = token_check(token, 'dxw', -1)
            if user:
                pro = Pronunciation.objects.filter(id=id)
                if pro.exists():
                    pro = pro[0]
                    pro.visibility ^= True
                    if pro.visibility:
                        content = f"恭喜您的语音(id ={id}) 已通过审核"
                    else:
                        body = demjson.decode(request.body) if len(request.body) else {}
                        msg = body['message'] if 'message' in body else '管理员审核不通过'
                        content = f'您的语音(id = {id}) 审核状态变为不可见，理由是:\n\t{msg}'
                    sendNotification(None, [pro.contributor], content=content, target=pro, title='【通知】语音审核结果')
                    pro.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=404)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=500)


@csrf_exempt
def searchApplication(request):
    try:
        if request.method == 'GET':
            token = request.headers['token']
            user = token_check(token, 'dxw', -1)
            if user:
                applications = Application.objects.filter(granted=False)
                result = []
                for application in applications:
                    related_words = [word.id for word in application.related_words.all()]
                    related_articles = [article.id for article in application.related_articles.all()]
                    result.append({
                        'content': {
                            'word': application.content_word,
                            'definition': application.definition,
                            "annotation": application.annotation,
                            "standard_ipa": application.standard_ipa,
                            "standard_pinyin": application.standard_pinyin,
                            "mandarin": eval(application.mandarin) if application.mandarin else [],
                            "related_words": related_words, "related_articles": related_articles,
                        },
                        'word': application.word.id if application.word else 0,
                        'reason': application.reason,
                        'application': application.id,
                        'contributor': {
                            'nickname': application.contributor.user_info.nickname,
                            'avatar': application.contributor.user_info.avatar,
                            'id': application.contributor.id
                        },
                        "granted": application.granted,
                        "verifier": {
                            'nickname': application.verifier.user_info.nickname,
                            'avatar': application.verifier.user_info.avatar,
                            'id': application.verifier.id
                        } if application.verifier else None,
                    })
                return JsonResponse({'applications': result}, status=200)
            else:
                return JsonResponse({}, status=401)
        elif request.method == 'POST':
            token = request.headers['token']
            user = token_check(token, 'dxw', -1)
            if user:
                body = demjson.decode(request.body)
                if 'word' in body['content']:
                    body['content_word'] = body['content']['word']
                    body['content'].pop('word')
                body.update(body['content'])
                application_form = ApplicationForm(body)
                word = Word.objects.filter(id=body['word'])
                if word.exists() or ~body['word']:
                    if application_form.is_valid() and isinstance(body['mandarin'], list):
                        for id in body['related_articles']:
                            Article.objects.get(id=id)
                        for id in body['related_words']:
                            Word.objects.get(id=id)
                        application = application_form.save(commit=False)
                        application.contributor = user
                        if word.exists():
                            word = word[0]
                            application.word = word
                        application.save()
                        for id in body['related_articles']:
                            article = Article.objects.get(id=id)
                            application.related_articles.add(article)
                        for id in body['related_words']:
                            wordx = Word.objects.get(id=id)
                            application.related_words.add(wordx)
                        return JsonResponse({'id': application.id}, status=200)
                    else:
                        return JsonResponse({}, status=400)
                else:
                    return JsonResponse({}, status=404)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)

    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=500)


@csrf_exempt
def manageApplication(request, id):
    try:
        application = Application.objects.filter(id=id)
        if application.exists():
            application = application[0]
            if request.method == 'GET':
                token = request.headers['token']
                user = token_check(token, 'dxw', application.contributor.id)
                if user:
                    related_words = [word.id for word in application.related_words.all()]
                    related_articles = [article.id for article in application.related_articles.all()]
                    result = {
                        'content': {
                            'word': application.content_word,
                            'definition': application.definition,
                            "annotation": application.annotation,
                            "standard_ipa": application.standard_ipa,
                            "standard_pinyin": application.standard_pinyin,
                            "mandarin": eval(application.mandarin) if application.mandarin else [],
                            "related_words": related_words, "related_articles": related_articles,
                        },
                        'word': application.word.id if application.word else 0,
                        'reason': application.reason,
                        'application': application.id,
                        'contributor': {
                            'nickname': application.contributor.user_info.nickname,
                            'avatar': application.contributor.user_info.avatar,
                            'id': application.contributor.id
                        },
                        "granted": application.granted,
                        "verifier": {
                            'nickname': application.verifier.user_info.nickname,
                            'avatar': application.verifier.user_info.avatar,
                            'id': application.verifier.id
                        } if application.verifier else None,
                    }
                    return JsonResponse({'application': result}, status=200)
                else:
                    return JsonResponse({}, status=401)
            elif request.method == 'PUT':
                token = request.headers['token']
                user = token_check(token, 'dxw', -1)
                if user:
                    body = demjson.decode(request.body)
                    application.granted = True
                    application.verifier = user
                    if body['result']:
                        if application.word:
                            word = application.word
                            content = f'您对(id = {application.word.id}) 词语提出的修改建议(id = {application.id})已通过' \
                                      f'，感谢您为社区所做的贡献！'
                            title = '【通知】词条修改申请审核结果'
                        else:
                            word = Word.objects.create(contributor=application.contributor, visibility=True)
                            application.word = word
                            content = f'您的创建申请 (id = {application.id})已通过，' \
                                      f'已创建词条(id = {word.id})，感谢您为社区所做的贡献！'
                            title = '【通知】词条创建申请审核结果'
                        attributes = ['definition', 'annotation', 'standard_ipa', 'standard_pinyin',
                                      'mandarin']
                        for attribute in attributes:
                            value = getattr(application, attribute)
                            setattr(word, attribute, value)
                        word.word = application.content_word
                        word.related_articles.clear()
                        for related_article in application.related_articles.all():
                            word.related_articles.add(related_article)
                        word.related_words.clear()
                        for related_word in application.related_words.all():
                            word.related_words.add(related_word)
                        word.save()
                    else:
                        content = f'您对(id = {application.word.id}) 词语提出的修改建议(id = {application.id})' \
                                  f'未能通过审核，理由是:\n\t{body["reason"]}\n感谢您为社区所做的贡献！'
                        title = '【通知】词条修改申请审核结果'
                    sendNotification(None, [application.contributor], content, target=application, title=title)
                    application.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
            else:
                return JsonResponse({}, status=405)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=500)
