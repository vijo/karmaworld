#!/usr/bin/env python
# -*- coding:utf8 -*-
# Copyright (C) 2012  FinalsClub Foundation

import json
import os.path
import requests

from apps.notes.models import Note
from apps.notes.gdrive import convert_raw_document
from apps.courses.models import Course
from apps.courses.models import School
from apps.courses.models import Professor
from apps.courses.models import Department
from apps.courses.models import ProfessorTaught
from apps.courses.models import ProfessorAffiliation
from apps.licenses.models import License
from apps.document_upload.models import RawDocument
from django.core.management.base import BaseCommand
from karmaworld.secret.filepicker import FILEPICKER_API_KEY

class Command(BaseCommand):
    args = 'directory containing json files from mit-ocw-scraper'
    help = """
           This command will systematically parse all *.json files in the given
           directory and load them into the database as course notes, uploaded
           through Filepicker.

           It is assumed the json files are generated by (or follow the same
           format as) mit-ocw-scraper:
           https://github.com/AndrewMagliozzi/mit-ocw-scraper
           """

    def handle(self, *args, **kwargs):
        if len(args) != 1:
            raise ArgumentError("Expected one argument, got none: please specify a directory to parse.")

        # Convert given path to an absolute path, not relative.
        path = os.path.abspath(args[0])

        if not os.path.isdir(path):
            raise ArgumentError("First argument should be a directory to parse.")

        # for now, assume the school is MIT and find by its US DepEd ID.
        # TODO for later, do something more clever
        dbschool = School.objects.filter(usde_id=121415)[0]

        # for now, assume license is the default OCW license: CC-BY-NC 3
        # TODO for later, do something more clever.
        dblicense = License.objects.get_or_create(
          name='cc-by-nc-3.0',
          html='<a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/"><img alt="Creative Commons License" style="border-width:0" src="http://i.creativecommons.org/l/by-nc/4.0/88x31.png" /></a>'
        )[0]

        # build Filepicker upload URL
        # http://stackoverflow.com/questions/14115280/store-files-to-filepicker-io-from-the-command-line
        fpurl = 'https://www.filepicker.io/api/store/S3?key={0}'.format(FILEPICKER_API_KEY)

        # find all *.json files in the given directory
        def is_json_file(filename):
            return filename[-5:].lower() == '.json'
        json_files = filter(is_json_file, os.listdir(path))
        # prepend filenames with absolute paths
        def full_path_to_file(filename):
            return os.path.sep.join((path, filename))
        json_files = map(full_path_to_file, json_files)

        # parse each json file and process it for courses and notes.
        for filename in json_files:
            with open(filename, 'r') as jsondata:
                # parse JSON into python
                parsed = json.load(jsondata)

                # find the department or create one.
                dept_info = {
                    'name': parsed['subject'],
                    'school': dbschool,
                    'url': parsed['departmentLink'],
                }
                dbdept = Department.objects.get_or_create(**dept_info)[0]

                # process courses
                for course in parsed['courses']:
                    # Assume first hit is always right. Solving the identity
                    # problem by name alone will always be a fool's errand.
                    dbprof = Professor.objects.get_or_create(name=course['professor'])[0]

                    # Associate the professor with the department.
                    # (no need to track the result)
                    ProfessorAffiliation.objects.get_or_create(
                        professor=dbprof,
                        department=dbdept)

                    # Extract the course info
                    course_info = {
                      'name': course['courseTitle'],
                      'department': dbdept,
                    }
                    # Create or Find the Course object.
                    dbcourse = Course.objects.get_or_create(**course_info)[0]
                    dbcourse.professor = dbprof
                    dbcourse.instructor_name = course['professor']
                    dbcourse.school = dbschool
                    dbcourse.save()
                    print "Course is in the database: {0}".format(dbcourse.name)

                    ProfessorTaught.objects.get_or_create(
                        professor=dbprof,
                        course=dbcourse)

                    if 'noteLinks' not in course or not course['noteLinks']:
                        print "No Notes in course."
                        continue

                    # process notes for each course
                    for note in course['noteLinks']:
                        # Check to see if the Note is already uploaded.
                        url = note['link']
                        dbnote = Note.objects.filter(upstream_link=url)
                        if len(dbnote) > 2:
                            print "WARNING Skipping Note: Too many notes for {0}".format(url)
                            continue
                        if len(dbnote) == 1:
                            dbnote = dbnote[0]
                            if dbnote.text and len(dbnote.text) or \
                               dbnote.html and len(dbnote.html):
                                print "Already there, moving on: {0}".format(url)
                                continue
                            else:
                                # Partially completed note. Remove it and try
                                # again.
                                dbnote.tags.set() # clear tags
                                dbnote.delete() # delete note
                                print "Found and removed incomplete note {0}.".format(url)

                        # Upload URL of note to Filepicker if it is not already
                        # in RawDocument.
                        rd_test = RawDocument.objects.filter(upstream_link=url)
                        if not len(rd_test):
                            # https://developers.inkfilepicker.com/docs/web/#inkblob-store
                            print "Uploading link {0} to FP.".format(url)
                            ulresp = requests.post(fpurl, data={
                              'url': url,
                            })
                            try:
                                ulresp.raise_for_status()
                            except Exception, e:
                                print "Failed to upload note: " + str(e)
                                print "Skipping."
                                continue
                            # Filepicker returns JSON, so use that
                            uljson = ulresp.json()

                            print "Saving raw document to database."
                            # Extract the note info
                            dbnote = RawDocument()
                            dbnote.course = dbcourse
                            dbnote.name = note['fileName']
                            dbnote.license = dblicense
                            dbnote.upstream_link = url
                            dbnote.fp_file = uljson['url']
                            dbnote.mimetype = uljson['type']
                            dbnote.is_processed = True # hack to bypass celery
                            # Create the RawDocument object.
                            dbnote.save()
                        else:
                            # Find the right RawDocument
                            print "Already uploaded link {0} to FP.".format(url)
                            dbnote = rd_test[0]

                        # Do tags separately
                        dbnote.tags.add('mit-ocw','karma')

                        print "Converting document and saving note to S3."
                        while True:
                            try:
                                convert_raw_document(dbnote)
                            except ValueError, e:
                                # only catch one specific error
                                if not str(e).startswith('PDF file could not be'):
                                    raise e
                                # write the link to file.
                                with open('pdferrors.log', 'a') as pdferrs:
                                    pdferrs.write(url + '\n')
                                # delete the partial Note created in convert_raw_doc
                                dbnote = Note.objects.filter(upstream_link=url)[0]
                                dbnote.tags.set()
                                dbnote.delete()
                                print "This note errored, so it is removed :("
                                break
                            except Exception, e:
                                if '403' in str(e):
                                    print "Failed: " + str(e)
                                    print "Trying again."
                                    continue
                                else:
                                    print "Failed: " + str(e)
                                    print "Aborting."
                                    break
                            else:
                                print "This note is done."
                                break

                    print "Notes for {0} are done.".format(dbcourse.name)
