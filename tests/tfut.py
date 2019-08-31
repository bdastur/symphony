#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Unit tests for terraform utils
'''

import shutil
import os
import unittest
import sys
import symphony.command as command
import symphony.terraform as terraform
import symphony.renderer as renderer


class TfUt(unittest.TestCase):
    '''Test Terraform operations'''
    TF_STAGING_DIR = "/tmp/symphdist"

    def setUp(self):
        print("Test setup!")
        tf_test_dir = "./testdata/tfdir"
        staging_dir = "/tmp/symphdist"
        # Set staging with sample terraform template
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir)
        shutil.copytree(tf_test_dir, staging_dir)

        # Copy sample scripts to /tmp
        scripts = {
            "./testdata/sample_pass.sh": "/tmp/sample_pass.sh",
            "./testdata/sample_fail.sh": "/tmp/sample_fail.sh"
        }
        for script in scripts.keys():
            print("Copying %s", script)
            shutil.copy(script, scripts[script])

    def normalize_string(self, string):
        newstr = string.replace(" ", "")
        newstr = newstr.replace("\n", "")
        return newstr

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

        ret, stdout, stderr = tfut.terraform_init(TfUt.TF_STAGING_DIR,
            tf_dir="/tmp/test")
        self.assertEqual(ret, 0, msg="Expected return 0")

    def test_terraform_init_fail(self):
        ''' test terraform_init '''
        tfut = terraform.Terraform(TfUt.TF_STAGING_DIR)
        self.assertEqual(tfut.initialized, True)

        ret, _, _ = tfut.terraform_init(TfUt.TF_STAGING_DIR,
            tf_dir="/tmp/test", get_plugins=False)
        self.assertEqual(ret, 1, msg="Expected return 1")

    def test_terraform_plan(self):
        ''' test terraform_plan '''
        tfut = terraform.Terraform(TfUt.TF_STAGING_DIR)
        self.assertEqual(tfut.initialized, True)

        # Terraform init
        ret, stdout, stderr = tfut.terraform_init(TfUt.TF_STAGING_DIR,
            tf_dir="/tmp/test")
        self.assertEqual(ret, 0, msg="Expected return 0")

        # Terraform plan
        ret, stdout, stderr = tfut.terraform_plan(TfUt.TF_STAGING_DIR,
            tf_dir="/tmp/test")
        self.assertEqual(ret, 0, msg="Expected return 0")
        print("stdout: ", stdout)
        print("stderr: ", stderr)

    def test_terraform_apply(self):
        ''' test terraform_apply '''
        tfut = terraform.Terraform(TfUt.TF_STAGING_DIR)
        self.assertEqual(tfut.initialized, True)

        # Terraform init
        ret, stdout, stderr = tfut.terraform_init(TfUt.TF_STAGING_DIR,
            tf_dir="/tmp/test")
        self.assertEqual(ret, 0, msg="Expected return 0")

        # Terraform plan
        ret, stdout, stderr = tfut.terraform_plan(TfUt.TF_STAGING_DIR,
            tf_dir="/tmp/test")
        self.assertEqual(ret, 0, msg="Expected return 0")
        print("stdout: ", stdout)
        print("stderr: ", stderr)

         # Terraform apply
        ret, stdout, stderr = tfut.terraform_apply(TfUt.TF_STAGING_DIR,
            tf_dir="/tmp/test")
        self.assertEqual(ret, 0, msg="Expected return 0")
        print("stdout: ", stdout)
        print("stderr: ", stderr)

    def test_render_j2basic(self):
        pass
        template = "templates/aws/provider.tf.j2"
        searchpath = "../"
        expected_output = '''
        #------------------------------------
        # AWS Provider definition

        provider "aws" {
          region = "us-west-2"
          shared_credentials_file = "/Users/home"
          profile = ""
        }

        '''
        expected_output = self.normalize_string(expected_output)
        obj = {
            'region': 'us-west-2',
            'profile': 'default',
            'credentials_file': "/Users/home"
        }
        rendered_data = renderer.render_j2_template(template, searchpath, obj)
        rendered_data = self.normalize_string(rendered_data)
        self.assertEqual(expected_output, rendered_data,
                         msg="Expected did not match actual")



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
        cmdobj = command.Command()
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
        cmdobj = command.Command()
        ret, out, err = cmdobj.execute_run(["/tmp/sample_pass.sh"])
        self.assertTrue(ret == 0, msg="Expected 0 ")

        ret, out, err = cmdobj.execute_run(["ls", "-l"], cwd="/tmp")
        self.assertEqual(ret, 0, msg="Expected value not returned")

        ret, out, err = cmdobj.execute_run(["./sample_fail.sh"], cwd="/tmp")
        self.assertEqual(ret, 255, msg="Expected value not returned")

        ret, out, err = cmdobj.execute_run(["foobar"])
        self.assertEqual(ret, 2, msg="Expected value not returned")





