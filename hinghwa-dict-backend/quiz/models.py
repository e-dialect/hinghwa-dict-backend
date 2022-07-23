from django.db import models


class Quiz(models.Model):
    question = models.CharField(max_length=100, verbose_name="问题")
    options = models.TextField(verbose_name="选项", blank=True, default="[]")
    answer = models.IntegerField(default=0, verbose_name="答案序号", editable=False)
    explanation = models.TextField(verbose_name="答案解析")

    def __str__(self):
        return self.question

    def clean(self):
        self.question = self.question.strip()
        self.options = self.options.strip()
        self.answer = self.answer.strip()
        self.explanation = self.explanation.strip()
        return super(Quiz, self)

    def save(self, *args, **kwargs):
        self.clean()
        return super(Quiz, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "测试"
        verbose_name = "测试"
