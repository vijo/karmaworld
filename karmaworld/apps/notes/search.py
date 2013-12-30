#!/usr/bin/env python
# -*- coding:utf8 -*-
# Copyright (C) 2013  FinalsClub Foundation

import indextank.client as itc
import karmaworld.secret.indexden as secret

api_client = itc.ApiClient(secret.PRIVATE_URL)
index = api_client.get_index('karmanotes')


def note_to_dict(note):
    d = {
        'name': note.name,
    }

    if note.text:
        d['text'] = note.text

    if note.tags.exists():
        d['tags'] = [str(tag) for tag in note.tags.all()]

    if note.desc:
        d['desc'] = note.desc

    if note.course:
        d['course_id'] = note.course.id

    return d

def add_document(note):
    index.add_document(note.id, note_to_dict(note))

def remove_document(note):
    index.delete_document(note.id)

def search(query, course_id=None):
    """Returns note IDs matching the given query,
    filtered by course ID if given"""
    if course_id:
        results = index.search('(text:"%s" OR name:"%s") AND course_id:%s' % (query, query, course_id))
    else:
        results = index.search('text:"%s" OR name:"%s"' % (query, query))

    matching_note_ids = [r['docid'] for r in results['results']]

    return matching_note_ids