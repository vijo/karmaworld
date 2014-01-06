#!/usr/bin/env python
# -*- coding:utf8 -*-
# Copyright (C) 2012  FinalsClub Foundation

"""
    Models for the courses django app.
    Handles courses, and their related models
    Courses are the first class object, they contain notes.
    Courses have a manytoone relation to schools.
"""
import datetime

from django.db import models
from django.template import defaultfilters
from karmaworld.settings.manual_unique_together import auto_add_check_unique_together


class School(models.Model):
    """ A grouping that contains many courses """
    name        = models.CharField(max_length=255)
    slug        = models.SlugField(max_length=150, null=True)
    location    = models.CharField(max_length=255, blank=True, null=True)
    url         = models.URLField(max_length=511, blank=True)
    # Facebook keeps a unique identifier for all schools
    facebook_id = models.BigIntegerField(blank=True, null=True)
    # United States Department of Education institution_id
    usde_id     = models.BigIntegerField(blank=True, null=True)
    file_count  = models.IntegerField(default=0)
    priority    = models.BooleanField(default=0)
    alias       = models.CharField(max_length=255, null=True, blank=True)
    hashtag     = models.CharField(max_length=16, null=True, blank=True, unique=True, help_text='School abbreviation without #')

    class Meta:
        """ Sort School by file_count descending, name abc=> """
        ordering = ['-file_count','-priority', 'name']


    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ Save school and generate a slug if one doesn't exist """
        if not self.slug:
            self.slug = defaultfilters.slugify(self.name)
        super(School, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return ("name__icontains",)

    def update_note_count(self):
        """ Update the School.file_count by summing the
            contained course.file_count
        """
        self.file_count = sum([course.file_count for course in self.course_set.all()])
        self.save()


class Department(models.Model):
    """ Department within a School. """
    name        = models.CharField(max_length=255)
    school      = models.ForeignKey(School) # Should this be optional ever?
    slug        = models.SlugField(max_length=150, null=True)
    url         = models.URLField(max_length=511, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ Save department and generate a slug if one doesn't exist """
        if not self.slug:
            self.slug = defaultfilters.slugify(self.name)
        super(Department, self).save(*args, **kwargs)


class Course(models.Model):
    """ First class object that contains many notes.Note objects """
    # Core metadata
    name        = models.CharField(max_length=255)
    slug        = models.SlugField(max_length=150, null=True)
    # department should remove nullable when school gets yoinked
    department  = models.ForeignKey(Department, blank=True, null=True)
    # school is an appendix: the kind that gets swollen and should be removed
    # (vistigial)
    school      = models.ForeignKey(School) 
    file_count  = models.IntegerField(default=0)

    desc        = models.TextField(max_length=511, blank=True, null=True)
    url         = models.URLField(max_length=511, blank=True, null=True)

    instructor_name     = models.CharField(max_length=255, blank=True, null=True)
    instructor_email    = models.EmailField(blank=True, null=True)

    updated_at      = models.DateTimeField(default=datetime.datetime.utcnow)

    created_at      = models.DateTimeField(auto_now_add=True)

    # Number of times this course has been flagged as abusive/spam.
    flags           = models.IntegerField(default=0,null=False)


    class Meta:
        ordering = ['-file_count', 'school', 'name']
        unique_together = ('school', 'name', 'instructor_name')
        verbose_name = 'course'
        verbose_name_plural = 'courses'

    def __unicode__(self):
        return u"{0}: {1}".format(self.name, self.school)

    def get_absolute_url(self):
        """ return url based on school slug and self slug """
        return u"/{0}/{1}".format(self.school.slug, self.slug)

    def save(self, *args, **kwargs):
        """ Save school and generate a slug if one doesn't exist """
        super(Course, self).save(*args, **kwargs) # generate a self.id
        if not self.slug:
            self.slug = defaultfilters.slugify("%s %s" % (self.name, self.id))
            self.save() # Save the slug

    def get_updated_at_string(self):
        """ return the formatted style for datetime strings """
        return self.updated_at.strftime("%I%p // %a %b %d %Y")

    @staticmethod
    def autocomplete_search_fields():
        return ("name__icontains",)

    def update_note_count(self):
        """ Update self.file_count by summing the note_set """
        self.file_count = self.note_set.count()
        self.save()


# Enforce unique constraints even when we're using a database like
# SQLite that doesn't understand them
auto_add_check_unique_together(Course)

