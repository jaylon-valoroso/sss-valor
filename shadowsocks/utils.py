#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2015 clowwindy
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys
import os
import logging


#def valor_logging(msg):
#    logging.basicConfig(level=logging.INFO,
#                        format='%(filename)s %(lineno)d %(funcName)s %(message)s')
#    logging.info(msg)


def encode(s):
    result = '\n'
    index = 1
    for c in s:
        v = hex(ord(c)).replace('0x', '')
        if len(v) == 1:
            v = '0' + v
        result += v
        if index % 16 == 0:
            result += '\n'
        elif index % 1 == 0:
            result += ' '
        index += 1
    return result


def decode(s):
    s = s.replace(' ', '')
    s = s.replace('\n', '')
    result = ''
    index = 1
    cc = ''
    for c in s:
        cc += c
        if index % 2 == 0:
            result += chr(int(cc, 16))
            cc = ''
        index += 1
    return result

