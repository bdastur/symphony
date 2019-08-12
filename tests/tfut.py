#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Unit tests for terraform utils
'''

import shutil
import os
import unittest
import symphony.terraform as terraform

class TfUt(unittest.TestCase):
    '''Test Terraform operations'''
    TF_STAGING_DIR = "/tmp/symphdist"

    def setUp(self):
        print("Test setup!")
        tf_test_dir = "./testdata/tfdir"
        staging_dir = "/tmp/symphdist"
        # Set staging with sample terraform template
        shutil.rmtree(staging_dir)
        shutil.copytree(tf_test_dir, staging_dir)

    def test_basic_tfutil(self):
        tfut = terraform.Terraform(TfUt.TF_STAGING_DIR)

