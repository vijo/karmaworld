#!/usr/bin/env python
# -*- coding:utf8 -*-
# Copyright (C) 2012  FinalsClub Foundation
""" Controller for the KarmaNotes website """

from django.contrib import admin
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView

from karmaworld.apps.courses.views import AboutView, flag_course, edit_course, course_list_ajax
from karmaworld.apps.courses.views import CourseDetailView
from karmaworld.apps.courses.views import CourseListView
from karmaworld.apps.courses.views import school_course_list
from karmaworld.apps.courses.views import school_course_instructor_list
from karmaworld.apps.notes.views import NoteView, thank_note, NoteSearchView, flag_note, downloaded_note, edit_note_tags, \
    NoteKeywordsView, NoteQuizView, NoteDeleteView
from karmaworld.apps.moderation import moderator
from karmaworld.apps.document_upload.views import save_fp_upload
from karmaworld.apps.quizzes.views import set_delete_keyword_annotator, get_keywords_annotator
from karmaworld.apps.users.views import ProfileView

# See: https://docs.djangoproject.com/en/dev/ref/contrib/admin/#hooking-adminsite-instances-into-your-urlconf
admin.autodiscover()

# reused named regex capture groups
SLUG = r'(?P<{0}slug>[-A-Za-z0-9_]+)'
"""
# ex: SLUG.format('')  :> (?P<slug>[-A-Za-z0-9_]+)
# ex: SLUG.format('school_')  :> (?P<school_slug>[-A-Za-z0-9_]+)

  ex: course url
  url(r'^' + SLUG.format('school_') + '/' + SLUG.format('') + '/'
        CourseDetailView.as_view(), name='course_detail'),

  (?P<school_slug>[^/]+)/(?P<course_slug>[^/]+)/(?P<pk>[\d^/]+)$', \
        NoteView.as_view(), name='note_detail_pk'),
"""

urlpatterns = patterns('',
    ## Administrative URLpatterns
    # Admin panel and documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    # Grappelli django-admin improvment suite
    url(r'^grappelli/', include('grappelli.urls')),
    # Moderator panel and documentation:
    url(r'^moderator/doc/', include('django.contrib.admindocs.urls')),
    url(r'^moderator/', include(moderator.site.urls)),

    # support AJAX lookup endpoints
    url(r'^lookups/', include('ajax_select.urls')),

    ## Single-serving page URLpatterns
    url(r'^terms/$', TemplateView.as_view(template_name='terms.html'), name='terms'),
    url(r'^about/$', AboutView.as_view(), name='about'),

    # All Auth
    url(r'^accounts/', include('allauth.urls')),
    url(r'^accounts/profile/', ProfileView.as_view(), name='accounts_profile'),

    # Media handling
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', 
            {'document_root': settings.MEDIA_ROOT, }),

    # Filepicker upload
    url(r'^api/upload$', save_fp_upload, name='upload_post'),

    # ---- JSON views ----#
    # return json list of courses for a given school
    url(r'^school/course/list/$', school_course_list, name='json_school_course_list'),
    # return json list of instructors for a given school and course
    url(r'^school/course/instructors/list/$', school_course_instructor_list, name='json_school_course_instructor_list'),
    # ---- end JSON views ----#

    url(r'^search/$', NoteSearchView.as_view(), name='note_search'),

    ## Course Model
    # VIEW for displaying a single Course
    url(r'^course/' + SLUG.format('') + '/$',
        CourseDetailView.as_view(), name='course_detail'),

    ## Note Model
    url(r'^ajax/courses/$', course_list_ajax, name='course_list_ajax'),
    # Ajax endpoint to thank a note
    url(r'^ajax/note/thank/(?P<pk>[\d]+)/$', thank_note, name='thank_note'),
    # Ajax endpoint to flag a note
    url(r'^ajax/note/flag/(?P<pk>[\d]+)/$', flag_note, name='flag_note'),
    # Ajax endpoint to update a notes tags
    url(r'^ajax/note/tags/(?P<pk>[\d]+)/$', edit_note_tags, name='edit_note_tags'),
    # Ajax endpoint to record that somebody downloaded a note
    url(r'^ajax/note/downloaded/(?P<pk>[\d]+)/$', downloaded_note, name='downloaded_note'),
    # Ajax endpoint to flag a course
    url(r'^ajax/course/flag/(?P<pk>[\d]+)/$', flag_course, name='flag_course'),
    # Ajax endpoint to edit a course
    url(r'^ajax/course/edit/(?P<pk>[\d]+)/$', edit_course, name='edit_course'),

    url(r'^ajax/annotations/annotations$', set_delete_keyword_annotator, name='set_keyword'),
    url(r'^ajax/annotations/search/$', get_keywords_annotator, name='get_keywords'),


    # Valid url cases to the Note page
    # a: school/course/id
    # b: school/course/id/slug
    # c: s../c../slug
    # note file as id, for notes without titles yet
    url(r'^note/(?P<school_slug>[^/]+)/(?P<course_slug>[^/]+)/(?P<pk>[\d^/]+)$', \
        NoteView.as_view(), name='note_detail_pk'),
    # note file by note.slug
    url(r'^note/' + SLUG.format('school_') + '/' + SLUG.format('course_') +'/'+ SLUG.format('') +'$',
        NoteView.as_view(), name='note_detail'),
    url(r'^note/' + SLUG.format('school_') + '/' + SLUG.format('course_') +'/'+ SLUG.format('') +'/keywords/$',
        NoteKeywordsView.as_view(), name='note_keywords'),
    url(r'^note/' + SLUG.format('school_') + '/' + SLUG.format('course_') +'/'+ SLUG.format('') +'/quiz/$',
        NoteQuizView.as_view(), name='note_quiz'),

    url(r'note/delete/$', NoteDeleteView.as_view(), name='note_delete'),

    url(r'^$', CourseListView.as_view(), name='home'),
)


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

