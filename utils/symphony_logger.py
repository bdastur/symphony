#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Logging Facility
'''

import logging


class Logger(object):
    '''
    Logger Class.
    '''
    def __init__(self,
                 name=__name__,
                 logfile="/tmp/symphony.log"):
        '''
        Symphony logger:

        :type name: String
        :param name: Name of module (used when logging a message)
        '''
        formatstr = '[%(asctime)s %(levelname)5s' \
            ' %(process)d %(name)s]: %(message)s'
        logging.basicConfig(
            level=logging.DEBUG,
            format=formatstr,
            datefmt='%m-%d-%y %H:%M',
            filename=logfile,
            filemode='a')

        # Defined a stream handler.
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '[%(asctime)s %(levelname)5s %(name)s]:  %(message)s',
            datefmt="%m-%d-%y %H:%M")

        console.setFormatter(formatter)

        # Add handler to root logger
        logging.getLogger(name).addHandler(console)

        self.logger = logging.getLogger(name)



# --- begin "pretty"
#
# pretty - A miniature library that provides a Python print and stdout
# wrapper that makes colored terminal text easier to use (e.g. without
# having to mess around with ANSI escape sequences). This code is public
# domain - there is no license except that you must leave this header.
#
# Copyright (C) 2008 Brian Nez <thedude at bri1 dot com>
#
# http://nezzen.net/2008/06/23/colored-text-in-python-using-ansi-escape-sequences/

codeCodes = {
    'black':     '0;30', 'bright gray':    '0;37',
    'blue':      '0;34', 'white':          '1;37',
    'green':     '0;32', 'bright blue':    '1;34',
    'cyan':      '0;36', 'bright green':   '1;32',
    'red':       '0;31', 'bright cyan':    '1;36',
    'purple':    '0;35', 'bright red':     '1;31',
    'yellow':    '0;33', 'bright purple':  '1;35',
    'dark gray': '1;30', 'bright yellow':  '1;33',
    'normal':    '0'
}


def stringc(text, color):
    """String in color."""
    return "\033[" + codeCodes[color] + "m" + text + "\033[0m"

# --- end "pretty"


