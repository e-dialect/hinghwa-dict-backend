from django import forms

from .models import Word, Pronunciation, Character


class WordForm(forms.ModelForm):
    class Meta:
        model = Word
        fields = ('word', 'definition',
                  'annotation', 'mandarin', 'visibility')


class PronunciationForm(forms.ModelForm):
    class Meta:
        model = Pronunciation
        fields = ('source', 'ipa', 'pinyin',
                  'county', 'town')


class CharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = ('pinyin', 'ipa', 'character',
                  'shengmu', 'yunmu', 'shengdiao',
                  'county', 'town')
