#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Handle Terraforrm operations
'''
import os
import sys
import asyncio
import subprocess
import utils.symphony_logger as logger
import symphony.command as command


class Terraform(object):
    '''
    Terraform handler
    '''
    def __init__(self, tf_staging_dir, slogger=None):
        print("Terraform class init")
        self.initialized = False
        self.cmdobj = command.Command()
        if slogger is None:
            self.slog = logger.Logger(name="Terraform")
        else:
            self.slog = slogger

        if tf_staging_dir is None:
            self.slog.logger.error("Terraform staging path cannot be none")
            return
        if not os.path.exists(tf_staging_dir) and \
            not os.path.isdir(tf_staging_dir):
            self.slog.logger.error("Staging dir %s, should be a dir", tf_staging_dir)
            return
        self.initialized = True

        self.slog.logger.info("Terraform module init!")

    def generate_terraform_command(self, operation, **kwargs):
        '''Build a command string'''
        command = ["terraform", operation]
        get_plugins = kwargs.get("get_plugins", True)
        lock = kwargs.get("lock", True)
        var_file = kwargs.get("var_file", None)
        auto_approve = kwargs.get("auto_approve", True)


        if operation == "init":
            if not get_plugins:
                command.append("-get-plugins=false")
            if not lock:
                command.append("-lock=false")
        elif operation == "plan":
            if var_file is not None:
                cmdoption = "-var-file=%s" % var_file
                command.append(cmdoption)
        elif operation == "apply":
            if auto_approve:
                command.append("-auto-approve")
            if var_file is not None:
                cmdoption = "-var-file=%s" % var_file
                command.append(cmdoption)

        return command

    def terraform_init(self, staging_dir, **kwargs):
        ''' Handle Terraform init '''
        self.slog.logger.info("Executing terraform init")
        init_cmd = self.generate_terraform_command("init", **kwargs)
        ret, stdout, stderr = self.cmdobj.execute_run(init_cmd, cwd=staging_dir)
        if ret != 0:
            print("Failed to execute terraform init")
        self.slog.logger.debug("Stdout: %s, Stderr: %s", stdout, stderr)
        return ret, stdout, stderr

    def terraform_plan(self, staging_dir, **kwargs):
        '''Handling terraform plan command'''
        self.slog.logger.info("Executing terraform plan")
        plan_cmd = self.generate_terraform_command("plan", **kwargs)
        print("Plan cmd: ", plan_cmd)
        ret, stdout, stderr = self.cmdobj.execute_run(plan_cmd, cwd=staging_dir)
        if ret != 0:
            self.slog.logger.error("Plan %s failed", plan_cmd)

        return ret, stdout, stderr

    def terraform_apply(self, staging_dir, **kwargs):
        '''Handling terraform apply command'''
        self.slog.logger.info("Executing terraform apply")
        apply_cmd = self.generate_terraform_command("apply", **kwargs)
        print("apply cmd: ", apply_cmd)
        ret, stdout, stderr = self.cmdobj.execute_run(apply_cmd, cwd=staging_dir)
        if ret != 0:
            self.slog.logger.error("apply %s failed", apply_cmd)

        return ret, stdout, stderr
