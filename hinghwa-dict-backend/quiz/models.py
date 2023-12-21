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
    id = models.CharField(max_length=20, verbose_name="ID", primary_key=True)


class PaperRecord(models.Model):
    contributor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="paper_user", verbose_name="答卷人"
    )
    timestamp = models.DateTimeField(verbose_name="时间")
    paper = models.ForeignKey(
        Paper,
        on_delete=models.CASCADE,
        related_name="papers",
        verbose_name="试卷",
    )
    id = models.CharField(max_length=20, verbose_name="ID", primary_key=True)


class QuizRecord(models.Model):
    contributor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="QuizRecordUser",
        verbose_name="答题人",
    )
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="quiz", verbose_name="测试题"
    )
    paper = models.ForeignKey(
        PaperRecord,
        on_delete=models.CASCADE,
        related_name="quiz_paper",
        verbose_name="所在试卷",
        null=True,
    )
    answer = models.CharField(max_length=1000, verbose_name="答案")
    correctness = models.BooleanField(verbose_name="是否正确")
    timestamp = models.DateTimeField(verbose_name="时间")
    id = models.CharField(max_length=20, verbose_name="ID", primary_key=True)
