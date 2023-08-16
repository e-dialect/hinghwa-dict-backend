import demjson
from ..models import List
from .dto.list_all import list_all
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from utils.exception.types.not_found import ListsNotFoundException
from utils.token import token_pass
from utils.generate_id import generate_list_id

