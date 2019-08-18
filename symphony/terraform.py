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
        command =["terraform", operation]
        get_plugins = kwargs.get("get_plugins", True)
        lock = kwargs.get("lock", True)

        if operation == "init":
            if not get_plugins:
                command.append("-get-plugins=false")

            if not lock:
                command.append("-lock=false")

        return command

    def terraform_init(self, staging_dir, **kwargs):
        ''' Handle Terraform init '''
        self.slog.logger.info("Executing terraform init")
        backend = kwargs.get('backend', False)
        plugin_dir = kwargs.get('plugin_dir', None)
        get_plugins = kwargs.get('get_plugins', True)
        init_cmd = self.generate_terraform_command("init", **kwargs)
        ret, stdout, stderr = self.cmdobj.execute_run(init_cmd, cwd=staging_dir)
        if ret != 0:
            print("Failed to execute terraform init")
        self.slog.logger.debug("Stdout: %s, Stderr: %s", stdout, stderr)
        return ret, stdout, stderr





