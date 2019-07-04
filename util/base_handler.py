#!/usr/bin/env python
# encoding=utf-8
import logging

from tornado.web import RequestHandler

from bson.json_util import dumps, loads
from util.escape import json_encode, safe_typed_from_str
from errors import BLError, DTError


class BaseHandler(RequestHandler):
    def prepare(self):
        uri = self.request.uri
        logging.info('accessing %s' % (uri))
        paths = self.request.path.split('/')
        if len(paths) >= 2:
            self.subject_name = paths[1]
        else:
            self.subject_name = self.application.settings['default_subject']
        if self.subject_name not in self.application.settings['subjects']:
            self.subject_name = self.application.settings['default_subject']

    @property
    def subject(self):
        return self.application.settings.get('subjects')[self.subject_name]

    @property
    def site_root(self):
        return self.subject.site_root

    @property
    def redis(self):
        return self.application.settings.get('redis')

    @property
    def oss_bucket(self):
        return self.application.settings.get('oss_bucket')

    def get_argument(self, name, *args, **kwargs):
        type_ = kwargs.pop("type_", None)
        arg = super(BaseHandler, self).get_argument(name, *args, **kwargs)
        if type_ and isinstance(arg, basestring):
            return safe_typed_from_str(arg, type_)
        else:
            return arg

    def write(self, chunk):
        """
            override write to support our json_encode
        """
        if isinstance(chunk, dict):
            chunk = json_encode(chunk)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        super(BaseHandler, self).write(chunk)

    def write_error(self, status_code, **kwargs):
        if status_code == 403:
            self.write('no previlege')
            return
        else:
            return super(BaseHandler, self).write_error(status_code, **kwargs)

    def _handle_request_exception(self, e):
        # adapted from tornado
        # doubt whether this is a good idea
        if isinstance(e, BLError):
            if self.is_ajax_request():
                self.write({
                    'error_msg': e.message
                })
            else:
                self.write(e.message)
            if not self._finished:
                self.finish()
            return
        elif isinstance(e, DTError):
            if self.is_ajax_request():
                self.write({
                    'error_code': 1,
                    'error_msg': e.message
                })
            else:
                self.write({
                    'error_code': 1,
                    'error_msg': e.message
                })
            if not self._finished:
                self.finish()
            return

        return super(BaseHandler, self)._handle_request_exception(e)

    def is_ajax_request(self):
        return self.request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def dumps(self, obj):
        return dumps(obj, ensure_ascii=False, indent=4, sort_keys=True)

    @staticmethod
    def loads(s):
        return loads(s)


class Subject(object):
    def __init__(self, rds, name, types):
        self._redis = rds
        self._name = name
        self._types = types
        if name == 'math':
            self._type2cn = {1001: u'选择题', 1002: u"填空题", 1003: u"解答题"}
        else:
            self._type2cn = {2001: u'选择题', 2002: u"填空题", 2003: u"解答题"}

    @property
    def name(self):
        return self._name

    @property
    def site_root(self):
        return "/%s" % self._name

    @property
    def types(self):
        return self._types

    @property
    def type2cn(self):
        return self._type2cn

    @property
    def redis(self):
        return self._redis
