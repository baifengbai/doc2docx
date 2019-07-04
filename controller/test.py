#!/usr/bin/env python
# encoding: utf-8

from util.base_handler import BaseHandler


class FirstHandler(BaseHandler):
    def get(self):
        a = self.get_argument('a', 0, type_=int)
        b = self.get_argument('b', 0, type_=int)
        self.write({'ans': a + b})
