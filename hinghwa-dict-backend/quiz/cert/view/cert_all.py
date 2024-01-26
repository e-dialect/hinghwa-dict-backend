import demjson
from django.http import JsonResponse
from django.views import View
from ...models import Cert
from ..forms import CertForm
from user.models import User
from ..dto.cert import cert_info
from utils.exception.types.bad_request import BadRequestException
from utils.token import token_pass
from utils.generate_id import generate_cert_id
from utils.exception.types.not_found import UserNotFoundException
from user.utils import get_user_by_id
from django.utils import timezone


class AllCert(View):
    # QZ0502创建证书
    def post(self, request):
        token_pass(request.headers, -1)
        body = demjson.decode(request.body)
        cert_form = CertForm(body["cert"])
        if not cert_form.is_valid():
            raise BadRequestException()
        cert = cert_form.save(commit=False)
        if body["user"] != "":
            user = User.objects.filter(id=body["user"])
            if not user.exists():
                raise UserNotFoundException()
            user = user[0]
            cert.user = user
        cert.id = generate_cert_id()
        cert.time = timezone.now()
        cert.save()
        return JsonResponse(cert_info(cert), status=200)

    # QZ0501查询所有证书
    def get(self, request):
        token_pass(request.headers)
        result = []
        name = request.GET["name"]
        name_set = Cert.objects.filter(name=name)
        for name in name_set:
            result.append(cert_info(name))
        if request.GET["user"]:
            user_id = request.GET["user"]
            users = Cert.objects.filter(user=get_user_by_id(user_id))
            for user in users:
                result.append(cert_info(user))
        result = list(tuple(result))
        return JsonResponse(
            {
                "amount": len(result),
                "certs": result,
            },
            status=200,
        )
