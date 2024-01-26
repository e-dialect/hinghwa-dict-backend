from ...models import Cert
from user.dto.user_simple import user_simple


def cert_info(cert: Cert):
    response = {
        "level": cert.level,
        "name": cert.name,
        "place": cert.place,
        "sequence": cert.sequence,
        "grade": cert.grade,
        "scores": cert.scores,
        "time": cert.time,
        "ID": cert.id,
        "user": None if cert.user is None else user_simple(cert.user),
    }
    return response
