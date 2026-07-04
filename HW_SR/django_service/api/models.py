from __future__ import annotations

from django.db import models


class WordWord(models.Model):
    id = models.AutoField(primary_key=True)
    word = models.CharField(max_length=60)
    definition = models.TextField()
    annotation = models.TextField()
    mandarin = models.TextField()
    standard_ipa = models.CharField(max_length=100)
    standard_pinyin = models.CharField(max_length=100)
    views = models.IntegerField()
    visibility = models.BooleanField()
    contributor_id = models.IntegerField()
    tags = models.TextField()

    class Meta:
        managed = False
        db_table = "word_word"
        app_label = "api"