from __future__ import absolute_import, unicode_literals

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO
import tempfile
import shutil
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from django.test import TestCase
from django import forms
from django.forms import widgets
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
from django import VERSION

from mock import patch

from db_output.xorformfields import (
    FileOrURLField, MutuallyExclusiveRadioWidget,
    MutuallyExclusiveValueField, FileOrURLWidget,
    )

djversion = float('.'.join(map(str, VERSION[:2])))


class MutuallyExclusiveValueFieldTestCase(TestCase):
    def setUp(self):
        class TestForm(forms.Form):
            test_field = MutuallyExclusiveValueField(
                fields=(forms.IntegerField(), forms.IntegerField()),
                widget=MutuallyExclusiveRadioWidget(widgets=[
                    forms.Select(choices=[(1, 1), (2, 2)]),
                    forms.TextInput(attrs={'placeholder': 'Enter a number'}),
                ]))
        self.form = TestForm

    def test_first_values(self):
        form = self.form({'test_field_0': 1})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['test_field'], 1)

    def test_second_values(self):
        form = self.form({'test_field_1': 1})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['test_field'], 1)

    def test_0_values(self):
        form = self.form({})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors,
                         {'test_field':
                          [forms.Field.default_error_messages['required']]})

    def test_2_values(self):
        form = self.form({'test_field_1': 1, 'test_field_0': 42})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors,
                         {'test_field':
                          [MutuallyExclusiveValueField.too_many_values_error]})

    def test_bad_value(self):
        form = self.form({'test_field_0': 'error'})
        self.assertFalse(form.is_valid())


class MutuallyExclusiveValueFieldInferedWidgetsTestCase(
        MutuallyExclusiveValueFieldTestCase):
    def setUp(self):
        class TestForm(forms.Form):
            test_field = MutuallyExclusiveValueField(
                fields=(forms.IntegerField(), forms.TypedChoiceField(
                    choices=[(1, 'one'), (2, 'two'), (3, 'three')],
                    coerce=int)))
        self.form = TestForm

    def test_bad_choice_value(self):
        form = self.form({'test_field_1': '4'})
        self.assertFalse(form.is_valid())

    def test_generated_widget(self):
        widget = self.form().fields['test_field'].widget
        self.assertIsInstance(
            widget.widgets[0],
            widgets.NumberInput if djversion >= 1.6 else widgets.Input)
        self.assertIsInstance(widget.widgets[1], widgets.Select)
        self.assertEqual(widget.widgets[1].choices,
                         [(1, 'one'), (2, 'two'), (3, 'three')])
        self.assertHTMLEqual(
            widget.render('test', None),
            '<span id="test_container" class="mutually-exclusive-widget" '
            'style="display:inline-block">'
            '<span><input checked="" name="test_radio" type="radio" />'
            '<input name="test_0" type="number" /></span><br><span>'
            '<input name="test_radio" type="radio" /><select name="test_1">'
            '<option value="1">one</option>'
            '<option value="2">two</option>'
            '<option value="3">three</option>'
            '</select></span></span>')


class LocalizedMutuallyExclusiveValueFieldTestCase(TestCase):
    def test_first_values(self):
        w = FileOrURLWidget()
        w.is_localized = True
        w.render('test', None)


class OptionalMutuallyExclusiveValueFieldTestCase(TestCase):
    def setUp(self):
        class TestForm(forms.Form):
            test_field = MutuallyExclusiveValueField(
                required=False,
                fields=(forms.IntegerField(), forms.IntegerField()),
                widget=MutuallyExclusiveRadioWidget(widgets=[
                    forms.Select(choices=[(1, 1), (2, 2)]),
                    forms.TextInput(attrs={'placeholder': 'Enter a number'}),
                ]))
        self.form = TestForm

    def test_0_values(self):
        form = self.form({})
        self.assertTrue(form.is_valid())
        self.assertIs(form.cleaned_data['test_field'], None)


class FileOrURLTestCaseBase(TestCase):
    test_file = InMemoryUploadedFile(
        StringIO(' '), None, 'file', 'text/plain', 1, None)
    test_url = 'http://example.com/'

    def setUp(self):
        class TestForm(forms.Form):
            test_field = FileOrURLField()
        self.form = TestForm


class OptionalFileOrURLTestCase(FileOrURLTestCaseBase):
    def setUp(self):
        class TestForm(forms.Form):
            test_field = FileOrURLField(required=False)
        self.form = TestForm

    def test_0_values(self):
        form = self.form({})
        self.assertTrue(form.is_valid())
        self.assertIs(form.cleaned_data['test_field'], None)


class FileOrURLTestZeroOrTwoValsMixin():
    def test_0_values(self):
        form = self.form({})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors,
                         {'test_field':
                          [forms.Field.default_error_messages['required']]})

    def test_2_values(self):
        form = self.form(
            {'test_field_1': self.test_url},
            {'test_field_0': self.test_file},
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors,
                         {'test_field':
                          [MutuallyExclusiveValueField.too_many_values_error]})


class FileOrURLPassthroughTestCase(FileOrURLTestZeroOrTwoValsMixin,
                                   FileOrURLTestCaseBase):
    def test_validate_url_passthrough(self):
        form = self.form({
            'test_field_1': self.test_url,
            })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['test_field'], self.test_url)

    def test_validate_file_passthrough(self):
        form = self.form({}, {
            'test_field_0': self.test_file,
            })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['test_field'], self.test_file)


class FileOrURLToURLTestCase(FileOrURLTestZeroOrTwoValsMixin,
                             FileOrURLTestCaseBase):
    def setUp(self):
        class TestForm(forms.Form):
            test_field = FileOrURLField(to='url', upload_to='TEST',
                                        no_aws_qs=True)
        self.form = TestForm

        settings._original_media_root = settings.MEDIA_ROOT
        self._temp_media = tempfile.mkdtemp()
        settings.MEDIA_ROOT = self._temp_media

    def tearDown(self):
        settings.MEDIA_ROOT = settings._original_media_root
        shutil.rmtree(self._temp_media, ignore_errors=True)

    def test_validate_url_passthrough(self):
        form = self.form({
            'test_field_1': self.test_url,
            })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['test_field'], self.test_url)

    def test_validate_file(self):
        form = self.form({}, {
            'test_field_0': self.test_file,
            })
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data['test_field'],
            urljoin(settings.MEDIA_URL, 'TEST/file'))


class FileOrURLToFileTestCase(FileOrURLTestZeroOrTwoValsMixin,
                              FileOrURLTestCaseBase):
    test_resp = 'foobar'

    def setUp(self):
        class TestForm(forms.Form):
            test_field = FileOrURLField(to='file')
        self.form = TestForm

    def test_validate_file_passthrough(self):
        form = self.form({}, {
            'test_field_0': self.test_file,
            })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['test_field'], self.test_file)

    @patch('requests.get')
    def test_validate_url(self, mock_get):
        class MockResp(object):
            status_code = 200
            content = self.test_resp
            headers = {'content-type': 'text/plain'}
        mock_get.return_value = MockResp()
        form = self.form({'test_field_1': 'http://example.com'}, {})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data['test_field'].read(),
            self.test_resp)

    @patch('requests.get')
    def test_validate_bad_url(self, mock_get):
        class MockResp(object):
            status_code = 400
            content = self.test_resp
            headers = {'content-type': 'text/plain'}
        mock_get.return_value = MockResp()
        form = self.form({'test_field_1': 'http://example.com'}, {})
        self.assertFalse(form.is_valid())

    @patch('requests.get')
    def test_validate_bad_request(self, mock_get):
        def raise_exception():
            raise Exception
        mock_get.side_effect = raise_exception
        form = self.form({'test_field_1': 'http://example.com'}, {})
        self.assertFalse(form.is_valid())


class FileOrURLToURLBadConfTestCase(FileOrURLToURLTestCase):
    def test_no_upload_to(self):
        self.assertRaises(RuntimeError, FileOrURLField, to='url')


class MutuallyExclusiveRadioWidgetTestCase(TestCase):
    def test_mutuallyexclusiveradiowidget(self):
        w = MutuallyExclusiveRadioWidget(widgets=[
            forms.Select(choices=[(1, 1), (2, 2)]),
            forms.TextInput(attrs={'placeholder': 'Enter a number'}),
            ])
        self.assertHTMLEqual(
            w.render('test', None),
            '<span id="test_container" class="mutually-exclusive-widget" '
            'style="display:inline-block">'
            '<span><input checked="" name="test_radio" type="radio" />'
            '<select name="test_0"><option value="1">1</option>'
            '<option value="2">2</option></select></span><br>'
            '<span><input name="test_radio" type="radio" />'
            '<input name="test_1" placeholder="Enter a number" type="text" />'
            '</span></span>')
        self.assertHTMLEqual(
            w.render('test', ''),
            '<span id="test_container" class="mutually-exclusive-widget" '
            'style="display:inline-block">'
            '<span><input checked="" name="test_radio" type="radio" />'
            '<select name="test_0"><option value="1">1</option>'
            '<option value="2">2</option></select></span><br>'
            '<span><input name="test_radio" type="radio" />'
            '<input name="test_1" placeholder="Enter a number" type="text" />'
            '</span></span>')
        self.assertHTMLEqual(
            w.render('test', '1'),
            '<span id="test_container" class="mutually-exclusive-widget" '
            'style="display:inline-block">'
            '<span><input checked="" name="test_radio" type="radio" />'
            '<select name="test_0"><option value="1">1</option>'
            '<option value="2">2</option></select></span><br>'
            '<span><input name="test_radio" type="radio" />'
            '<input name="test_1" placeholder="Enter a number" type="text" />'
            '</span></span>')
        self.assertHTMLEqual(
            w.render('test', ['1', None]),
            '<span id="test_container" class="mutually-exclusive-widget" '
            'style="display:inline-block">'
            '<span><input checked="" name="test_radio" type="radio" />'
            '<select name="test_0"><option value="1" selected="selected">1'
            '</option><option value="2">2</option></select></span><br>'
            '<span><input name="test_radio" type="radio" />'
            '<input name="test_1" placeholder="Enter a number" type="text" />'
            '</span></span>')
        self.assertHTMLEqual(
            w.render('test', [None, '1']),
            '<span id="test_container" class="mutually-exclusive-widget" '
            'style="display:inline-block">'
            '<span><input name="test_radio" type="radio" />'
            '<select name="test_0"><option value="1">1</option>'
            '<option value="2">2</option></select></span><br><span>'
            '<input checked="" name="test_radio" type="radio" />'
            '<input name="test_1" placeholder="Enter a number" type="text" '
            'value="1" /></span></span>')


class FileOrURLWidgetTestCase(TestCase):
    test_file = InMemoryUploadedFile(
        StringIO(' '), None, 'file', 'text/plain', 1, None)

    def test_fileorurlwidget(self):
        w = FileOrURLWidget()
        self.assertHTMLEqual(
            w.render('test', None),
            '<span id="test_container" class="mutually-exclusive-widget" '
            'style="display:inline-block">'
            '<span><input checked="" name="test_radio" type="radio" />'
            '<input name="test_0" type="file" /></span><br><span>'
            '<input name="test_radio" type="radio" />'
            '<input name="test_1" placeholder="Enter URL" type="url" />'
            '</span></span>')
        self.assertHTMLEqual(
            w.render('test', ''),
            '<span id="test_container" class="mutually-exclusive-widget" '
            'style="display:inline-block">'
            '<span><input checked="" name="test_radio" type="radio" />'
            '<input name="test_0" type="file" /></span><br><span>'
            '<input name="test_radio" type="radio" />'
            '<input name="test_1" placeholder="Enter URL" type="url" />'
            '</span></span>')
        self.assertHTMLEqual(
            w.render('test', self.test_file),
            '<span id="test_container" class="mutually-exclusive-widget" '
            'style="display:inline-block">'
            '<span><input checked="" name="test_radio" type="radio" />'
            '<input name="test_0" type="file" /></span><br><span>'
            '<input name="test_radio" type="radio" />'
            '<input name="test_1" placeholder="Enter URL" type="url" />'
            '</span></span>')
        self.assertHTMLEqual(
            w.render('test', 'http://example.com'),
            '<span id="test_container" class="mutually-exclusive-widget" '
            'style="display:inline-block">'
            '<span><input name="test_radio" type="radio" />'
            '<input name="test_0" type="file" /></span><br><span>'
            '<input checked="" name="test_radio" type="radio" />'
            '<input name="test_1" placeholder="Enter URL" type="url" '
            'value="http://example.com"/>'
            '</span></span>')
        self.assertHTMLEqual(
            w.render('test', [None, 'http://example.com']),
            '<span id="test_container" class="mutually-exclusive-widget" '
            'style="display:inline-block">'
            '<span><input name="test_radio" type="radio" />'
            '<input name="test_0" type="file" /></span><br><span>'
            '<input checked="" name="test_radio" type="radio" />'
            '<input name="test_1" placeholder="Enter URL" type="url" '
            'value="http://example.com" />'
            '</span></span>')
        self.assertHTMLEqual(
            w.render('test', []),
            '<span id="test_container" class="mutually-exclusive-widget" '
            'style="display:inline-block">'
            '<span><input checked="" name="test_radio" type="radio" />'
            '<input name="test_0" type="file" /></span><br><span>'
            '<input name="test_radio" type="radio" />'
            '<input name="test_1" placeholder="Enter URL" type="url" />'
            '</span></span>')

    def test_fileorurlwidget_with_id(self):
        w = FileOrURLWidget(attrs={'id': 'test'})
        self.assertHTMLEqual(
            w.render('test', None),
            '<span id="test_container" class="mutually-exclusive-widget" '
            'style="display:inline-block">'
            '<span><input checked="" name="test_radio" type="radio" />'
            '<input id="test_0" name="test_0" type="file" /></span><br><span>'
            '<input name="test_radio" type="radio" />'
            '<input id="test_1" name="test_1" placeholder="Enter URL" '
            'type="url" /></span></span>')

    def test_fileorurlwidget_value_from_datadict(self):
        w = FileOrURLWidget()
        w.value_from_datadict({'test': self.test_file}, {}, 'test')
        w.value_from_datadict({}, {'test': 'http://example.com'}, 'test')
