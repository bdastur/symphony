#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Unit tests for terraform utils
'''

import shutil
import os
import unittest
import sys
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

        # Copy sample scripts to /tmp
        scripts = {
            "./testdata/sample_pass.sh": "/tmp/sample_pass.sh",
            "./testdata/sample_fail.sh": "/tmp/sample_fail.sh"
        }
        for script in scripts.keys():
            print("Copy %s", script)
            shutil.copy(script, scripts[script])


    def test_terraform_module_init(self):
        invalid_staging = "/tmp/nonexistent"
        tfut = terraform.Terraform(invalid_staging)
        self.assertEqual(tfut.initialized, False)

        tfut = terraform.Terraform(None)
        self.assertEqual(tfut.initialized, False)

        tfut = terraform.Terraform(TfUt.TF_STAGING_DIR)
        self.assertEqual(tfut.initialized, True)

    def test_terraform_init(self):
        ''' test terraform_init '''
        tfut = terraform.Terraform(TfUt.TF_STAGING_DIR)
        self.assertEqual(tfut.initialized, True)

        tfut.terraform_init(tf_dir="/tmp/test")


class CommandUt(unittest.TestCase):
    '''Test Command class'''
    def setUp(self):
        # Copy sample scripts to /tmp
        scripts = {
            "./testdata/sample_pass.sh": "/tmp/sample_pass.sh",
            "./testdata/sample_fail.sh": "/tmp/sample_fail.sh"
        }
        for script in scripts:
            print("Copy ", script)
            shutil.copy(script, scripts[script])


    def test_command_execute(self):
        '''command run test '''
        cmdobj = terraform.Command()
        ret, out = cmdobj.execute_cmd("/tmp/sample_fail.sh")
        self.assertEqual(ret, 1)
        print(out)

        ret, out = cmdobj.execute_cmd("/tmp/sample_pass.sh")
        self.assertEqual(ret, 0)
        print(out)

        ret, out = cmdobj.execute_cmd("/tmp/sample_pass.sh", popen=True)
        self.assertEqual(ret, 0)
        print(out)

    def test_command_run(self):
        '''Command run test'''
        cmdobj = terraform.Command()
        ret, out, err = cmdobj.execute_run(["/tmp/sample_pass.sh"])
        self.assertTrue(ret == 0, msg="Expected 0 ")

        cmdoptions = {}
        cmdoptions['cwd'] = "/tmp"
        ret, out, err = cmdobj.execute_run(["ls", "-l"], options=cmdoptions)
        self.assertEqual(ret, 0, msg="Expected value not returned")

        ret, out, err = cmdobj.execute_run(["./sample_fail.sh"], options=cmdoptions)
        self.assertEqual(ret, 255, msg="Expected value not returned")

        ret, out, err = cmdobj.execute_run(["foobar"])
        self.assertEqual(ret, 2, msg="Expected value not returned")





