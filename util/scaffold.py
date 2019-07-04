#!/usr/bin/env python
# encoding: utf-8

import sys
import time
import logging
import os

import oss2
from tornado.options import options, parse_command_line, parse_config_file
from pymongo import MongoClient
import settings
from base_handler import Subject
from app_define import ALL_SUPPORT_SUBJECTS
from util.message_queue import RabbitMQProducer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Scaffold(object):
    def __init__(self):
        self.subject_name = ""
        self.setup()

    def set_subject_name(self, subject_name):
        self.subject_name = subject_name

    def setup(self):
        settings.define_app_options()
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(filename)s %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            )
        parse_command_line(final=False)
        # current_dir = os.path.dirname(os.path.abspath(__file__))
        # current_dir = os.path.split(os.path.realpath(sys.argv[0]))[0]
        current_dir = sys.path[0]
        logging.info('Running in %s mode' % ('debug' if options.debug else 'production'))
        if options.debug:
            conf_file_path = os.path.join(current_dir, 'server.conf')
        else:
            conf_file_path = os.path.join(current_dir, 'prod.conf')
        if os.path.exists(conf_file_path):
            parse_config_file(conf_file_path, final=False)

        parse_command_line(final=True)
        self.subjects = {}
        self.oss_bucket = self.setup_oss_bucket()
        for subject_name in ALL_SUPPORT_SUBJECTS:
            self.load_subject_conf(subject_name)
            subject = Subject(None, subject_name, options.types)
            # 脚本暂时不需要motor
            self.subjects[subject_name] = subject

        # self.db = self.setup_db()
        # self.userdb = self.setup_userdb()

    def load_subject_conf(self, subject):
        # self_dir_path = os.getcwd()
        self_dir_path = sys.path[0]
        subject_file_path = os.path.join(self_dir_path, 'conf/', '%s.conf' % subject)
        if os.path.exists(subject_file_path):
            parse_config_file(subject_file_path, final=False)
        else:
            logging.warning("%s conf file not found", subject)
            assert False

    def setup_oss_bucket(self):
        auth = oss2.Auth(options.oss_access_id, options.oss_access_key)
        bucket = oss2.Bucket(auth, options.oss_endpoint, options.oss_name)
        return bucket

    def timeit(self, fn, *args, **kwargs):
        t1 = time.clock()
        ret = fn(*args, **kwargs)
        t2 = time.clock()
        return t2 - t1, ret

    def run(self, *args, **kwargs):
        return self.main(*args, **kwargs )

    def main(self, *args, **kwargs):
        # overwrite
        assert False

    @property
    def subject(self):
        return self.subjects[self.subject_name]

