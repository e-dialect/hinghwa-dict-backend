from django import forms
from .models import Quiz, QuizRecord


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ("question", "options", "answer", "explanation")


class QuizRecordForm(forms.ModelForm):
    class Meta:
        model = QuizRecord
        fields = ("answer", "correctness")
