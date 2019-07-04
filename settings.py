#!/usr/bin/env python
# encoding: utf-8

import logging
from tornado.options import define


def define_app_options():
    define('debug', default=True)
    define('log_level', default=logging.INFO)
    define('cookie_secret', default='dzwOrPqGdgOwBqyVdzwOrPqGdgOwBqyVdzwOrPqGdgOwBqyV')
    define('port', default=8080)

    define('types', default=[])

    define('replica_set', default='')
    define('w_value', default=0)
    define('wtimeout', default=5000)

    define('oss_access_id', default='LTAIVDL7MzrhpspZ'),
    define('oss_access_key', default='dLkT1LRxmASCVt2IJ6DmaFVkePdhPl'),
    define('oss_endpoint', 'http://oss-cn-beijing.aliyuncs.com')
    define('oss_name', '17zy-oto-export')
    define('oss_url_pref', default='')
    define('oss_tex_path', default='/latex/')
    define('oss_pdf_path', default='/pdf/')

    define('doc_temp_path', default='C://temp/doc/')
    define('docx_temp_path', default='C://temp/docx/')
    define('xmf_temp_path', default='C://temp/wmf/')
    define('png_temp_path', default='C://temp/png/')
    define('xmf2png', default='C://ImageMagick-7.0.8-Q16/magick')
    define('redis_url', default='redis://10.6.0.137:6444')
    define('redis_db', default=0)
