#!/usr/bin/env python
# encoding: utf-8
import sys
import codecs
import os
import PyPDF2

from util.oss_file_util import open_oss

reload(sys)
sys.setdefaultencoding('utf-8')
del sys.setdefaultencoding
del sys


def merge_pdf(file_name, pdf_path):
    """
    将part2-5的pdf拼接
    :param file_name:
    :param pdf_path:
    :return:
    """
    # 建立一个装pdf文件的数组
    files = list()
    # 遍历该目录下的所有文件
    for filename in os.listdir(pdf_path):
        # 如果是以.pdf结尾的文件，则追加到数组中
        if filename.endswith(".pdf"):
            files.append(filename)

        # 以数字进行排序（数组中的排列顺序默认是以ASCII码排序，当以数字进行排序时会不成功）
        newfiles = sorted(files, key=lambda d: int(d.split(".pdf")[0]))

        # 进入该目录
        os.chdir(pdf_path)
        # 生成一个空白的PDF文件
        pdfwriter = PyPDF2.PdfFileWriter()
        for item in newfiles:
            pdfreader = PyPDF2.PdfFileReader(open(item, "rb"))
            for page in range(pdfreader.numPages):
                #  #将打开的pdf文件内容一页一页的复制到新建的空白pdf里
                pdfwriter.addPage(pdfreader.getPage(page))

                # 生成all.pdf文件
                with codecs.open(file_name, "wb") as f:
                    # 将复制的内容全部写入all.pdf文件中
                    pdfwriter.write(f)


def download_ie_pdf_by_dict(bucket, pdf_dict, dir_path):
    """
    按照pdf_dict从oss上下载pdf文件
    :param bucket:
    :param pdf_dict:
    :param dir_path:
    :return:
    """
    del pdf_dict['name']
    for part in pdf_dict:
        q_file_path = dir_path + 'question/' + '1' + part + '.pdf'
        with open(q_file_path, 'w') as fi:
            content = open_oss(bucket, pdf_dict[part]['q']).read()
            fi.write(content)
        a_file_path = dir_path + 'answer/' + '2' + part + '.pdf'
        with open(a_file_path, 'w') as fi:
            content = open_oss(bucket, pdf_dict[part]['a']).read()
            fi.write(content)
