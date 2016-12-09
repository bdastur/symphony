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
import json
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
        elif operobj['operation'] == "list":
            self.valid = self.__populate_list_operation(operobj)

        self.slog.logger.info("Symphony Helper: Initialized")

    def normalize_parsed_configuration(self):
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

        data = {}

        data['cluster_name'] = self.parsed_config.get(
            'name', default['cluster_name'])

        data['cloud_type'] = self.parsed_env.get('type',
                                                 default['cloud_type'])
        data['credentials_file'] = \
            self.parsed_config.get('credentials_file',
                                   default['credentials_file'])
        data['profile_name'] = \
            self.parsed_config.get('profile_name',
                                   default['profile_name'])
        data['region'] = self.parsed_env.get(
            'region', default['region'])

        data['public_key_loc'] = \
            self.parsed_config.get('public_key_loc',
                                   default['public_key_loc'])

        data['private_key_loc'] = \
            self.parsed_config.get('private_key_loc',
                                   default['private_key_loc'])

        data['subnets'] = \
            self.parsed_config.get('subnets',
                                   self.parsed_env.get('subnets',
                                                       None))
        data['security_groups'] = \
            self.parsed_config.get('subnets',
                                   self.parsed_env.get('security_groups',
                                                       None))

        data['connection_info'] = self.parsed_config.get('connection_info')


        data['clusters'] = {}
        for cluster in self.parsed_config['clusters'].keys():
            data['clusters'][cluster] = {}
            cobj = self.parsed_config['clusters'][cluster]

            data['clusters'][cluster]['region'] = self.parsed_env.get(
                'region',
                default['region'])
            data['clusters'][cluster]['cluster_name'] = \
                cobj.get('name', cluster)
            data['clusters'][cluster]['cluster_size'] = \
                cobj.get('cluster_size', default['cluster_size'])
            data['clusters'][cluster]['instance_type'] = \
                cobj.get('instance_type', default['instance_type'])
            data['clusters'][cluster]['public_key_loc'] = \
                cobj.get('public_key_loc',
                         self.parsed_config.get('public_key_loc',
                                                default['public_key_loc']))
            data['clusters'][cluster]['private_key_loc'] = \
                cobj.get('private_key_loc',
                         self.parsed_config.get('private_key_loc',
                                                default['private_key_loc']))
            data['clusters'][cluster]['cluster_template'] = \
                cobj.get('cluster_template',
                         self.parsed_config.get('cluster_template',
                                                None))

            data['clusters'][cluster]['tags'] = \
                cobj.get('tags',  self.parsed_config.get('tags', None))

            data['clusters'][cluster]['amis'] = \
                cobj.get('amis',
                         self.parsed_config.get(
                             'amis',
                             self.parsed_env.get('amis', None)))

            data['clusters'][cluster]['subnets'] = self.parsed_config.get(
                    'subnets',
                    self.parsed_env.get('subnets', None))

            data['clusters'][cluster]['security_groups'] = \
                self.parsed_config.get('security_groups',
                                       self.parsed_env.get(
                                           'security_groups', None))

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

        # Validate staging dir.
        if os.path.exists(self.tf_staging) and \
                not os.path.isdir(self.tf_staging):
            self.slog.logger.error("Staging path cannot be a file")
            return False

        # Validate template path.
        if not os.path.exists(self.template_path) or \
                not os.path.isdir(self.template_path):
            self.slog.logger.error("Ivalid template path [%s]",
                                   self.template_path)
            return False

        return True

    def __populate_configure_operation(self, operobj):
        '''
        Populate config operation
        '''

        # Read the user input (cluster config file and staging location)
        self.slog.logger.info("Helper: configure operation populate")
        try:
            self.cluster_config = operobj['config']
            self.env_path = operobj['environment']
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

        # Parse the environment file.
        self.parsed_env = \
            self.parse_environment_configuration(self.env_path)
        if self.parsed_env is None:
            self.slog.logger.error("Failed to parse [%s]",
                                   self.env_path)
            return False
        self.slog.logger.debug("Parsed env: [%s]", self.parsed_env)

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

    def __populate_list_operation(self, operobj):
        '''
        Populate list operation
        '''
        print "List: ", operobj

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
            return 1

        if self.operation == "build":
            # Build Operation.

            # Normalize our parsed configuration.
            self.normalized_data = self.normalize_parsed_configuration()
            print "Build operation"
            if not os.path.exists(self.template_path) or \
                    not os.path.isdir(self.template_path):
                self.slog.logger.error("Invalid path to templates [%s]",
                                       self.template_path)
                return 1

            # Create the staging directory
            ret = self.build_tf_cluster_staging_directory(self.tf_staging)
            if ret != 0:
                return ret

            # Render the common template.
            self.render_symphony_template("common",
                                          "common",
                                          self.tf_cluster_staging,
                                          self.normalized_data)

            # Render templates for cluster specific.
            for cluster in self.normalized_data['clusters'].keys():
                obj = self.normalized_data['clusters'][cluster]
                templatename = obj['cluster_template']
                tf_filename = obj['cluster_name']
                obj['init_script'] = "./scripts/%s.sh" % tf_filename
                self.render_symphony_template(templatename,
                                              tf_filename,
                                              self.tf_cluster_staging,
                                              obj)

                # Now that we have taken care of rendering the template,
                # check if user has provided init script and set that as well.
                self.generate_init_script(tf_filename,
                                          self.tf_cluster_staging,
                                          obj['user_init_script'])
        elif self.operation == "deploy":
            print "Deploy operation"
            self.deploy_terraform_environment(self.tf_staging)
        elif self.operation == "configure":
            print "Configure operation"
            self.normalized_data = self.normalize_parsed_configuration()
            self.configure_terraform_environment(self.tf_staging)
        elif self.operation == "destroy":
            print "Destroy operation"
            self.destroy_terraform_environment(self.tf_staging)
        elif self.operation == "list":
            self.display_terraform_environment(self.tf_staging)

    def generate_init_script(self,
                             tf_filename,
                             tf_cluster_staging,
                             user_init_script):
        '''
        Generate the init script.
        '''
        scripts_dir = os.path.join(tf_cluster_staging, "scripts")
        scripts_filename = "%s.sh" % tf_filename

        scripts_file = os.path.join(scripts_dir, scripts_filename)
        if not os.path.exists(scripts_dir):
            self.slog.logger.error("[%s] scripts dir does not exist",
                                   scripts_dir)
            os.mkdir(scripts_dir)

        # Read our common.sh script.
        fp = open("./scripts/common.sh", "r")
        common_data = fp.read()
        fp.close()

        if user_init_script is not None:
            if not os.path.exists(user_init_script):
                self.slog.logger.error("Invalid path to init script [%s]",
                                       user_init_script)
            else:
                fp = open(user_init_script, "r")
                userdata = fp.read()
                fp.close()

                for line in userdata.splitlines():
                    if line.startswith("#!"):
                        continue
                    fp.close()
                    common_data += "\n" + line

        fp = open(scripts_file, "w")
        fp.write(common_data)
        fp.close()
















    def render_symphony_template(self,
                                 template_name,
                                 tf_filename,
                                 staging_dir,
                                 normalized_data):
        '''
        Render the template
        '''
        cloud_type = self.normalized_data['cloud_type']
        template_path = os.path.join(self.template_path,
                                     cloud_type)
        template_filename = template_name + ".j2"
        template_file_path = os.path.join(template_path,
                                          template_name) + ".j2"
        try:
            template_fp = open(template_file_path, "r")
        except IOError as ioerr:
            self.slog.logger.error("Failed to open template file %s [%s]",
                                   template_path, ioerr)
            return 1
        template_fp.close()

        rendered_data = self.render_jinja2_template(template_filename,
                                                    template_path,
                                                    normalized_data)

        print "Rendered data: \n", rendered_data

        tf_filename = tf_filename + ".tf"

        tf_filepath = os.path.join(staging_dir, tf_filename)
        tf_fp = open(tf_filepath, "w")
        tf_fp.write(rendered_data)
        tf_fp.close()

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

    def build_tf_cluster_staging_directory(self, userenv_dir):
        '''
        Create a new terraform staging folder. Generate a terraform
        definition file based on the rendered template
        '''
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

        # Create a subdirectory within the staging folder for
        # keeping scripts.
        scripts_dir = os.path.join(subdir_path, "scripts")
        if not os.path.exists(scripts_dir):
            self.slog.logger.info("%s Does not exist. Creating it",
                                  scripts_dir)
            os.mkdir(scripts_dir)


        self.slog.logger.info("Build cluster staging: Successful")
        return 0

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

    def display_terraform_environment(self, cluster_staging_dir):
        '''
        Given the path to staging dir, walk through the directory
        and display the resources created for each environment
        '''
        print "BRD: Display tf env: ", cluster_staging_dir

        parserobj = tfparser.TFParser(cluster_staging_dir)
        parserobj.terraform_display_environments()

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
        for cluster in self.normalized_data['clusters'].keys():
            services = self.normalized_data['clusters'][cluster]['services']
            print "%s: Services: %s " % (cluster, services)

            default_hosts = \
                self.normalized_data['clusters'][cluster]['cluster_name']

            for service in services.keys():
                kwargs = {}
                print "service: ", service
                print services[service]
                default_service_dir = os.path.join("./services", service)
                kwargs['username'] = \
                    self.normalized_data['connection_info']['username']
                kwargs['private_key'] = self.normalized_data['private_key_loc']
                kwargs['tf_staging'] = cluster_staging_dir
                kwargs['use_private_ip'] = \
                    self.normalized_data['connection_info'].get(
                        'use_private_ip',
                        "True")

                if services[service] is not None:
                    service_dir = services[service].get(
                        'service_dir', default_service_dir)
                    kwargs['hosts'] = services[service].get(
                        'hosts', default_hosts)
                    kwargs['service_vars'] = services[service]
                else:
                    service_dir = default_service_dir
                    kwargs['hosts'] = default_hosts
                    kwargs['service_vars'] = {}


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
        print "playbook [%s, %s] hosts: %s" % \
            (playbook_path, playbook_name, kwargs['hosts'])

        tf_dynamic_inventory = "../../../tf_ansible/terraform.py"

        # Set Ansible Options.
        extra_vars = "username=%s hosts=%s" % \
            (kwargs['username'], kwargs['hosts'])
        private_key_option = "--private-key=%s" % kwargs['private_key']

        # Set the Additional variables in cluster info.
        service_vars = kwargs['service_vars']
        service_vars = json.dumps(service_vars)

        # Set environment variables.
        os.environ['TERRAFORM_STATE_ROOT'] = kwargs['tf_staging']
        os.environ['ANSIBLE_HOST_KEY_CHECKING'] = "False"
        os.environ['USE_PRIVATE_IP'] = kwargs['use_private_ip']

        ansible_cmd = ["ansible-playbook", "-i", tf_dynamic_inventory,
                       playbook_name, "-e", extra_vars,
                       "-e", service_vars,
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




