#!/usr/bin/env python
# encoding: utf-8


def get(site_root):
    routes = [
        (r'', 'controller.test.FirstHandler'),
    ]
    routes = [(site_root + route[0], ) + route[1:] for route in routes]
    return routes


def get_main_route():
    routes = [
        (r'/', 'controller.test.FirstHandler'),
        (r'/doc2docx', 'controller.docx.DocxHandler'),
        (r'/xmf2png', 'controller.xmf.xmf2pngHandler')
    ]
    return routes
