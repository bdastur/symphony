#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
Helper:
The module provides APIs for performing the
build, deploy, configure operations for symphony.

'''

import sys
import os
import time
import subprocess
import socket
import paramiko
import yaml
import jinja2
import utils.symphony_logger as logger
try:
    import symphony.tfparser as tfparser
except ImportError:
    import tfparser


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
        elif operobj['operation'] == "deploy":
            self.valid = self.__populate_deploy_operation(operobj)
        elif operobj['operation'] == "configure":
            self.valid = self.__populate_configure_operation(operobj)
        elif operobj['operation'] == "destroy":
            self.valid = self.__populate_destroy_operation(operobj)

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
            self.parse_cluster_configuration(self.cluster_config)
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

    def __populate_configure_operation(self, operobj):
        '''
        Populate config operation
        '''

        # Read the user input (cluster config file and staging location)
        self.slog.logger.info("Helper: configure operation populate")
        try:
            self.cluster_config = operobj['config']
            self.tf_staging = operobj['staging']
        except KeyError as keyerror:
            self.slog.logger.error("Key not found [%s]", keyerror)
            return False

        # Parse the cluster config.
        self.parsed_config = \
            self.parse_cluster_configuration(self.cluster_config)
        if self.parsed_config is None:
            self.slog.logger.error("Failed to parse [%s]",
                                   self.cluster_config)

        return True

    def __populate_deploy_operation(self, operobj):
        '''
        Populate deploy operation
        '''
        self.slog.logger.info("Helper: Deploy operation populate")

        # Read the user input (staging location)
        try:
            self.tf_staging = operobj['staging']
        except KeyError as keyerror:
            self.slog.logger.error("Key not found [%s]", keyerror)
            return False

        if not os.path.exists(self.tf_staging) or \
                not os.path.isdir(self.tf_staging):
            self.slog.logger.error("Invalid staging location %s",
                                   self.tf_staging)
            return False

        return True

    def __populate_destroy_operation(self, operobj):
        '''
        Populate destroy operation params
        '''
        self.slog.logger.info("Helper: Destroy operation populate")

        # Read the user input(staging location)
        try:
            self.tf_staging = operobj['staging']
        except KeyError as keyerror:
            self.slog.logger.error("Key not found [%s]", keyerror)
            return False

        if not os.path.exists(self.tf_staging) or \
                not os.path.isdir(self.tf_staging):
            self.slog.logger.error("Invalid staging location: %s",
                                   self.tf_staging)
            return False

        return True

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

        if self.operation == "build":
            # Build Operation.

            # Normalize our parsed configuration.
            self.normalized_data = self.__normalize_parsed_configuration()
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
        elif self.operation == "deploy":
            print "Deploy operation"
            self.deploy_terraform_environment(self.tf_staging)
        elif self.operation == "configure":
            print "Configure operation"
            self.configure_terraform_environment(self.tf_staging)
        elif self.operation == "destroy":
            print "Destroy operation"
            self.destroy_terraform_environment(self.tf_staging)

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

    def deploy_terraform_environment(self, cluster_staging_dir):
        '''
        Deploy the terraform environment
        '''
        self.slog.logger.info("Cluster Staging Dir: %s",
                              cluster_staging_dir)

        if not os.path.exists(cluster_staging_dir):
            self.slog.logger.error("Staging Dir %s does not exist",
                                   cluster_staging_dir)
            return

        # Terraform plan
        tf_plan_cmd = ["terraform", "plan"]
        sproc = subprocess.Popen(tf_plan_cmd,
                                 cwd=cluster_staging_dir,
                                 stdout=subprocess.PIPE)

        while True:
            nextline = sproc.stdout.readline()
            if nextline == "" and sproc.poll() is not None:
                break

            sys.stdout.write(nextline)
            sys.stdout.flush()

        # Terraform apply.
        tf_apply_cmd = ["terraform", "apply"]
        sproc = subprocess.Popen(tf_apply_cmd,
                                 cwd=cluster_staging_dir,
                                 stdout=subprocess.PIPE)

        while True:
            nextline = sproc.stdout.readline()
            if nextline == "" and sproc.poll() is not None:
                break

            sys.stdout.write(nextline)
            sys.stdout.flush()

    def destroy_terraform_environment(self, cluster_staging_dir):
        '''
        Given the path to the staging dir, cleanup the environment
        '''
        self.slog.logger.info("Cluster staging dir: %s", cluster_staging_dir)

        tf_statefile = os.path.join(cluster_staging_dir, "terraform.tfstate")
        if not os.path.exists(tf_statefile):
            self.slog.logger.error("tf state file %s does not exist",
                                   tf_statefile)
            sys.exit()

        # Confirm destroy command.
        confirm_msg = "Do you really want to destroy?\n"
        confirm_msg_fmt = logger.stringc(confirm_msg, "bold")

        confirm_msg_fmt += "   Terraform will delete all your" \
            " mapped infrastructure.\n" \
            "   There is no undo. Only 'yes' will be accepted to confirm.\n"
        print confirm_msg_fmt

        option = raw_input("Enter a value:")
        if option != "yes":
            print "Only \"yes\" will delete"
            return

        # Terraform destroy
        tf_destroy_cmd = ["terraform", "destroy", "-force"]
        sproc = subprocess.Popen(tf_destroy_cmd,
                                 cwd=cluster_staging_dir,
                                 stdout=subprocess.PIPE)
        while True:
            nextline = sproc.stdout.readline()
            if nextline == "" and sproc.poll() is not None:
                break

            sys.stdout.write(nextline)
            sys.stdout.flush()

    def configure_terraform_environment(self, cluster_staging_dir):
        '''
        Configure the terraform environment
        '''
        if not os.path.exists(cluster_staging_dir) or \
                not os.path.isdir(cluster_staging_dir):
            self.slog.logger.error("Staging dir %s does not exist",
                                   cluster_staging_dir)
            return

        print "Configure"
        ssh_failure = self.wait_for_ssh_connectivity(
            cluster_staging_dir,
            self.parsed_config['connection_info']['username'],
            self.parsed_config['private_key_loc'])
        if not ssh_failure:
            print "Failed to connect to hosts."
            return

        # Now that we are able to reach all hosts.
        # We can start configuring services.
        for service in self.parsed_config['services'].keys():
            kwargs = {}
            print "service: ", service
            print self.parsed_config['services'][service]
            default_service_dir = os.path.join("./services", service)
            default_hosts = "all"
            kwargs['username'] = \
                self.parsed_config['connection_info']['username']
            kwargs['private_key'] = self.parsed_config['private_key_loc']
            kwargs['tf_staging'] = cluster_staging_dir
            kwargs['use_private_ip'] = \
                self.parsed_config['connection_info'].get('use_private_ip',
                                                          "True")

            if self.parsed_config['services'][service] is not None:
                service_dir = self.parsed_config['services'][service].get(
                    'service_dir', default_service_dir)
                kwargs['hosts'] = self.parsed_config['services'][service].get(
                    'hosts', default_hosts)
            else:
                service_dir = default_service_dir
                kwargs['hosts'] = default_hosts


            default_playbook_name = "site.yaml"
            self.execute_ansible_playbook(service_dir,
                                          default_playbook_name,
                                          **kwargs)



    def wait_for_ssh_connectivity(self,
                                  cluster_staging_dir,
                                  username,
                                  private_key_loc):
        '''
        Wait for SSH Connectivity to the hosts.
        '''
        print "privkey loc: ", private_key_loc

        parseobj = tfparser.TFParser(cluster_staging_dir)
        instinfo = parseobj.parser_get_aws_instance_info()

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh_hosts = []
        for env in instinfo.keys():
            for reskey, resval in instinfo[env].items():
                ssh_hosts.append(resval['private_ip'])

        retry_count = 0
        while retry_count < 10:
            no_ssh_failure = True
            for ssh_host in ssh_hosts:
                try:
                    print "Try connection to [%s: %d]" % \
                        (ssh_host, retry_count)
                    ssh.connect(ssh_host,
                                username=username,
                                key_filename=private_key_loc,
                                timeout=5,
                                banner_timeout=5)
                    print "Connection Success: [%s: %d]" % \
                        (ssh_host, retry_count)
                except socket.error as sockerr:
                    print "Socket error: ", sockerr
                    no_ssh_failure = False
                except paramiko.ssh_exception.SSHException as paramikoerr:
                    print "Paramiko ssh error ", paramikoerr
                    no_ssh_failure = False

            if no_ssh_failure:
                break

            retry_count += 1
            time.sleep(10)

        return no_ssh_failure

    def execute_ansible_playbook(self,
                                 playbook_path,
                                 playbook_name,
                                 **kwargs):
        '''
        Execute the ansible playbook
        '''
        print "playbook [%s, %s]" % (playbook_path, playbook_name)

        tf_dynamic_inventory = "../../../tf_ansible/terraform.py"

        # Set Ansible Options.
        extra_vars = "username=%s hosts=%s" % \
            (kwargs['username'], kwargs['hosts'])
        private_key_option = "--private-key=%s" % kwargs['private_key']

        # Set environment variables.
        os.environ['TERRAFORM_STATE_ROOT'] = kwargs['tf_staging']
        os.environ['ANSIBLE_HOST_KEY_CHECKING'] = "False"
        os.environ['USE_PRIVATE_IP'] = kwargs['use_private_ip']

        ansible_cmd = ["ansible-playbook", "-i", tf_dynamic_inventory,
                       playbook_name, "-e", extra_vars,
                       private_key_option]

        sproc = subprocess.Popen(ansible_cmd,
                                 cwd=playbook_path,
                                 stdout=subprocess.PIPE)
        while True:
            nextline = sproc.stdout.readline()
            if nextline == "" and sproc.poll() is not None:
                break

            sys.stdout.write(nextline)
            sys.stdout.flush()




