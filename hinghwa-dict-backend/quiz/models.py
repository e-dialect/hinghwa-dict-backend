from django.db import models
from django.contrib.auth.models import User


class Quiz(models.Model):
    author = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="quizzes",
        verbose_name="作者",
        default=2,
    )
    question = models.CharField(max_length=100, verbose_name="问题")
    options = models.TextField(verbose_name="选项", blank=True, default="[]")
    answer = models.IntegerField(default=0, verbose_name="答案序号", editable=True)
    explanation = models.TextField(verbose_name="答案解析")
    visibility = models.BooleanField(default=False, verbose_name="是否审核")
    voice_source = models.URLField(max_length=200, verbose_name="播报语音链接", default="")

    def __str__(self):
        return self.question

    def clean(self):
        self.question = self.question.strip()
        if ~isinstance(self.options, str):
            self.options = str(self.options)
        self.options = self.options.strip()
        # self.answer = self.answer.strip()
        self.explanation = self.explanation.strip()
        return super(Quiz, self)

    def save(self, *args, **kwargs):
        self.clean()
        return super(Quiz, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "测试题"
        verbose_name = "测试题"
