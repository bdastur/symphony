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

class Command(object):
    '''
    Command Handlerself
    '''
    def __init__(self):
        self.slog = logger.Logger(name="Command")

    def execute_cmd(self, cmd, options={}, popen=False):
        cwd = options.get('cwd', None)
        env = options.get('env', None)
        if popen:
            cmdoutput = ""
            sproc = subprocess.Popen(cmd,
                                     env=env,
                                     cwd=cwd,
                                     shell=True,
                                     stdout=subprocess.PIPE)
            while True:
                nextline = sproc.stdout.readline()
                nextline = nextline.decode("utf-8")
                cmdoutput += nextline
                if nextline == '' and sproc.poll() is not None:
                    break

                sys.stdout.write(nextline)
                sys.stdout.flush()

            return 0, cmdoutput

        try:
            cmdoutput = subprocess.check_output(cmd,
                                                cwd=cwd,
                                                stderr=subprocess.STDOUT,
                                                shell=False,
                                                env=env)

        except subprocess.CalledProcessError as err:
            self.slog.logger.error("Failed to execut %s. Err %s",
                                   cmd, err)
            return 1, ""

        return 0, cmdoutput

    def execute(self, cmd, options={}):
        '''Execute command'''
        cwd = options.get('cwd', None)
        sproc = subprocess.Popen(cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            close_fds=True)
        while True:
            next_line = sproc.stdout.readline()
            next_line = next_line.decode("utf-8")
            if next_line == "" and sproc.poll() is not None:
                break

            sys.stdout.write(next_line)
            sys.stdout.flush()

        print(sproc.errors)
        sys.stdout.close()

    def execute_run(self, cmd, options={}):
        ''' Execute command'''
        cwd = options.get('cwd', None)
        env = options.get('env', None)
        self.slog.logger.debug("CMD: %s, option: %s",
            cmd, options)
        try:
            proc = subprocess.run(
                cmd,
                env=env, cwd=cwd,
                capture_output=True)
            stdout = proc.stdout.decode("utf-8")
            stderr = proc.stderr.decode("utf-8")
            return proc.returncode, stdout, stderr
        except FileNotFoundError as err:
            self.slog.logger.error("CMD: %s not found %s",
            cmd, err)
            return err.errno, "", err.__str__()



class Terraform(object):
    '''
    Terraform handlerself
    '''
    def __init__(self, tf_staging_dir, slogger=None):
        print("Terraform class init")
        self.initialized = False
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

    def terraform_init(self, **kwargs):
        ''' Handle Terraform init '''
        print("Terraform init: ", kwargs)





