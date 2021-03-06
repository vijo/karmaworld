#!/usr/bin/env python
# -*- coding:utf8 -*-
# Copyright (C) 2014  FinalsClub Foundation
from django.forms import TextInput, Textarea, HiddenInput, Form, CharField, IntegerField


class KeywordForm(Form):
    keyword = CharField(widget=TextInput(attrs={'placeholder': 'Keyword', 'class': 'keyword'}),
                        required=False)
    definition = CharField(widget=Textarea(attrs={'placeholder': 'Definition', 'class': 'definition'}),
                           required=False)
    id = IntegerField(widget=HiddenInput(attrs={'class': 'object-id'}), required=False)

