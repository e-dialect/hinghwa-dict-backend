from django import forms

from .models import Word, Pronunciation, Character, Application, List


class WordForm(forms.ModelForm):
    class Meta:
        model = Word
        fields = (
            "word",
            "definition",
            "annotation",
            "mandarin",
            "visibility",
            "standard_ipa",
            "standard_pinyin",
        )


class PronunciationForm(forms.ModelForm):
    class Meta:
        model = Pronunciation
        fields = ("source", "ipa", "pinyin", "county", "town")


class CharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = (
            "pinyin",
            "ipa",
            "character",
            "shengmu",
            "yunmu",
            "shengdiao",
            "county",
            "town",
            "traditional",
            "type",
        )


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = (
            "reason",
            "content_word",
            "definition",
            "annotation",
            "mandarin",
            "standard_ipa",
            "standard_pinyin",
        )


class ListForm(forms.ModelForm):
    class Meta:
        model = List
        fields = ("name", "description")
