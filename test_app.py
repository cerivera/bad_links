from unittest import TestCase
from unittest.mock import patch, MagicMock
from http import HTTPStatus
from requests.exceptions import ConnectionError

import app


class TestNotFound(TestCase):
    sample_bytes_content = b'<!doctype html>\n<html>\n<head>\n    <title>Example Domain</title>\n\n    <meta charset="utf-8" />\n    <meta http-equiv="Content-type" content="text/html; charset=utf-8" />\n    <meta name="viewport" content="width=device-width, initial-scale=1" />\n    <style type="text/css">\n    body {\n        background-color: #f0f0f2;\n        margin: 0;\n        padding: 0;\n        font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", "Open Sans", "Helvetica Neue", Helvetica, Arial, sans-serif;\n        \n    }\n    div {\n        width: 600px;\n        margin: 5em auto;\n        padding: 2em;\n        background-color: #fdfdff;\n        border-radius: 0.5em;\n        box-shadow: 2px 3px 7px 2px rgba(0,0,0,0.02);\n    }\n    a:link, a:visited {\n        color: #38488f;\n        text-decoration: none;\n    }\n    @media (max-width: 700px) {\n        div {\n            margin: 0 auto;\n            width: auto;\n        }\n    }\n    </style>    \n</head>\n\n<body>\n<div>\n    <h1>Example Domain</h1>\n    <p>This domain is for use in illustrative examples in documents. You may use this\n    domain in literature without prior coordination or asking for permission.</p>\n   <a href="https://somebadlink.com/abc123">Bad Link</a> <p><a href="https://www.iana.org/domains/example">More information...</a></p>\n</div>\n</body>\n</html>\n'
    sample_string_content = sample_bytes_content.decode('utf-8')
    good_url = 'https://www.iana.org/domains/example' 
    broken_url = 'https://somebadlink.com/abc123'

    def test_with_bad_source(self):
        with patch('app.requests.get') as mock_requests_get:
            mocked_response = MagicMock()
            mocked_response.ok = False
            mock_requests_get.return_value = mocked_response

            self.assertRaises(app.BadSourceUrl, app.find_bad_links_slow, 'http://somebadurl.com')

    def test_good_source_no_exception(self):
        with patch('app.requests.get') as mock_requests_get:
            mocked_response = MagicMock()
            mocked_response.ok = True
            mocked_response.content = b''
            mock_requests_get.return_value = mocked_response

            try:
                app.find_bad_links_slow('http://somegoodurl.com')
            except app.BadSourceUrl:
                self.fail('BadSourceUrl raised')
    
    def test_get_content(self):
        with patch('app.requests.get') as mock_requests_get:
            mocked_response = MagicMock()
            mocked_response.content = self.sample_bytes_content
            mock_requests_get.return_value = mocked_response

            content = app.get_content_from_url('http://somefunurl.com')
            self.assertTrue(isinstance(content, str))

    def test_find_urls(self):
        urls = app.find_urls_in_content(self.sample_string_content)

        self.assertTrue(urls)
        self.assertTrue(self.good_url in urls)
        self.assertTrue(self.broken_url in urls)
        self.assertFalse('https://npr.org' in urls)

    def test_find_bad_links(self):
        with patch('app.get_content_from_url') as mock_get_content:
            mock_get_content.return_value = self.sample_string_content
            bad_urls = app.find_bad_links_slow('http://somefunurl.com')
            self.assertTrue(bad_urls)
            self.assertTrue(self.broken_url in bad_urls)
            self.assertFalse(self.good_url in bad_urls)

    def test_bad_link(self):
        with patch('app.requests.get') as mock_requests_get:
            mocked_response = MagicMock()
            mocked_response.ok = False
            mock_requests_get.return_value = mocked_response

            self.assertTrue(app.is_link_bad('http://somebadlink.com')[0])

            mock_requests_get.side_effect = ConnectionError()
            self.assertTrue(app.is_link_bad('http://anotherbadlink.com')[0])

    def test_good_link(self):
        with patch('app.requests.get') as mock_requests_get:
            mocked_response = MagicMock()
            mocked_response.ok = True
            mock_requests_get.return_value = mocked_response

            self.assertFalse(app.is_link_bad('http://somebadlink.com')[0])