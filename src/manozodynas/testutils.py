import urllib
from urlparse import urljoin

import lxml.html
from lxml.etree import XMLSyntaxError

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import translation
from django.utils.translation import trans_null
from django.utils.datastructures import MultiValueDict


def lxml_form_data(form):
    """Get form data as MultiValueDict from lxml Form element"""
    data = MultiValueDict()
    for obj in form.cssselect('input[type=text],'
                              'input[type=hidden],'
                              'textarea'):
        data.appendlist(
            obj.name,
            obj.value or ''
        )
    for obj in form.cssselect('input[type=checkbox][checked],'
                              'input[type=radio][checked]'):
        data.appendlist(
            obj.name,
            obj.value or '',
        )
    for obj in form.cssselect('select'):
        for opt in obj.cssselect('option[selected]'):
            data.appendlist(
                obj.name,
                opt.get('value'),
            )
    return data


class StatefulTesting(TestCase):
    def setUp(self):
        self.state = {}

    def reset(self, **kwargs):
        self.state = {}
        self.state.update(kwargs)

    def get_html(self):
        if self.state.get('html', None) is None:
            url = self.state['response_url']
            content = self.state['response'].content.decode('utf-8')
            assert content, "%s, content is empty" % url
            try:
                self.state['html'] = lxml.html.fromstring(content)
            except XMLSyntaxError, e:
                r = [url]
                r.append(unicode(e))
                ln, pos = e.position
                excerpt = content.splitlines()[ln - 3:ln + 3]
                excerpt = ['%d.  %s' % (i + ln - 3, line) for i, line in
                           enumerate(excerpt)]
                r.extend(excerpt)
                assert False, '\n'.join(r)
        return self.state['html']

    def login(self, username, password):
        assert self.client.login(username=username, password=password), \
            'Can not login as %s:%s' % (username, password)

    def open(self, *args, **kwargs):
        self.reset()
        url = self._getUrl(*args, **kwargs)
        self.state['response'] = self.client.get(url)
        self.state['response_url'] = url
        return self.state['response']

    def assertStatusCode(self, code):
        a = self.state['response'].status_code
        b = code
        assert a == b, 'Expecting status code %s, got: %s (url: %s)' % (
            b, a, self.state['response_url']
        )

    def assertRedirects(self, *args, **kwargs):
        response = self.state['response']
        target_status_code = kwargs.pop('target_status_code', 200)
        url = self._getUrl(*args, **kwargs)
        super(StatefulTesting, self).assertRedirects(response, url,
                                                     target_status_code=target_status_code)

    def selectTable(self, css):
        self.selectOne(css)
        self.assertTag('table')

    def assertTableHasRows(self, query, n=1):
        table = self.state['selection']
        i = sum(1 for tr in table.cssselect('tr')
                if query in tr.text_content())
        if i != int(n):
            try:
                table_as_text = self.formatTable(table)
            except Exception:
                table_as_text = lxml.html.tostring(table)
            self.fail("Found %d rows matching %s in:\n%s" % (i, query, table_as_text))

    def assertTag(self, name):
        if self.state['selection'].tag != name:
            self.fail('Element tag mismatch %r != %r' % (
                name, self.state['selection'].tag
            ))

    def selectForm(self, css):
        f = self.selectOne(css)
        self.assertTag('form')
        return f

    def submitForm(self, data, follow=False):
        self.assertTag('form')
        form = self.state['selection']
        d = lxml_form_data(form)
        data = dict(d.lists(), **data)
        url = urljoin(self.state['response_url'], form.action)
        self.reset()
        self.state['response'] = self.client.post(url, data, follow=follow)
        self.state['response_url'] = url
        return self.state['response']

    def assertFieldValue(self, field, value):
        self.assertTag('form')
        fields = self.state['selection'].fields
        if not field in fields.keys():
            self.fail('No such field %s, available fields are: %r' %
                      (field, fields.keys()))
        self.assertEqual(fields[field], value)

    def selectOne(self, css):
        selection = self.selectMany(css)
        self._assertSingleSelection(css, selection)
        self.state['selection'] = selection[0]
        return selection[0]

    def selectMany(self, css):
        html = self.get_html()
        selection = html.cssselect(css)
        if not len(selection):
            self.fail('No elements matching: %r' % css)
        self.state['selection'] = selection
        return selection

    def assertContent(self, css, content, base='#main '):
        html = self.get_html()
        css = base + css
        selection = html.cssselect(css)
        self._assertSingleSelection(css, selection)
        self.assertEqual(content, selection[0].text_content())

    def assertActiveMainMenu(self, *args, **kwargs):
        url = self._getUrl(*args, **kwargs)
        self.selectOne('header .active a[href="%s"]' % url)

    def assertInBreadcrumb(self, *args, **kwargs):
        url = self._getUrl(*args, **kwargs)
        self.selectOne('.breadcrumb a[href="%s"]' % url)

    def assertActiveSideMenu(self, *args, **kwargs):
        url = self._getUrl(*args, **kwargs)
        self.selectMany('.sidebar .nav .active a[href="%s"]' % url)

    def getCheckboxNameForRowWithText(self, text):
        selection = self.getCheckboxNamesForRowsWithText(text)
        if len(selection) > 1:
            self.fail('Found more than one checkbox'
                      ' next to a table cell with %r: %r'
                      % (text, selection))
        return selection[0]

    def getCheckboxNamesForRowsWithText(self, text, fail_if_none_found=True):
        return [checkbox.get('name') for checkbox in
                self._getCheckboxesForRowsWithText(text, fail_if_none_found)]

    def getCheckboxValueForRowWithText(self, text):
        selection = self.getCheckboxValuesForRowsWithText(text)
        if len(selection) > 1:
            self.fail('Found more than one checkbox'
                      ' next to a table cell with %r: %r'
                      % (text, selection))
        return selection[0]

    def getCheckboxValuesForRowsWithText(self, text, fail_if_none_found=True):
        return [checkbox.get('value') for checkbox in
                self._getCheckboxesForRowsWithText(text, fail_if_none_found)]

    def _getCheckboxesForRowsWithText(self, text, fail_if_none_found=True):
        # we expect a table to be selected before this
        assert '"' not in text and '\\' not in text, (
            "xpath quoting not implemented yet")
        self.assertTag('table')
        table = self.state['selection']
        selection = table.xpath(
            u'.//td[contains(., "%s")]/../td/input[@type="checkbox"]'
            % text)
        if not selection and fail_if_none_found:
            self.fail('Cannot find a checkbox next to a table cell with %r'
                      % text)
        return selection

    def _assertSingleSelection(self, css, selection):
        if len(selection) > 1:
            self.fail('Found more than one element matching %r: %r' %
                      (css, selection))
        elif len(selection) == 0:
            self.fail('Cannot find element by this CSS selector: %r' % css)

    def _getUrl(self, name, *args, **kwargs):
        if '/' in name:
            return name
        else:
            params = kwargs.pop('GET', None)
            url = reverse(name, args=args, kwargs=kwargs)
            if params:
                url = '%s?%s' % (url, urllib.urlencode(params))
                # urlencode uses urllib.quote_plus, that does not have safe set
                # to '/' and if this symbol gets substitutes, assertRedirects
                # tests will fail.
                url = url.replace('%2F', '/')
            return url


class disable_i18n(override_settings):
    """Disable I18N in tests.

    Does django.utils.translation monkey patching to temporary disable I18N.

    This cannot be done simply using override_settings(USE_I18N=False), because
    translation functions are cached after first call.

    You can use this class same way as override_settings:

        https://docs.djangoproject.com/en/dev/topics/testing/#django.test.utils.override_settings

    """
    def enable(self):
        self.trans = translation._trans
        translation._trans = trans_null

    def disable(self):
        translation._trans = self.trans
