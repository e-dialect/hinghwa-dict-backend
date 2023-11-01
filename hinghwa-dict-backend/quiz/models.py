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
    type = models.CharField(blank=True, max_length=50, verbose_name="问题类型")

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


class Paper(models.Model):
    title = models.CharField(blank=True, max_length=50, verbose_name="试卷标题")
    quizzes = models.ManyToManyField(
        Quiz, related_name="exam_questions", verbose_name="问题列表", blank=True
    )
    quantity = models.IntegerField(blank=True, verbose_name="题目数量")
    id = models.CharField(max_length=20, verbose_name="ID", primary_key=True)


class Record(models.Model):
    timestamp = models.DateTimeField(blank=True, verbose_name="时间")
    correct_answer = models.CharField(max_length=150, blank=True, verbose_name="答对数量")
    answer_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="answer_user", verbose_name="答题人"
    )
    exam = models.ManyToManyField(
        Paper, related_name="exam_record", verbose_name="对应试卷"
    )
    id = models.CharField(max_length=20, verbose_name="ID", primary_key=True)


class QuizHistory(models.Model):
    id = models.CharField(max_length=20, verbose_name="ID", primary_key=True)
    total = models.IntegerField(blank=True, verbose_name="总答题数")
    paper = models.ManyToManyField(
        Paper, related_name="relate_paper", verbose_name="对应试卷"
    )
