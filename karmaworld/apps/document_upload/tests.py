"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase, Client
from karmaworld.apps.courses.models import School, Course
from karmaworld.apps.document_upload.forms import RawDocumentForm
from karmaworld.apps.notes.gdrive import *
from karmaworld.apps.notes.models import Note

CREDENTIALS_PATH = os.path.join(settings.DJANGO_ROOT,
                    'secret/oauth_token.json')

# NOTE: these tests require that you have the file
# secret/oauth_token.json. See docs/source/gdrive.rst
# for how to set this up.

class ConversionTest(TestCase):


    def setUp(self):
        self.school = School(name='Northeastern University')
        self.school.save()
        self.course = Course(name='Intro to Advanced Study', school=self.school)
        self.course.save()
        self.client = Client()
        self.setUpGDriveAuth()

    def setUpGDriveAuth(self):
        try:
            f = open(CREDENTIALS_PATH)
        except IOError:
            raise RuntimeError("Could not find {c}, did you create it? See docs/source/gdrive.rst".format(c=CREDENTIALS_PATH))
        creds_str = f.read()
        f.close()
        DriveAuth(credentials=creds_str).save()

    def doConversionForPost(self, post):
        self.assertEqual(Note.objects.count(), 0)
        r_d_f = RawDocumentForm(post)
        self.assertTrue(r_d_f.is_valid())
        raw_document = r_d_f.save(commit=False)
        raw_document.fp_file = post['fp_file']
        convert_raw_document(raw_document)
        self.assertEqual(Note.objects.count(), 1)

    def testPlaintextConversion(self):
        self.doConversionForPost({'fp_file': 'https://www.filepicker.io/api/file/S2lhT3INSFCVFURR2RV7',
                                 'course': str(self.course.id),
                                 'name': 'graph3.txt',
                                 'tags': '',
                                 'mimetype': 'text/plain'})

    def testEvernoteConversion(self):
        self.doConversionForPost({'fp_file': 'https://www.filepicker.io/api/file/vOtEo0FrSbu2WDbAOzLn',
                                 'course': str(self.course.id),
                                 'name': 'KarmaNotes test 3',
                                 'tags': '',
                                 'mimetype': 'text/enml'})

    def testPdfConversion(self):
        self.doConversionForPost({'fp_file': 'https://www.filepicker.io/api/file/8l6mtMURnu1uXvcvJo9s',
                                 'course': str(self.course.id),
                                 'name': 'geneve_1564.pdf',
                                 'tags': '',
                                 'mimetype': 'application/pdf'})

    def testGarbage(self):
        with self.assertRaises(ValueError):
            self.doConversionForPost({'fp_file': 'https://www.filepicker.io/api/file/H85Xl8VURqiGusxhZKMl',
                                     'course': str(self.course.id),
                                     'name': 'random',
                                     'tags': '',
                                     'mimetype': 'application/octet-stream'})

