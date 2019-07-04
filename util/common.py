#!/usr/bin/env python
# encoding: utf-8

import logging
import time
import signal

import xlwt
import httpagentparser
from tornado.escape import url_escape

import re
MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 1
PAGE_SIZE_DEFAULT = 20
_INVALID_HTTP_HEADER_CHAR_RE = re.compile(br"[\x00-\x1f]")


def install_tornado_shutdown_handler(ioloop, server, logger=None):
    # see https://gist.github.com/mywaiting/4643396 for more detail
    if logger is None:
        import logging
        logger = logging

    def _sig_handler(sig, frame):
        logger.info("Signal %s received. Preparing to stop server.", sig)
        ioloop.add_callback(shutdown)

    def shutdown():
        logger.info("Stopping http server...")
        server.stop()
        logger.info("will shutdown in %s seconds", MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
        deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN

        def stop_loop():
            now = time.time()
            if now < deadline and (ioloop._callbacks or ioloop._timeouts):
                ioloop.add_timeout(now + 1, stop_loop)
                logger.debug("Waiting for callbacks and timesouts in IOLoop...")
            else:
                ioloop.stop()
                logger.info("Server is shutdown")
        stop_loop()

    signal.signal(signal.SIGTERM, _sig_handler)
    signal.signal(signal.SIGINT, _sig_handler)


def filter_unsafe_http_header_value(value):
    return _INVALID_HTTP_HEADER_CHAR_RE.sub(' ', value)


def force_browser_download_content(handler, fname):
    fname = filter_unsafe_http_header_value(fname)
    if not fname:
        fname = u'未命名'
    agent = httpagentparser.detect(handler.request.headers.get('User-Agent', u''))
    browser = agent.get('browser', None) if agent else None
    header_set = False
    escaped_fname = url_escape(fname, False)
    if browser:
        if browser.get('name', u'') == 'Microsoft Internet Explorer' and\
                browser.get('version', u'') in ('7.0', '8.0'):
            handler.set_header('Content-Disposition',
                               'attachment;filename={}'.format(escaped_fname))
            header_set = True
    if not header_set:
        handler.set_header('Content-Disposition',
                           'attachment;filename="{}";filename*=UTF-8\'\'{}'.format(
                               fname.encode('utf-8'), escaped_fname))


class Pager:
    def __init__(self, handler):
        self.page_count = 0
        self.page = handler.get_argument('page', 0, type_=int)
        self.page_size = handler.get_argument('pagesize', PAGE_SIZE_DEFAULT, type_=int)
        self.page_size = min(100, max(1, self.page_size))

    def paginate(self, cursor):
        cursor.limit(self.page_size)
        if self.page > 0:
            cursor.skip(self.page_size * self.page)
        self.page_count = self.count_page_num(cursor.count())
        return cursor

    def paged_response(self):
        return {
            'page': self.page,
            'pagecount': self.page_count,
            'pagesize': self.page_size
        }

    def count_page_num(self, total_count):
        res = total_count / self.page_size
        if total_count % self.page_size:
            res += 1
        return res


def iter_paper_item(paper):
    assert 'parts' in paper
    for i, part in enumerate(paper['parts']):
        for j, it in enumerate(part):
            yield (i, j), it


class TextWriter(object):
    def __init__(self, **kwargs):
        self.method = kwargs.get("method", "cmd")       # cmd, file, logging
        self.with_linenum = kwargs.get("with_linenum", False)
        self.file_name = kwargs.get("file_name", "new_file.txt")
        self.caches = []

    def set_method(self, s):
        self.method = s

    def set_linenum(self, f):
        self.with_linenum = f

    def set_file_name(self, f):
        self.file_name = f

    def write(self, s):
        idx = len(self.caches) - 1
        if idx < 0:
            idx += 1
            self.caches.append("")
        self.caches[idx] += s

    def writeln(self, s):
        self.caches.append(s)

    def write_pretty(self, s):
        def _combined(val):
            """
            判断val是不是dict或者list
            :param val:
            :return: none
            """
            if isinstance(val, list) or isinstance(val, dict) or isinstance(val, tuple):
                return True
            return False

        def _write_pretty(val, write_caches, deep=0):
            """
            格式化输出，用来调试
            :param show_mode:
            :param val:
            :param deep:
            :return: None
            """
            if isinstance(val, dict):
                for r in val:
                    if _combined(val[r]):
                        write_caches.append(u"%s%s:" % ('\t' * deep, r))
                        _write_pretty(val[r], write_caches, deep + 1)
                    else:
                        write_caches.append(u"%s%s:%s" % ("\t" * deep, r, val[r]))

            elif isinstance(val, list) or isinstance(val, tuple):
                for i, r in enumerate(val):
                    if _combined(val[i]):
                        write_caches.append(u"%s%d:" % ("\t" * deep, i))
                        _write_pretty(val[i], write_caches, deep + 1)
                    else:
                        write_caches.append(u"%s%d:%s" % ("\t" * deep, i, val[i]))
            else:
                write_caches.append(u"%s:%s" % ("\t" * deep, val))

        _caches = []
        _write_pretty(s, _caches)
        self.caches.extend(_caches)

    def clear(self):
        self.caches = []

    def commit(self):
        if self.method == "file":
            with open(self.file_name, "w") as f:
                for out_str in self._datas():
                    f.write("%s\n" % out_str)
        else:
            for out_str in self._datas():
                if self.method == "cmd":
                    print out_str
                elif self.method == "logging":
                    logging.info(out_str)

    def _datas(self):
        for i, s in enumerate(self.caches):
            if self.with_linenum:
                yield u"%d\t|\t%s" % (i+1, s)
            else:
                yield u"%s" % s


class ExcelWriter(object):
    def __init__(self, file_name="new_excel.xls"):
        self.file_name = file_name
        self.data = xlwt.Workbook()
        self.cur_sheet = None
        self.sheets = []
        self.caches = []

    def new_sheet(self, sheet_name=None):
        if not sheet_name:
            sheet_name = "sheet%d" % len(self.sheets)
        self.cur_sheet = self.data.add_sheet(sheet_name)
        self.sheets.append(self.cur_sheet)

    def write(self, s):
        pass

    def writeln(self, row):
        if not self.cur_sheet:
            self.new_sheet()
        self.caches.append(row)

    def show(self):
        for row in self.caches:
            for s in row:
                print s, '\t',
            print

    def commit(self):
        for i, row in enumerate(self.caches):
            for j, s in enumerate(row):
                self.cur_sheet.write(i, j, s)
        self.cur_sheet = None

    def save_file(self):
        self.data.save(self.file_name)


CN_NUM = [u'十', u'一', u'二', u'三', u'四', u'五', u'六', u'七', u'八', u'九']


def num2cn(x):
    assert 1000 > x > 0
    if x < 10:
        return CN_NUM[x]
    else:
        if x < 20:
            if x > 10:
                return CN_NUM[0] + CN_NUM[x % 10]
            else:
                return CN_NUM[0]
        elif x < 100:
            # return CN_NUM[x / 10] + CN_NUM[0] + CN_NUM[x % 10]
            res = CN_NUM[x / 10] + CN_NUM[0]
            if x % 10:
                res += CN_NUM[x % 10]
            return res
        elif x > 100:
            t = x / 10 % 10
            mid = u'零' if not t else u"%s十" % CN_NUM[t]
            # return CN_NUM[x / 100] + u'百' + mid + CN_NUM[x % 10]
            res = CN_NUM[x / 100] + u'百' + mid
            if x % 10:
                res += CN_NUM[x % 10]
            return res


def origin_item_scan(item, ref_item):
    """
    判断一个item答题卡试题与原试题结构是否一致以及是否为主观题
    :param item: 题目信息
    :return: coordinate_flag: 答题卡试题与原试题结构是否一致
    :return: subjective_flag: 是否为主观题
    """
    subjective_flag = True
    coordinate_flag = True
    qs_count = 0
    if len(item['data']['qs']) != len(ref_item['data']['qs']):
        # 当结构不一致时，不需要判断是否为主观，直接返回即可
        return False, subjective_flag
    for qs in item['data']['qs']:
        if qs['opts']:
            subjective_flag = False
        if 'qs' in qs:
            if 'qs' not in ref_item['data']['qs'][qs_count]:
                return False, subjective_flag
            if len(qs['qs']) != len(ref_item['data']['qs'][qs_count]['qs']):
                return False, subjective_flag
            for qss in qs['qs']:
                if qss['opts']:
                    subjective_flag = False
        elif 'qs' in ref_item['data']['qs'][qs_count]:
            return False, subjective_flag
        qs_count += 1
    return coordinate_flag, subjective_flag


def replace_item_content(item, ref_item):
    """
    替换答题卡试题内容
    :param item:答题卡试题
    :param ref_item: 原题
    :return: 替换过内容的试题
    """
    item['data']['type'] = ref_item['data']['type']
    item['data']['stem'] = ref_item['data']['stem']
    for i in range(len(ref_item['data']['qs'])):
        item['data']['qs'][i]['desc'] = \
            ref_item['data']['qs'][i]['desc']
        if 'qs' in ref_item['data']['qs'][i]:
            for j in range(len(ref_item['data']['qs'][i]['qs'])):
                item['data']['qs'][i]['qs'][j]['desc'] = \
                    ref_item['data']['qs'][i]['qs'][j]['desc']
    return item


def replace_item_ans(item, ref_item):
    """
    替换答题卡答案
    :param item:答题卡试题
    :param ref_item: 原题
    :return: 替换过答案的试题
    """
    for i in range(len(ref_item['data']['qs'])):
        item['data']['qs'][i]['exp'] = \
            ref_item['data']['qs'][i]['exp']
        item['data']['qs'][i]['ans'] = \
            ref_item['data']['qs'][i]['ans']
        if 'qs' in ref_item['data']['qs'][i]:
            for j in range(len(ref_item['data']['qs'][i]['qs'])):
                item['data']['qs'][i]['qs'][j]['ans'] = \
                    ref_item['data']['qs'][i]['qs'][j]['ans']
                item['data']['qs'][i]['qs'][j]['exp'] = \
                    ref_item['data']['qs'][i]['qs'][j]['exp']
    return item


subject2cn = {
    'math': u'数学',
    'physics': u'物理',
    'chemistry': u'化学',
    'biology': u'生物',
    'chinese': u'语文',
    'english': u'英语',
    'politics': u'政治',
    'history': u'历史',
    'geography': u'地理',
    'science': u'科学',
}

grade2cn = {
    6: u'六年级',
    7: u'七年级',
    8: u'八年级',
    9: u'九年级',
    10: u'十年级',
    11: u'高一',
    12: u'高二',
    13: u'高三',
}
