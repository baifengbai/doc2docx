#!/usr/bin/env python
# encoding: utf-8

from tornado.gen import coroutine
from util.base_handler import BaseHandler
from bl.docx import doc2docx, open_doc_file, save_docx_file
from util.redis_tool import push_to_cache, check_cache


class DocxHandler(BaseHandler):
    @coroutine
    def get(self):
        doc_path = self.get_argument('file_name', '')
        has_rec = check_cache(self.redis, doc_path)
        if has_rec:
            docx_path = self.redis.get(doc_path)
            self.write({'docx_path': docx_path})
        else:
            local_doc_path = open_doc_file(self.oss_bucket, doc_path)
            local_docx_path = ''
            if doc_path:
                local_docx_path = yield doc2docx(local_doc_path)
            docx_path = save_docx_file(self.oss_bucket, local_docx_path)
            if docx_path:
                push_to_cache(self.redis, doc_path, docx_path)
            self.write({'docx_path': docx_path})

