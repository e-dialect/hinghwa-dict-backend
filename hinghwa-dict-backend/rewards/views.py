import datetime
import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from .dto.rewards_all import rewards_all
from .dto.title_all import title_all
from utils.exception.types.not_found import (
    RewardsNotFoundException,
    TitleNotFoundException,
)
from utils.token import generate_token
from utils.Upload import uploadAvatar
from django.conf import settings
from .models import Rewards, Title
from .forms import RewardsInfoForm, TitleInfoForm
from django.views import View
from utils.exception.types.bad_request import BadRequestException
from utils.token import token_user, token_pass
from website.views import token_check


class ManageRewards(View):
    # RE0101 上传新商品
    @csrf_exempt
    def post(self, request) -> JsonResponse:
        try:
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY, -1)
            if user:
                body = demjson.decode(request.body)
                reward_form = RewardsInfoForm(body)
                if not reward_form.is_valid():
                    raise BadRequestException()
                reward = reward_form.save()
                reward.save()
                return JsonResponse({"id": reward.id}, status=200)
            else:
                return JsonResponse({}, status=403)
        except Exception as e:
            return JsonResponse({"msg": str(e)}, status=500)

    # RE0102 删除商品
    @csrf_exempt
    def delete(self, request, id) -> JsonResponse:
        try:
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY, -1)
            if user:
                reward = Rewards.objects.filter(id=id)
                if not reward.exists():
                    raise RewardsNotFoundException()
                reward = reward[0]
                reward.delete()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=403)
        except Exception as e:
            return JsonResponse({"msg": str(e)}, status=500)

    # RE0103 更新商品信息
    @csrf_exempt
    def put(self, request, id) -> JsonResponse:
        token = request.headers["token"]
        user = token_check(token, settings.JWT_KEY, -1)
        if user:
            reward = Rewards.objects.filter(id=id)
            if not reward.exists():
                raise RewardsNotFoundException()
            reward = reward[0]
            body = demjson.decode(request.body)
            for key in body:
                setattr(reward, key, body[key])
            reward.save()
            return JsonResponse({"rewards": rewards_all(reward)}, status=200)
        else:
            return JsonResponse({}, status=403)


class SearchRewards(View):
    # RE0104获取单个商品信息
    @csrf_exempt
    def get(self, request, id):
        reward = Rewards.objects.filter(id=id)
        if not reward.exists():
            raise RewardsNotFoundException()
        reward = reward[0]
        return JsonResponse({"rewards": rewards_all(reward)}, status=200)

    # RE0201获取全部商品信息
    @csrf_exempt
    def post(self, request):
        result_rewards = Rewards.objects.all()
        result_titles = Title.objects.all()
        rewards = []
        titles = []
        for reward in result_rewards:
            rewards.append(rewards_all(reward))
        for title in result_titles:
            titles.append(title_all(title))

        return JsonResponse({"rewards": rewards, "titles": titles}, status=200)


class ManageTitle(View):
    # RE0105上传新头衔
    @csrf_exempt
    def post(self, request) -> JsonResponse:
        try:
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY, -1)
            if user:
                body = demjson.decode(request.body)
                title_form = TitleInfoForm(body)
                if not title_form.is_valid():
                    raise BadRequestException()
                title = title_form.save()
                title.save()
                return JsonResponse({"id": title.id}, status=200)
            else:
                return JsonResponse({}, status=403)
        except Exception as e:
            return JsonResponse({"msg": str(e)}, status=500)

    # RE0106删除头衔
    @csrf_exempt
    def delete(self, request, id) -> JsonResponse:
        try:
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY, -1)
            if user:
                title = Title.objects.filter(id=id)
                if not title.exists():
                    raise TitleNotFoundException()
                title = title[0]
                title.delete()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=403)
        except Exception as e:
            return JsonResponse({"msg": str(e)}, status=500)

    # RE0107更新头衔信息
    @csrf_exempt
    def put(self, request, id) -> JsonResponse:
        token = request.headers["token"]
        user = token_check(token, settings.JWT_KEY, -1)
        if user:
            title = Title.objects.filter(id=id)
            if not title.exists():
                raise TitleNotFoundException()
            title = title[0]
            body = demjson.decode(request.body)
            for key in body:
                setattr(title, key, body[key])
            title.save()
            return JsonResponse({"title": title_all(title)}, status=200)
        else:
            return JsonResponse({}, status=403)


class SearchTitle(View):
    # RE0108获取单个头衔信息
    @csrf_exempt
    def get(self, request, id):
        title = Title.objects.filter(id=id)
        if not title.exists():
            raise TitleNotFoundException()
        title = title[0]
        return JsonResponse({"title": title_all(title)}, status=200)
