#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
Helper:
The module provides APIs for performing the
build, deploy, configure operations for symphony.

'''

import os
import yaml
import utils.symphony_logger as logger


class Helper(object):
    def __init__(self, operobj):
        '''
        Initialize the Helper.

        :type operation: Dictionary
        :param operation: An object that defines the operations
        '''
        self.cluster_config = None
        self.tf_staging = None
        self.env_path = None
        self.parsed_config = None
        self.parsed_env = None

        self.slog = logger.Logger(name="Helper")

        if operobj['operation'] == "build":
            self.__populate_build_operation(operobj)

        self.slog.logger.info("Symphony Helper: Initialized")

    def __populate_build_operation(self, operobj):
        '''
        Populate build operation
        '''
        self.slog.logger.info("Helper: Build operation populate")
        try:
            self.cluster_config = operobj['config']
            self.tf_staging = operobj['staging']
            self.env_path = operobj['environment']
        except KeyError as keyerror:
            self.slog.logger.error("Key not found [%s]", keyerror)
            return None

        self.parsed_config = \
            self.parse_cluster_configuation(self.cluster_config)
        if self.parsed_config is None:
            self.slog.logger.error("Failed to parse [%s]",
                                   self.cluster_config)
            return
        self.slog.logger.debug("Parsed config: [%s]", self.parsed_config)

        self.parsed_env = \
            self.parse_environment_configuration(self.env_path)
        if self.parsed_env is None:
            self.slog.logger.error("Failed to parse [%s]",
                                   self.env_path)
            return
        self.slog.logger.debug("Parsed env: [%s]", self.parsed_env)

    def parse_cluster_configuation(self, config_file):
        '''
        Parse the cluster configuration file.
        '''
        try:
            parsed_data = yaml.safe_load(config_file)
        except yaml.YAMLError as yamlerror:
            self.slog.logger.error("Failed to parse cluster config [%s] [%s]",
                                   config_file, yamlerror)
            return None

        return parsed_data

    def parse_environment_configuration(self, env_path):
        '''
        Parse the environment configuration file.
        '''
        # Check for valid path.
        if not os.path.exists(env_path) or \
                not os.path.isdir(env_path):
            self.slog.logger.error("Invalid environment path [%s]",
                                   env_path)
            return None

        try:
            env_name = self.parsed_config['environment']
        except KeyError:
            self.slog.logger.error(
                "Parsed config does not have `environment` key")
            return None

        envfile = os.path.join(env_path, env_name) + ".yaml"
        if not os.path.exists(envfile):
            self.slog.logger.error("[%s] Environment file not found",
                                   envfile)
            return None

        try:
            envfp = open(envfile, "r")
        except IOError as ioerror:
            self.slog.logger.error("Failed to open %s [%s]",
                                   envfile, ioerror)
            return None

        try:
            parsed_data = yaml.safe_load(envfp)
        except yaml.YAMLError as yamlerror:
            self.slog.logger.error("Failed to parse env config [%s] [%s]",
                                   envfile, yamlerror)
            return None

        return parsed_data







