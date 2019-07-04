#!/usr/bin/env python
# encoding: utf-8

import os
import re
import logging

from bson import ObjectId
from tornado.options import options
from util.oss_file_util import save_oss, open_oss

from tornado.httpclient import AsyncHTTPClient
from tornado.gen import coroutine
from tornado.gen import Return

@coroutine
def xmf2png(xmf_path):
    xmf2png = options.xmf2png
    png_path = options.png_temp_path + str(ObjectId()) + '.png'
    wmf2png_cmd = "%s %s %s" % (xmf2png, xmf_path, png_path)
    os.system(wmf2png_cmd)
    raise Return(png_path)


def open_xmf_file(bucket, xmf_path):
    try:
        ext = re.findall('\.\wmf', xmf_path)[0]
        local_xmf_path = options.xmf_temp_path + str(ObjectId()) + '.' + ext
        with open(local_xmf_path, 'wb') as fi:
            content = open_oss(bucket, xmf_path).read()
            fi.write(content)
            return local_xmf_path
    except Exception as e:
        logging.info('open xmf file error, err_info:{}, xmf_path:{}'.format(str(e), xmf_path))
        return ''


def save_png_file(bucket, local_png_path):
    with open(local_png_path, 'rb') as fi:
        content = fi.read()
    file_path = save_oss(bucket, "img", content, ext="png")
    return file_path

