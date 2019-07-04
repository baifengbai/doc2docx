#!/usr/bin/env python
# encoding: utf-8

import logging

ex = 86400


def push_to_cache(redis, key, v):
    redis.set(key, v, ex=ex)
    logging.info("push into redis, key :{}, value:{}".format(key, v))


def check_cache(redis, xmf_path):
    value = redis.get(xmf_path)
    return True if value else False

