import os

import demjson
import xlrd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from article.models import Article
from website.views import evaluate
from website.views import token_check
from .forms import WordForm, CharacterForm, PronunciationForm
from .models import Word, Character, Pronunciation, User


@csrf_exempt
def searchWords(request):
    try:
        if request.method == 'GET':
            words = Word.objects.all()
            if 'contributor' in request.GET:
                words = words.filter(contributor=request.GET['contributor'])
            if 'search' in request.GET:
                result = []
                key = request.GET['search']
                for word in words:
                    score = evaluate(
                        [(word.word, 3), (word.definition, 2), (word.mandarin, 1.5), (word.annotation, 1)], key)
                    result.append((word.id, score))
                result.sort(key=lambda a: a[1], reverse=True)
                words = []
                for id, score in result:
                    if score > 0:
                        words.append(Word.objects.get(id=id))
                    else:
                        break

            end = min(20, len(words))
            words = [word.id for word in words[:end]]
            return JsonResponse({"words": words}, status=200)
        elif request.method == 'POST':
            body = demjson.decode(request.body)
            token = request.headers['token']
            user = token_check(token, '***REMOVED***')
            if user:
                body = body['word']
                word_form = WordForm(body)
                if word_form.is_valid() and isinstance(body['mandarin'], list):
                    word = word_form.save(commit=False)
                    word.contributor = user
                    for id in body['related_articles']:
                        Article.objects.get(id=id)
                    for id in body['related_words']:
                        Word.objects.get(id=id)
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
            for id in body['words']:
                word = Word.objects.get(id=id)
                words.append({'word': {"id": word.id, 'word': word.word, 'definition': word.definition,
                                       "contributor": word.contributor.id, "annotation": word.annotation,
                                       "mandarin": eval(word.mandarin), "views": word.views},
                              'contributor': {
                                  'id': word.contributor.id,
                                  'nickname': word.contributor.user_info.nickname,
                                  'avatar': word.contributor.user_info.avatar}})
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
                related_words = [word.id for word in word.related_words.all()]
                related_articles = [article.id for article in word.related_articles.all()]
                word.views = word.views + 1
                word.save()
                user = word.contributor
                return JsonResponse({"word": {"id": word.id, 'word': word.word, 'definition': word.definition,
                                              "contributor": {"id": user.id, 'username': user.username,
                                                              'nickname': user.user_info.nickname,
                                                              'email': user.email,
                                                              'telephone': user.user_info.telephone,
                                                              'registration_time': user.date_joined.__format__(
                                                                  '%Y-%m-%d %H:%M:%S'),
                                                              'login_time': user.last_login.__format__(
                                                                  '%Y-%m-%d %H:%M:%S'),
                                                              'birthday': user.user_info.birthday,
                                                              'avatar': user.user_info.avatar,
                                                              'county': user.user_info.county,
                                                              'town': user.user_info.town,
                                                              'is_admin': user.is_superuser},
                                              "annotation": word.annotation,
                                              "mandarin": eval(word.mandarin),
                                              "related_words": related_words, "related_articles": related_articles,
                                              "views": word.views}}, status=200)
            elif request.method == 'PUT':
                body = demjson.decode(request.body)
                token = request.headers['token']
                if token_check(token, '***REMOVED***', word.contributor.id):
                    body = body['word']
                    word_form = WordForm(body)
                    for key in body:
                        if (key in word_form) and len(word_form[key].errors.data):
                            return JsonResponse({}, status=400)
                    for key in body:
                        if key != 'related_words' and key != 'related_articles':
                            setattr(word, key, body[key])
                        elif key == 'related_words':
                            word.related_words.clear()
                            for id in body['related_words']:
                                wordx = Word.objects.get(id=id)
                                word.related_words.add(wordx)
                        elif key == 'related_articles':
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
                if token_check(token, '***REMOVED***', word.contributor.id):
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
            user = token_check(token, '***REMOVED***')
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
            characters = []
            for id in body['characters']:
                character = Character.objects.get(id=id)
                characters.append(
                    {"id": character.id, 'shengmu': character.shengmu, 'ipa': character.ipa,
                     'pinyin': character.pinyin, 'yunmu': character.yunmu, 'shengdiao': character.shengdiao,
                     'character': character.character, 'county': character.county, 'town': character.town})
            return JsonResponse({"characters": characters}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


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
                                   'town': character.town}}, status=200)
            elif request.method == 'PUT':
                body = demjson.decode(request.body)
                token = request.headers['token']
                if token_check(token, '***REMOVED***', -1):
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
                if token_check(token, '***REMOVED***', -1):
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
            # 有的话就返回，没有就生成一个返回
            ipa = request.GET['ipa']
            pronunciations = Pronunciation.objects.get(id=1)
            return JsonResponse({"contributor": pronunciations.contributor, "url": pronunciations.source}, status=200)
        elif request.method == 'POST':
            token = request.headers['token']
            user = token_check(token, '***REMOVED***')
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
        elif request.method == "PUT":
            pronunciations = []
            body = demjson.decode(request.body)
            for id in body['pronunciation']:
                pronunciation = Pronunciation.objects.get(id=id)
                pronunciations.append(
                    {'pronunciation': {"id": pronunciation.id, 'word': pronunciation.word.id,
                                       'source': pronunciation.source,
                                       'ipa': pronunciation.ipa, 'pinyin': pronunciation.pinyin,
                                       'contributor': pronunciation.contributor.id,
                                       'county': pronunciation.county, 'town': pronunciation.town,
                                       'visibility': pronunciation.visibility},
                     'contributor': {
                         'id': pronunciation.contributor.id, 'nickname': pronunciation.contributor.user_info.nickname,
                         'avatar': pronunciation.contributor.user_info.avatar}})
            return JsonResponse({"pronunciation": pronunciations}, status=200)
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
                    {"pronunciation": {"id": pronunciation.id, 'word': pronunciation.word.id,
                                       'source': pronunciation.source,
                                       'ipa': pronunciation.ipa, 'pinyin': pronunciation.pinyin,
                                       'contributor': {"id": user.id, 'username': user.username,
                                                       'nickname': user.user_info.nickname,
                                                       'email': user.email, 'telephone': user.user_info.telephone,
                                                       'registration_time': user.date_joined.__format__(
                                                           '%Y-%m-%d %H:%M:%S'),
                                                       'login_time': user.last_login.__format__('%Y-%m-%d %H:%M:%S'),
                                                       'birthday': user.user_info.birthday,
                                                       'avatar': user.user_info.avatar,
                                                       'county': user.user_info.county, 'town': user.user_info.town,
                                                       'is_admin': user.is_superuser}, 'county': pronunciation.county,
                                       'town': pronunciation.town, 'visibility': pronunciation.visibility}}, status=200)
            elif request.method == 'PUT':
                token = request.headers['token']
                if token_check(token, '***REMOVED***', pronunciation.contributor.id):
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
                if token_check(token, '***REMOVED***'):
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
        file = body['file']
        sheet = xlrd.open_workbook(os.path.join('material', 'character', file)).sheet_by_index(0)
        line = sheet.nrows
        col = sheet.ncols
        title = sheet.row(0)
        for line in range(1, line):
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
