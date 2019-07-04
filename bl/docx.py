from win32com import client as wc
from bson import ObjectId
from tornado.options import options
from util.oss_file_util import save_oss, open_oss

from tornado.httpclient import AsyncHTTPClient
from tornado.gen import coroutine
from tornado.gen import Return


@coroutine
def doc2docx(doc_path):
    w = wc.DispatchEx('Word.Application')
    # w = wc.DispatchEx('Word.Application')
    # doc = w.Documents.Open("E:\\Jupyter\\s.doc")
    doc = w.Documents.Open(doc_path)
    docx_path = options.docx_temp_path + str(ObjectId()) + '.docx'
    doc.SaveAs(docx_path, 16)
    raise Return(docx_path)


def open_doc_file(bucket, oss_file_path):
    doc_path = options.docx_temp_path + str(ObjectId()) + '.doc'
    with open(doc_path, 'wb') as fi:
        content = open_oss(bucket, oss_file_path).read()
        fi.write(content)
    return doc_path


def save_docx_file(bucket, local_docx_path):
    with open(local_docx_path, 'rb') as fi:
        content = fi.read()
    file_path = save_oss(bucket, "docx", content, ext="docx")
    return file_path
