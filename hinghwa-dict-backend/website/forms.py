#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author:dxw time:2021/12/11
from django import forms

from .models import DailyExpression


class DailyExpressionForm(forms.ModelForm):
    class Meta:
        model = DailyExpression
        fields = ("english", "mandarin", "character", "pinyin")
