"""
Restful json clients.

Use `Resource`_ for a connection to a single host.
"""

import warnings
import io
import gzip
import shutil
import httplib
import urllib
import urlparse
from .utils import json


class Response(httplib.HTTPResponse):
    "A completed response which handles json and caches its body."
    content_type = 'application/json'

    def end(self):
        self.body = self.read()
        self.time = float(self.getheader('x-response-time', 'nan'))
        if 'gzip' in self.getheader('content-encoding', ''):
            self.body = gzip.GzipFile(fileobj=io.BytesIO(self.body)).read()

    def __nonzero__(self):
        "Return whether status is successful."
        return httplib.OK <= self.status < httplib.MULTIPLE_CHOICES

    def __call__(self):
        "Return evaluated response body or raise exception."
        body = self.body
        if body and self.getheader('content-type').startswith(self.content_type):
            body = json.loads(body)
        code, agent, text = self.getheader('warning', '  ').split(' ', 2)
        if agent == 'lupyne':
            warnings.warn(json.loads(text))
        if self:
            return body
        raise httplib.HTTPException(self.status, self.reason, body)


class Resource(httplib.HTTPConnection):
    "Synchronous connection which handles json responses."
    response_class = Response
    headers = {'accept-encoding': 'compress, gzip', 'content-length': '0'}

    def request(self, method, path, body=None):
        "Send request after handling body and headers."
        headers = dict(self.headers)
        if body is not None:
            body = json.dumps(body)
            headers.update({'content-length': str(len(body)), 'content-type': self.response_class.content_type})
        httplib.HTTPConnection.request(self, method, path, body, headers)

    def getresponse(self, filename=''):
        "Return completed response, optionally write response body to a file."
        response = httplib.HTTPConnection.getresponse(self)
        if response and filename:
            with open(filename, 'w') as output:
                shutil.copyfileobj(response, output)
        response.end()
        return response

    def call(self, method, path, body=None, params=(), redirect=False):
        "Send request and return completed `response`_."
        if params:
            path += '?' + urllib.urlencode(params, doseq=True)
        self.request(method, path, body)
        response = self.getresponse()
        if redirect and httplib.MULTIPLE_CHOICES <= response.status < httplib.NOT_MODIFIED:
            url = urlparse.urlparse(response.getheader('location'))
            assert url.netloc.startswith(self.host)
            warnings.warn('{}: {}'.format(response.reason, url.path), DeprecationWarning)
            return self.call(method, url.path, body, params, redirect - 1)
        return response

    def download(self, path, filename):
        "Download response body from GET request to a file."
        self.request('GET', path)
        return self.getresponse(filename)()

    def multicall(self, *requests):
        "Pipeline requests (method, path[, body]) and generate completed responses."
        responses = []
        for request in requests:
            self.request(*request)
            responses.append(self.response_class(self.sock, self.debuglevel, self.strict, self._method))
            self._HTTPConnection__state = 'Idle'
        return (response.begin() or response.end() or response for response in responses)

    def get(self, path, **params):
        "Return response body from GET request."
        return self.call('GET', path, params=params)()
    def post(self, path, body=None, **kwargs):
        "Return response body from POST request."
        return self.call('POST', path, body, **kwargs)()
    def put(self, path, body=None, **kwargs):
        "Return response body from PUT request."
        return self.call('PUT', path, body, **kwargs)()
    def delete(self, path, **params):
        "Return response body from DELETE request."
        return self.call('DELETE', path, params=params)()
    def patch(self, path, body=None, **kwargs):
        "Return response body from PATCH request."
        return self.call('PATCH', path, body, **kwargs)()


if hasattr(httplib, 'HTTPSConnection'):  # pragma: no branch
    class SResource(Resource, httplib.HTTPSConnection, object):
        pass
