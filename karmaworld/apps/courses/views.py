#!/usr/bin/env python
# -*- coding:utf8 -*-
# Copyright (C) 2012  FinalsClub Foundation
""" Views for the KarmaNotes Courses app """

import json

from django.db.models import Sum
from django.core import serializers
from django.core.exceptions import MultipleObjectsReturned
from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.views.generic import DetailView
from django.views.generic import TemplateView
from django.views.generic.edit import ProcessFormView
from django.views.generic.edit import ModelFormMixin
from django.views.generic.list import ListView

from karmaworld.apps.courses.forms import CourseForm
from karmaworld.apps.courses.models import Course
from karmaworld.apps.courses.models import School
from karmaworld.apps.notes.models import Note
from karmaworld.apps.users.models import CourseKarmaEvent
from karmaworld.apps.notes.forms import FileUploadForm
from karmaworld.utils import ajax_increment, format_session_increment_field

FLAG_FIELD = 'flags'
USER_PROFILE_FLAGS_FIELD = 'flagged_courses'


class CourseListView(ListView, ModelFormMixin, ProcessFormView):
    """ Simple ListView for the front page that includes the CourseForm """
    model = Course
    form_class = CourseForm
    object = None

    def get_context_data(self, **kwargs):
        """ Add the CourseForm to ListView context """
        # get the original context
        context = super(CourseListView, self).get_context_data(**kwargs)
        # get the total number of notes
        context['note_count'] = Note.objects.count()
        # get the course form for the form at the bottom of the homepage
        context['course_form'] = kwargs.get('course_form', CourseForm())
        if context['course_form'].errors:
            # if there was an error in the form
            context['jump_to_form'] = True

        # Include "Add Course" button in header
        context['display_add_course'] = True

        # Include courses to number of total note thanks mapping
        # See Course.get_popularity for a more detailed explanation.
        thanks = Course.objects.values('id').annotate(sum=Sum('note__thanks'))
        # Create a generator to convert the list of dicts into a dict.
        context['course_thanks'] = dict((x['id'],x['sum'] or 0) for x in thanks)

        return context

    def get_success_url(self):
        """ On success, return url based on urls.py definition. """
        return self.object.get_absolute_url()

    def form_invalid(self, form, **kwargs):
        """ override form_invalid to populate object_list on redirect """
        kwargs['is_error'] = True
        kwargs['course_form'] = form
        self.object_list = self.get_queryset()
        kwargs['object_list'] = self.object_list
        return self.render_to_response(self.get_context_data(**kwargs))


class CourseDetailView(DetailView):
    """ Class-based view for the course html page """
    model = Course
    context_object_name = u"course" # name passed to template

    def get_context_data(self, **kwargs):
        """ filter the Course.note_set to return no Drafts """
        kwargs = super(CourseDetailView, self).get_context_data()
        kwargs['note_set'] = self.object.note_set.filter(is_hidden=False)

        # Include "Add Note" button in header
        kwargs['display_add_note'] = True

        # For the Filepicker Partial template
        kwargs['file_upload_form'] = FileUploadForm()

        if self.request.user.is_authenticated():
            try:
                self.request.user.get_profile().flagged_courses.get(pk=self.object.pk)
                kwargs['already_flagged'] = True
            except ObjectDoesNotExist:
                pass

        return kwargs

class AboutView(TemplateView):
    """ Display the About page with the Schools leaderboard """
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        """ get the list of schools with the most files for leaderboard """
        if 'schools' not in kwargs:
            kwargs['schools'] = School.objects.filter(file_count__gt=0).order_by('-file_count')[:20]
        return kwargs


def school_list(request):
    """ Return JSON describing Schools that match q query on name """
    if not (request.method == 'POST' and request.is_ajax()
                        and request.POST.has_key('q')):
        #return that the api call failed
        return HttpResponseBadRequest(json.dumps({'status':'fail'}), mimetype="application/json")

    # if an ajax get request with a 'q' name query
    # get the schools as a id name dict,
    _query = request.POST['q']
    matching_school_aliases = list(School.objects.filter(alias__icontains=_query))
    matching_school_names = sorted(list(School.objects.filter(name__icontains=_query)[:20]),key=lambda o:len(o.name))
    _schools = matching_school_aliases[:2] + matching_school_names
    schools = [{'id': s.id, 'name': s.name} for s in _schools]

    # return as json
    return HttpResponse(json.dumps({'status':'success', 'schools': schools}), mimetype="application/json")


def school_course_list(request):
    """Return JSON describing courses we know of at the given school
     that match the query """
    if not (request.method == 'POST' and request.is_ajax()
                        and request.POST.has_key('q')
                        and request.POST.has_key('school_id')):
        # return that the api call failed
        return HttpResponseBadRequest(json.dumps({'status': 'fail', 'message': 'query parameters missing'}),
                                    mimetype="application/json")

    _query = request.POST['q']
    try:
      _school_id = int(request.POST['school_id'])
    except:
      return HttpResponseBadRequest(json.dumps({'status': 'fail',
                                              'message': 'could not convert school id to integer'}),
                                  mimetype="application/json")

    # Look up the school
    try:
        school = School.objects.get(id__exact=_school_id)
    except (MultipleObjectsReturned, ObjectDoesNotExist):
        return HttpResponseBadRequest(json.dumps({'status': 'fail',
                                                'message': 'school id did not match exactly one school'}),
                                    mimetype="application/json")

    # Look up matching courses
    _courses = Course.objects.filter(school__exact=school.id, name__icontains=_query)
    courses = [{'name': c.name} for c in _courses]

    # return as json
    return HttpResponse(json.dumps({'status':'success', 'courses': courses}),
                        mimetype="application/json")


def school_course_instructor_list(request):
    """Return JSON describing instructors we know of at the given school
       teaching the given course
       that match the query """
    if not(request.method == 'POST' and request.is_ajax()
                        and request.POST.has_key('q')
                        and request.POST.has_key('course_name')
                        and request.POST.has_key('school_id')):
        # return that the api call failed
        return HttpResponseBadRequest(json.dumps({'status': 'fail', 'message': 'query parameters missing'}),
                                    mimetype="application/json")

    _query = request.POST['q']
    _course_name = request.POST['course_name']
    try:
      _school_id = int(request.POST['school_id'])
    except:
      return HttpResponseBadRequest(json.dumps({'status': 'fail',
                                              'message':'could not convert school id to integer'}),
                                  mimetype="application/json")

    # Look up the school
    try:
        school = School.objects.get(id__exact=_school_id)
    except (MultipleObjectsReturned, ObjectDoesNotExist):
        return HttpResponseBadRequest(json.dumps({'status': 'fail',
                                                  'message': 'school id did not match exactly one school'}),
                                    mimetype="application/json")

    # Look up matching courses
    _courses = Course.objects.filter(school__exact=school.id,
                                     name__exact=_course_name,
                                     instructor_name__icontains=_query)
    instructors = [{'name': c.instructor_name, 'url': c.get_absolute_url()} for c in _courses]

    # return as json
    return HttpResponse(json.dumps({'status':'success', 'instructors': instructors}),
                        mimetype="application/json")


def process_course_flag_events(request_user, course):
    # Take a point away from person flagging this course
    if request_user.is_authenticated():
        CourseKarmaEvent.create_event(request_user, course, CourseKarmaEvent.GIVE_FLAG)


def flag_course(request, pk):
    """Record that somebody has flagged a note."""
    return ajax_increment(Course, request, pk, FLAG_FIELD, USER_PROFILE_FLAGS_FIELD, process_course_flag_events)

def edit_course(request, pk):
    """
    Saves the edited course content
    """
    if request.method == "POST" and request.is_ajax():
        course = Course.objects.get(pk=pk)
        original_name = course.name
        course_form = CourseForm(request.POST or None, instance=course)

        if course_form.is_valid():
            course_form.save()

            course_json = serializers.serialize('json', [course,])
            resp = json.loads(course_json)[0]

            if (course.name != original_name):
                course.set_slug()
                resp['fields']['new_url'] = course.get_absolute_url()

            return HttpResponse(json.dumps(resp), mimetype="application/json")
        else:
            return HttpResponseBadRequest(json.dumps({'status': 'fail', 'message': 'Validation error',
                                          'errors': course_form.errors}),
                                          mimetype="application/json")
    else:
        return HttpResponseBadRequest(json.dumps({'status': 'fail', 'message': 'Invalid request'}),
                                      mimetype="application/json")
