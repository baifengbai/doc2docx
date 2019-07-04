#!/usr/bin/env python
# encoding=utf-8

import sys
import os
import logging

import oss2
from tornado.httpserver import HTTPServer
from tornado.web import Application
from tornado.ioloop import IOLoop
from tornado.options import options, parse_command_line, parse_config_file
from pymongo import MongoClient
from redis import StrictRedis

import routes
import settings
from util.common import install_tornado_shutdown_handler
from util.base_handler import Subject
from util.message_queue import RabbitMQProducer
from app_define import ALL_SUPPORT_SUBJECTS

reload(sys)
sys.setdefaultencoding('utf-8')
del sys.setdefaultencoding
del sys

MYSQL_PING = 10 * 60 * 1000  # 毫秒级


class YWeb(object):
    def __init__(self, **more_settings):
        settings.define_app_options()
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(filename)s %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            )
        parse_command_line(final=False)
        self_dir_path = os.path.abspath(os.path.dirname(__file__))
        if options.debug:
            conf_file_path = os.path.join(self_dir_path, 'server.conf')
        else:
            conf_file_path = os.path.join(self_dir_path, 'prod.conf')
        if os.path.exists(conf_file_path):
            parse_config_file(conf_file_path, final=False)
        parse_command_line(final=True)

        rds = None

        # self.jyeoo_admin_db = subject_db_client['jyeoo_admin']
        self.subjects = {}
        self.default_subject = ALL_SUPPORT_SUBJECTS[0]

        logging.info("Connecting to redis %s ...", options.redis_url)
        self.redis = StrictRedis.from_url(options.redis_url, db=options.redis_db,
                                          socket_timeout=5.0)
        self.redis.exists("dumb_key_test_connectivity")  # force to connect
        logging.info("Redis connected. Seems good.")

        the_routes = routes.get_main_route()
        the_settings = {
            'debug': options.debug,
            'cookie_secret': options.cookie_secret,
            'xsrf_cookies': False,
            # 'mysql_db': self.setup_subject_mysql_db(),
            # 'static_path': u'/static/',
            # 'static_handler_class': SmartStaticFileHandler,
            'oss_bucket': self.setup_oss_bucket(),
            'subjects': self.subjects,
            'default_subject': self.default_subject,
            'redis': self.redis,
        }
        the_settings.update(more_settings)
        # routes = get_routes()
        self.app = Application(the_routes, **the_settings)

    def load_subject_conf(self, subject):
        self_dir_path = os.path.abspath(os.path.dirname(__file__))
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

    def run(self):
        logging.info('Running at port %s in %s mode'
                     % (options.port, 'debug' if options.debug else 'production'))
        server = HTTPServer(self.app, xheaders=True)
        server.listen(options.port)
        # PeriodicCallback(self.ping_mysql_db, MYSQL_PING).start()
        install_tornado_shutdown_handler(IOLoop.instance(), server)
        logging.info('Good to go!')

        IOLoop.instance().start()
        logging.info('Exiting...waiting for backgroundparse_command_line(final=True) jobs done...')
        logging.info('Done. Bye.')


if __name__ == "__main__":
    y_server = YWeb()
    y_server.run()
