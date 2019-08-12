#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import yaml
import utils.symphony_logger as logger


class ConfigParser(object):
    def __init__(self):
        self.slog = logger.Logger(name="Helper")
        self.slog.logger.info("Symphony Config Parser: Initialized")

    def parse_cluster_configuration(self, config_file):
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

    def parse_environment_configuration(self, env_path, env_name):
        '''
        Parse the environment configuration file.
        '''
        # Check for valid path.
        if not os.path.exists(env_path) or \
                not os.path.isdir(env_path):
            self.slog.logger.error("Invalid environment path [%s]",
                                   env_path)
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

    def normalize_parsed_configuration(self,
                                       parsed_config,
                                       parsed_env):
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
        config_required_fields = ['private_key_loc',
                                  'public_key_loc',
                                  'credentials_file',
                                  'profile_name']

        default = {}
        default['region'] = "us-east-1"
        default['cloud_type'] = "aws"
        default['public_key_loc'] = ".ssh/symphonykey.pub"
        default['private_key_loc'] = ".ssh/symphonykey"
        default['credentials_file'] = "~/.aws/credentials"
        default['profile_name'] = "default"
        default['cluster_size'] = 1
        default['instance_type'] = "t2.micro"
        default['cluster_name'] = "symphony-default-cluster"
        default['network_type'] = "private"

        data = {}

        data['cluster_name'] = parsed_config.get(
            'name', default['cluster_name'])

        data['cloud_type'] = parsed_env.get('type',
                                            default['cloud_type'])
        data['credentials_file'] = \
            parsed_config.get('credentials_file',
                              default['credentials_file'])
        data['profile_name'] = \
            parsed_config.get('profile_name',
                              default['profile_name'])
        data['region'] = parsed_env.get(
            'region', default['region'])

        data['public_key_loc'] = \
            parsed_config.get('public_key_loc',
                              default['public_key_loc'])

        data['private_key_loc'] = \
            parsed_config.get('private_key_loc',
                              default['private_key_loc'])

        data['subnets'] = \
            parsed_config.get('subnets',
                              parsed_env.get('subnets',
                                             None))
        data['security_groups'] = \
            parsed_config.get('subnets',
                              parsed_env.get('security_groups',
                                             None))

        data['connection_info'] = parsed_config.get('connection_info')

        data['clusters'] = {}
        for cluster in parsed_config['clusters'].keys():
            data['clusters'][cluster] = {}
            cobj = parsed_config['clusters'][cluster]

            data['clusters'][cluster]['region'] = parsed_env.get(
                'region',
                default['region'])
            data['clusters'][cluster]['cluster_name'] = \
                cobj.get('name', cluster)
            data['clusters'][cluster]['cluster_size'] = \
                cobj.get('cluster_size', default['cluster_size'])
            data['clusters'][cluster]['instance_type'] = \
                cobj.get('instance_type', default['instance_type'])
            data['clusters'][cluster]['network_type'] = \
                cobj.get('network_type', default['network_type'])
            data['clusters'][cluster]['public_key_loc'] = \
                cobj.get('public_key_loc',
                         parsed_config.get('public_key_loc',
                                           default['public_key_loc']))

            data['clusters'][cluster]['vpc_id'] = \
                parsed_config.get('vpc',
                                  parsed_env.get('vpc',
                                                 None))

            data['clusters'][cluster]['private_key_loc'] = \
                cobj.get('private_key_loc',
                         parsed_config.get('private_key_loc',
                                           default['private_key_loc']))
            data['clusters'][cluster]['cluster_template'] = \
                cobj.get('cluster_template',
                         parsed_config.get('cluster_template',
                                           None))

            data['clusters'][cluster]['tags'] = \
                cobj.get('tags', parsed_config.get('tags', None))

            data['clusters'][cluster]['amis'] = \
                cobj.get('amis',
                         parsed_config.get(
                             'amis',
                             parsed_env.get('amis', None)))

            data['clusters'][cluster]['subnets'] = parsed_config.get(
                'subnets',
                parsed_env.get('subnets', None))

            # parse and save preconfigured security groups and
            # user provided security groups.
            data['clusters'][cluster]['security_groups'] = \
                parsed_config.get('security_groups',
                                  parsed_env.get(
                                      'security_groups', None))

            # Check to see if user specific security group rules.
            if cobj.get('user_security_groups', None) is not None:
                user_sg_info = cobj.get('user_security_groups')
                data['clusters'][cluster]['user_security_groups'] = \
                    user_sg_info

            # Check to see if loadbalancer config is specified.
            if cobj.get('loadbalancer', None) is not None:
                lb_info = cobj.get('loadbalancer')
                data['clusters'][cluster]['loadbalancer'] = lb_info

            data['clusters'][cluster]['user_init_script'] = \
                cobj.get('init_script', None)

            data['clusters'][cluster]['services'] = \
                cobj.get('services',
                         None)

        # Validate normalized data.
        for item in config_required_fields:
            if item not in data.keys():
                self.slog.logger.error("%s not found in normalized data",
                                       item)

        return data

