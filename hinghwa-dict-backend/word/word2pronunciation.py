from django.db.models import Q

from .models import Word, Pronunciation


def word2pronunciation(word: Word, null=None):
    pronunciations = word.pronunciation.filter(
        Q(ipa__iexact=word.standard_ipa) & Q(visibility=True) & Q(source__isnull=False)
    )
    if pronunciations.exists():
        source = pronunciations[0].source
    else:
        pronunciations = Pronunciation.objects.filter(
            Q(ipa__iexact=word.standard_ipa)
            & Q(visibility=True)
            & Q(source__isnull=False)
        )
        if pronunciations.exists():
            source = pronunciations[0].source
        else:
            source = null
    return source
