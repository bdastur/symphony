#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
Helper:
The module provides APIs for performing the
build, deploy, configure operations for symphony.

'''

import os
import yaml
import jinja2
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
        self.template_path = None
        self.normalized_data = None
        self.operation = operobj['operation']

        self.slog = logger.Logger(name="Helper")

        if operobj['operation'] == "build":
            self.valid = self.__populate_build_operation(operobj)

        self.slog.logger.info("Symphony Helper: Initialized")

    def __normalize_parsed_configuration(self):
        '''
        The API goes through the parsed environment and cluster
        configuration, and forms a normalized configuration which is used
        to render the template.

        Users can specify certain parameters at various levels in their
        configuration files. Here is the priority with which we will
        normalize the user variables.

        Going from high to low, as to where a variable is defined:

        1. Instance level variable
        2. Cluster level variable
        3. Environment level variable
        4. Default. (applicable only in some cases)

        To give an example. An environment file can define a 'vpc_id', however
        if the same variable is defined under cluster config or instance,
        then that will take precedence.
        '''
        required_fields = ['private_key_loc',
                           'public_key_loc',
                           'subnets',
                           'security_groups']
        default = {}
        default['region'] = "us-east-1"
        default['cloud_type'] = "aws"
        default['public_key_loc'] = ".ssh/symphonykey.pub"
        default['cluster_size'] = 1
        default['instance_type'] = "t2.micro"

        data = {}
        data['region'] = self.parsed_config.get('region',
                                                default['region'])
        data['cloud_type'] = self.parsed_env.get('type',
                                                 default['cloud_type'])
        data['credentials_file'] = \
            self.parsed_config.get('credentials_file',
                                   self.parsed_env.get('credentials_file',
                                                       None))
        data['profile_name'] = \
            self.parsed_config.get('profile_name',
                                   self.parsed_env.get('profile_name',
                                                       None))
        data['cluster_name'] = self.parsed_config.get('name', 'symphcluster')
        data['cluster_size'] = self.parsed_config.get('cluster_size',
                                                      default['cluster_size'])
        data['instance_type'] = self.parsed_config.get('instance_type',
                                                       default['instance_type'])

        data['public_key_loc'] = \
            self.parsed_config.get('public_key_loc',
                                   self.parsed_env.get('public_key_loc',
                                                       None))
        data['private_key_loc'] = \
            self.parsed_config.get('private_key_loc',
                                   self.parsed_env.get('private_key_loc',
                                                       None))
        data['subnets'] = \
            self.parsed_config.get('subnets',
                                   self.parsed_env.get('subnets',
                                                       None))
        data['security_groups'] = \
            self.parsed_config.get('security_groups',
                                   self.parsed_env.get('security_groups',
                                                       None))
        data['amis'] = \
            self.parsed_config.get('amis',
                                   self.parsed_env.get('amis',
                                                       None))

        data['tags'] = \
            self.parsed_config.get('tags',
                                   self.parsed_env.get('tags',
                                                       None))

        return data

    def __populate_build_operation(self, operobj):
        '''
        Populate build operation
        '''

        # Read the user input (cluster config file, staging loc,
        # environment path)
        self.slog.logger.info("Helper: Build operation populate")
        try:
            self.cluster_config = operobj['config']
            self.tf_staging = operobj['staging']
            self.env_path = operobj['environment']
            self.template_path = operobj['template']
        except KeyError as keyerror:
            self.slog.logger.error("Key not found [%s]", keyerror)
            return False

        # Parse the cluster config.
        self.parsed_config = \
            self.parse_cluster_configuation(self.cluster_config)
        if self.parsed_config is None:
            self.slog.logger.error("Failed to parse [%s]",
                                   self.cluster_config)
            return False
        self.slog.logger.debug("Parsed config: [%s]", self.parsed_config)

        # Parse the environment file.
        self.parsed_env = \
            self.parse_environment_configuration(self.env_path)
        if self.parsed_env is None:
            self.slog.logger.error("Failed to parse [%s]",
                                   self.env_path)
            return False
        self.slog.logger.debug("Parsed env: [%s]", self.parsed_env)

        return True

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

    def perform_operation(self):
        '''
        Perform the build, deploy, configure, destroy or list operation.
        '''
        if self.operation is None:
            self.slog.logger.error("Operation not set. Cannot perform task")
            return

        # Normalize our parsed configuration.
        self.normalized_data = self.__normalize_parsed_configuration()

        if self.operation == "build":
            # Build Operation.
            print "Build operation"
            if not os.path.exists(self.template_path) or \
                    not os.path.isdir(self.template_path):
                self.slog.logger.error("Invalid path to templates [%s]",
                                       self.template_path)
                return

            try:
                cluster_template = \
                    self.parsed_config['cluster_template']
            except KeyError:
                self.slog.logger.error(
                    "No field 'cluster_template' found cluster config")
                return

            print "cluster template: ", cluster_template

            cloud_type = self.normalized_data['cloud_type']
            template_path = os.path.join(self.template_path,
                                         cloud_type)
            template_filename = cluster_template + ".j2"
            template_file = os.path.join(template_path,
                                         cluster_template) + ".j2"

            try:
                template_fp = open(template_file, "r")
            except IOError as ioerror:
                self.slog.logger.error("Failed to open %s [%s]",
                                       template_fp, ioerror)
                return

            rendered_data = self.render_jinja2_template(
                template_filename,
                template_path,
                self.normalized_data)
            print "rendered data: ", rendered_data
            self.build_tf_cluster_staging_directory(rendered_data,
                                                    self.tf_staging)


    def render_jinja2_template(self, templatefile, searchpath, obj):
        '''
        Render a jinja2 template and return the rendered string
        '''
        rendered_data = None
        template_loader = jinja2.FileSystemLoader(searchpath=searchpath)
        env = jinja2.Environment(loader=template_loader,
                                 trim_blocks=False,
                                 lstrip_blocks=False)
        template = env.get_template(templatefile)
        rendered_data = template.render(obj)

        return rendered_data

    def build_tf_cluster_staging_directory(self,
                                           rendered_data,
                                           userenv_dir):
        '''
        Create a new terraform staging folder. Generate a terraform
        definition file based on the rendered template
        '''
        print "BRD: tf staging dir: ", userenv_dir
        if not os.path.exists(userenv_dir) or \
                not os.path.isdir(userenv_dir):
            self.slog.logger.info("Invalid staging directory %s",
                                  userenv_dir)
            os.mkdir(userenv_dir)

        # Generate a subdirectory based on the cluster name and
        # environment name.

        subdir_name = self.parsed_config['name'] + "_" + \
            self.parsed_config['environment']

        subdir_path = os.path.join(userenv_dir, subdir_name)
        self.tf_cluster_staging = subdir_path

        if not os.path.exists(subdir_path):
            self.slog.logger.info("%s Does not exist. Creating it",
                                  subdir_path)
            os.mkdir(subdir_path)

        tf_filename = os.path.join(subdir_path, "main.tf")

        tf_fp = open(tf_filename, "w")
        tf_fp.write(rendered_data)
        tf_fp.close()

        self.slog.logger.info("Build cluster staging: Successful")
















