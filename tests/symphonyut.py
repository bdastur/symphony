#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Unit tests for All symphony modules.
'''

import unittest
import utils.symphony_logger as logger


class SymphonyUt(unittest.TestCase):
    def test_basic(self):
        print "Test Basic"

    def test_logging_basic(self):
        print "Test logging utility"

        slog = logger.Logger(name="TestModule")
        self.failUnless(slog.logger is not None)

        slog.logger.info("This is an INFO message")
        slog.logger.error("This is an ERROR message")

        slog2 = logger.Logger(name="Another Module",
                              logfile="/tmp/anotherlog.log")

        slog2.logger.info("Another Log INFO MSG")

    def test_logging_newfile(self):
        print "Test Logging utility"
        slog = logger.Logger(name="NEWTEST",
                             logfile="/tmp/newlog.log")
        self.failUnless(slog.logger is not None)

        slog.logger.debug("Test logging newfile: DEBUG log")




