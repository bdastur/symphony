#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Handle Terraforrm operations
'''
import os
import utils.symphony_logger as logger

class Terraform(object):
    '''
    Terraform handlerself
    '''
    def __init__(self, tf_staging_dir, slogger=None):
        print("Terraform class init")
        if slogger is None:
            self.slog = logger.Logger(name="Terraform")
        else:
            self.slog = slogger

        if tf_staging_dir is None:
            self.slog.logger.error("Terraform staging path cannot be none")
            return
        if not os.path.exists(tf_staging_dir) and not os.path.isdir(tf_staging_dir):
            self.slog.logger.error("Staging dir %s, should be a dir", tf_staging_dir)
            return

        self.slog.logger.info("Terraform module init!")



