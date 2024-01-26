from django.http import JsonResponse
from django.views import View
from ...models import Cert
from utils.token import token_pass
from utils.exception.types.not_found import CertNotFoundException
from ..dto.cert import cert_info


class SingleCert(View):
    # QZ0503查询证书信息
    def get(self, request, id):
        token_pass(request.headers)
        cert = Cert.objects.filter(id=id)
        if not cert.exists():
            raise CertNotFoundException()
        cert = cert[0]
        return JsonResponse({"cert": cert_info(cert)}, status=200)
