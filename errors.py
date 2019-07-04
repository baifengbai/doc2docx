#!/usr/bin/env python
# encoding: utf-8


class BLError(Exception):
    def __init__(self, msg):
        self.message = msg


class DTError(Exception):
    def __init__(self, msg):
        self.message = msg
