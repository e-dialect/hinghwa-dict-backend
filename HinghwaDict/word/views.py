import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from article.models import Article
from website.views import token_check
from .forms import WordForm, CharacterForm, PronunciationForm
from .models import Word, Character, Pronunciation


@csrf_exempt
def searchWords(request):
    body = demjson.decode(request.body)
    try:
        if request.method == 'GET':
            all = Word.objects.all()
            words = [word.id for word in all]
            return JsonResponse({"words": words}, status=200)
        elif request.method == 'POST':
            token = request.headers['token']
            user = token_check(token, 'dxw')
            if user:
                body = body['word']
                word_form = WordForm(body)
                if word_form.is_valid():
                    word = word_form.save(commit=False)
                    word.contributor = user
                    for id in body['related_articles']:
                        article = Article.objects.get(id=id)
                        word.related_articles.add(article)
                    for id in body['related_words']:
                        wordx = Word.objects.get(id=id)
                        word.related_words.add(wordx)
                    word.save()
                    return JsonResponse({'id': word.id}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        elif request.method == "PUT":
            words = []
            for id in body['words']:
                word = Word.objects.get(id=id)
                words.append({"id": word.id, 'word': word.word, 'definition': word.definition,
                              "contributor": word.contributor.id, "annotation": word.annotation,
                              "mandarin": word.mandarin, "views": word.views})
            return JsonResponse({"words": words}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def manageWord(request, id):
    try:
        word = Word.objects.get(id=id)
        body = demjson.decode(request.body)
        if request.method == 'GET':
            related_words = [word.id for word in word.related_words.all()]
            related_articles = [article.id for article in word.related_articles.all()]
            word.views = word.views + 1
            word.save()
            user = word.contributor
            return JsonResponse({"word": {"id": word.id, 'word': word.word, 'definition': word.definition,
                                          "contributor": {"id": user.id, 'username': user.username,
                                                          'nickname': user.user_info.nickname,
                                                          'email': user.email, 'telephone': user.user_info.telephone,
                                                          'registration_time': user.date_joined,
                                                          'login_time': user.last_login,
                                                          'birthday': user.user_info.birthday,
                                                          'avatar': user.user_info.avatar,
                                                          'county': user.user_info.county, 'town': user.user_info.town,
                                                          'is_admin': user.is_superuser}, "annotation": word.annotation,
                                          "mandarin": word.mandarin,
                                          "related_words": related_words, "related_articles": related_articles,
                                          "views": word.views}}, status=200)
        elif request.method == 'PUT':
            token = request.headers['token']
            if token_check(token, 'dxw', word.contributor.id):
                body = body['word']
                word_form = WordForm(body)
                for key in body:
                    if len(word_form[key].errors.data):
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
                            word.related_words.add(article)
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
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def searchCharacters(request):
    body = demjson.decode(request.body)
    try:
        if request.method == 'GET':
            all = Character.objects.all()
            characters = [character.id for character in all]
            return JsonResponse({"characters": characters}, status=200)
        elif request.method == 'POST':
            token = request.headers['token']
            user = token_check(token, 'dxw')
            if user:
                body = body['character']
                character_form = WordForm(body)
                if character_form.is_valid():
                    character = character_form.save(commit=False)
                    character.save()
                    return JsonResponse({'id': character.id}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        elif request.method == "PUT":
            characters = []
            for id in body['characters']:
                character = Character.objects.get(id=id)
                characters.append(
                    {"id": character.id, 'shengmu': character.shengmu, 'ipa': character.ipa,
                     'pinyin': character.pinyin, 'yunmu': character.yunmu, 'shengdiao': character.shengdiao,
                     'character': character.character, 'county': character.county, 'town': character.county})
            return JsonResponse({"characters": characters}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def manageCharacter(request, id):
    try:
        body = demjson.decode(request.body)
        character = Character.objects.get(id=id)
        if request.method == 'GET':
            return JsonResponse({'character': {"id": character.id, 'shengmu': character.shengmu, 'ipa': character.ipa,
                                               'pinyin': character.pinyin, 'yunmu': character.yunmu,
                                               'shengdiao': character.shengdiao,
                                               'character': character.character, 'county': character.county,
                                               'town': character.county}}, status=200)
        elif request.method == 'PUT':
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
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def searchPronunciations(request):
    body = demjson.decode(request.body)
    try:
        if request.method == 'GET':
            # 有的话就返回，没有就生成一个返回
            pronunciations = Pronunciation.objects.get(id=1)
            return JsonResponse({"contributor": pronunciations.contributor, "url": pronunciations.source}, status=200)
        elif request.method == 'POST':
            token = request.headers['token']
            user = token_check(token, 'dxw')
            if user:
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
            for id in body['pronunciations']:
                pronunciation = Pronunciation.objects.get(id=id)
                pronunciations.append(
                    {"id": pronunciation.id, 'word': pronunciation.word, 'source': pronunciation.source,
                     'ipa': pronunciation.ipa, 'pinyin': pronunciation.pinyin,
                     'contributor': pronunciation.contributor.id,
                     'county': pronunciation.county, 'town': pronunciation.county,
                     'visibility': pronunciation.visibility})
            return JsonResponse({"pronunciations": pronunciations}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def managePronunciation(request, id):
    try:
        body = demjson.decode(request.body)
        pronunciation = Pronunciation.objects.get(id=id)
        if request.method == 'GET':
            pronunciation.views += 1
            pronunciation.save()
            user = pronunciation.contributor
            return JsonResponse(
                {"pronunciation": {"id": pronunciation.id, 'word': pronunciation.word, 'source': pronunciation.source,
                                   'ipa': pronunciation.ipa, 'pinyin': pronunciation.pinyin,
                                   'contributor': {"id": user.id, 'username': user.username,
                                                   'nickname': user.user_infoinfo.nickname,
                                                   'email': user.email, 'telephone': user.user_info.telephone,
                                                   'registration_time': user.date_joined, 'login_time': user.last_login,
                                                   'birthday': user.user_info.birthday, 'avatar': user.user_info.avatar,
                                                   'county': user.user_info.county, 'town': user.user_info.town,
                                                   'is_admin': user.is_superuser}, 'county': pronunciation.county,
                                   'town': pronunciation.county, 'visibility': pronunciation.visibility}}, status=200)
        elif request.method == 'PUT':
            token = request.headers['token']
            if token_check(token, 'dxw', pronunciation.contributor.id):
                body = body['pronunciation']
                pronunciation_form = PronunciationForm(body)
                for key in body:
                    if len(pronunciation_form[key].errors.data):
                        return JsonResponse({}, status=400)
                for key in body:
                    setattr(pronunciation, key, body[key])
                pronunciation.save()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
        elif request.method == 'DELETE':
            token = request.headers['token']
            if token_check(token, 'dxw'):
                pronunciation.delete()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)
