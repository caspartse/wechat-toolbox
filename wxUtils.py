#!/usr/bin/env python
# -*- coding:utf-8 -*
from time import time
from random import randint
from PIL import Image
from StringIO import StringIO


def genTimeStamp(length):
    t = '%d' % (time() * 10 ** (length - 10))
    return t


def genRandint(length):
    r = randint(10 ** (length - 1), 10 ** length - 1)
    return r


def displayImage(content):
    Image.open(StringIO(content)).show()
    return

if __name__ == '__main__':
    pass
