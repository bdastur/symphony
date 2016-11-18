#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Unit tests for All symphony modules.
'''

import unittest
import utils.symphony_logger as logger
import symphony.tfparser as tfparser
import symphony.helper as helper

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

    def test_build_operation_init_invalid_1(self):
        print "Helper Build operation init"
        obj = {}
        obj['operation'] = "build"
        obj['config'] = open("./testdata/clusters/invalid_cluster.yaml")
        obj['environment'] = "./testdata/environment/"
        obj['staging'] = "./teststaging"
        obj['skip_deploy'] = True
        obj['template'] = "../templates"



        print "Invalid cluster config --->"
        helperobj = helper.Helper(obj)
        self.failUnless(helperobj is not None)
        self.failUnless(helperobj.valid is False)
        obj['config'].close()

        obj['config'] = open("./testdata/clusters/rabbitmq_cluster.yaml")
        obj['environment'] = "./testdata/dummydir/"

        print "Invlaid environments dir path --->"
        helperobj = helper.Helper(obj)
        self.failUnless(helperobj is not None)
        self.failUnless(helperobj.valid is False)
        obj['config'].close()

        obj['config'] = open("./testdata/clusters/rabbitmq_cluster.yaml")
        obj['environment'] = "./testdata/environment"
        obj['staging'] = "/tmp/symphony.log"
        print "Invlaid staging path --->"
        helperobj = helper.Helper(obj)
        self.failUnless(helperobj is not None)
        self.failUnless(helperobj.valid is False)



