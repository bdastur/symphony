#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Unit tests for All symphony modules.
'''

import unittest
import utils.symphony_logger as logger
import symphony.tfparser as tfparser


class TFParserUt(unittest.TestCase):
    def test_parser_init_invalid(self):
        print "Test TFParser Initialization"
        cluster_dir = "/foobar"
        parser = tfparser.TFParser(cluster_dir, slogger=None)
        self.failUnless(parser.tfobject is None)

    def test_parser_init_valid(self):
        print "Test TFParser valid"
        cluster_dir = "./testdata/env1"
        parser = tfparser.TFParser(cluster_dir, slogger=None)
        self.failUnless(parser.tfobject is not None)
        print parser.tfobject

    def test_parser_get_all_resource_types(self):
        print "Test api for resource types"
        cluster_dir = "./testdata/env1"
        parser = tfparser.TFParser(cluster_dir, slogger=None)
        self.failUnless(parser.tfobject is not None)
        restypes = parser.parser_get_all_resource_types()
        print "Resource types: ", restypes



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




