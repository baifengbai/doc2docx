#!/usr/bin/env python
# encoding: utf-8

from tornado.gen import coroutine
from util.base_handler import BaseHandler
from bl.xmf import open_xmf_file, xmf2png, save_png_file
from util.redis_tool import push_to_cache, check_cache


class xmf2pngHandler(BaseHandler):

    @coroutine
    def get(self):
        xmf_path = self.get_argument('file_name', '')
        has_rec = check_cache(self.redis, xmf_path)
        if has_rec:
            png_path = self.redis.get(xmf_path)
            self.write({'png_path': png_path})
        else:
            local_xmf_path = open_xmf_file(self.oss_bucket, xmf_path)
            if local_xmf_path:
                local_png_path = yield xmf2png(local_xmf_path)
                png_path = save_png_file(self.oss_bucket, local_png_path)
                push_to_cache(self.redis, xmf_path, png_path)
                self.write({'png_path': png_path})
            else:
                self.write({'png_path': '', 'message': 'can not open_xmf_file'})
