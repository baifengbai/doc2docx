#!/usr/bin/env python
# encoding: utf-8

import hashlib
import hmac
import binascii
from tornado.options import options
from util.escape import json_encode


def get_sign(args):
    # targs = [(k, v) for k, v in args.items()]
    # targs = sorted(targs)
    # s = ""
    # for i, tp in enumerate(targs):
    #     if i > 0:
    #         s += "&"
    #     s += "%s=%s" % (tp[0], tp[1])
    s = args_encode(args)
    sign = hmac.new(options.cancer_secrect, s, digestmod=hashlib.sha256).digest()
    sign = binascii.hexlify(sign)
    return sign


def args_encode(args):
    targs = [(k, v) for k, v in args.items()]
    targs = sorted(targs)
    s = ""
    for i, tp in enumerate(targs):
        if i > 0:
            s += "&"

        if type(tp[1]) == str or type(tp[1]) == unicode:
            vs = tp[1]
        elif type(tp[1]) == list:
            vs = json_encode(tp[1])
        elif type(tp[1]) == dict:
            vs = args_encode(tp[1])
        else:
            # TODO MORE TYPES
            vs = ""
        s += "%s=%s" % (tp[0], vs)
    return s
