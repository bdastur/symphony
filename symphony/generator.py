#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Generator: The porgram reads a user input file
and builds the app environment.

'''

import sys
import os
import shutil
import json
import yaml
import argparse
import prettytable
import subprocess
import jinja2
import utils.symphony_logger as logger


class Generator(object):
    '''
    Read the user input file. Perform validations
    and provide APIs to access data.
    '''
    def __init__(self, namespace):
        self.slog = logger.Logger(name="Generator")
        if namespace.operation == "build":
            self.inputfilename = namespace.input.name
            self.parsed_input = self.__parse_userinput(namespace.input)
            if self.parsed_input is None:
                self.slog.logger.error("Parsing Failed for %s",
                                       self.inputfilename)
            else:
                self.slog.logger.info("Parsed %s successfull",
                                      self.inputfilename)
        elif namespace.operation == "listenv":
            self.list_environments(namespace.envdir)

    def __is_valid_userinput(self, parsed_data):
        required_valid_keys = ['template_root', 'cloud', 'working_dir']

        # Check for valid required keys in input file
        for validkey in required_valid_keys:
            if validkey not in parsed_data.keys():
                self.slog.logger.error("Key %s not present in %s",
                                       validkey, self.inputfilename)
                return False

        return True

    def __parse_userinput(self, inputfile):
        try:
            parsed_data = yaml.safe_load(inputfile)
        except yaml.YAMLError as yamlerr:
            self.slog.logger.error("Failed to parse %s [%s]",
                                   self.inputfilename, yamlerr)
            return None

        if not self.__is_valid_userinput(parsed_data):
            self.slog.logger.error("Inputfile Validation Failed")
            return None

        return parsed_data

    def render_templates(self, searchpath, templatefile, obj):
        '''
        Read and render jinja2 templates. Returns a rendered
        text
        '''
        template_loader = jinja2.FileSystemLoader(searchpath=searchpath)
        env = jinja2.Environment(loader=template_loader,
                                 trim_blocks=False,
                                 lstrip_blocks=False)
        template = env.get_template(templatefile)
        data = template.render(obj)

        print "Rendered data: ", data
        return data

    def render_template_inline(self, template_str, data):
        '''
        Read the template string and return the rendered output
        '''
        if template_str is None or len(template_str) == 0:
            self.slog.logger.error("Invalid template string")
            return None

        if data is None or len(data) == 0:
            self.slog.logger.error("Render data cannot be empty")
            return None

        try:
            template = jinja2.Template(template_str,
                                       trim_blocks=True,
                                       lstrip_blocks=True)
            rendered_str = template.render(data)
        except jinja2.exceptions.TemplateSyntaxError as j2error:
            self.slog.logger.error("J2 Error: [%s]", j2error)
            return None

        return rendered_str

    def render_terraform_file(self, tf_src, tf_dst):
        '''
        Read the source  file, and copy rendred data to dst.
        '''
        template_root = self.parsed_input['template_root']
        # Render environment.txt.
        try:
            fp = open(tf_src)
            template_str = fp.read()
        except IOError as ioerr:
            self.slog.logger.error("IOError: [%s]", ioerr)
            sys.exit()

        fp.close()

        # Prefill some variables.
        if self.parsed_input.get('keypair_module_source', None) is None:
            self.parsed_input['keypair_module_source'] = \
               os.path.join(template_root,
                            "tfmodules",
                            self.parsed_input['cloud']['type'].lower(),
                            "keypair")

        if self.parsed_input.get('sg_core_module_source', None) is None:
            self.parsed_input['sg_core_module_source'] = \
               os.path.join(template_root,
                            "tfmodules",
                            self.parsed_input['cloud']['type'].lower(),
                            "securitygroup", "core")

        if self.parsed_input.get('sg_http_module_source', None) is None:
            self.parsed_input['sg_http_module_source'] = \
               os.path.join(template_root,
                            "tfmodules",
                            self.parsed_input['cloud']['type'].lower(),
                            "securitygroup", "http")

        if self.parsed_input.get('ec2_instance_module_source', None) is None:
            self.parsed_input['ec2_instance_module_source'] = \
               os.path.join(template_root,
                            "tfmodules",
                            self.parsed_input['cloud']['type'].lower(),
                            "instance", "basic")

        if self.parsed_input.get('cloud_config_file', None) is None:
            self.parsed_input['cloud_config_file'] = "./cloud_config.sh"

        rendered_str = self.render_template_inline(template_str,
                                                   self.parsed_input)
        print "Rendered: ", rendered_str
        try:
            fp = open(tf_dst, 'w')
            fp.write(rendered_str)
        except IOError as ioerr:
            self.slog.logger.error("IOError writing rendered str [%s]",
                                   ioerr)
            sys.exit()

    def setup_environment_directory(self, template_root, working_dir):
        template_dir = os.path.join(template_root,
                                    "tf_templates",
                                    self.parsed_input['cloud']['type'].lower(),
                                    self.parsed_input['template_name'])

        if not os.path.exists(template_dir):
            self.slog.logger.error("[%s] template_dir path does not exist",
                                   template_dir)
            sys.exit()
        print "Template dir %s exists" % template_dir

        tf_common_dir = os.path.join(template_root,
                                     "tf_templates",
                                     self.parsed_input['cloud']['type'].lower(),
                                     "common")
        if not os.path.exists(tf_common_dir):
            self.slog.logger.error("[%s] template common dir does not exist",
                                   tf_common_dir)
            sys.exit()

        env_root = os.path.join(working_dir,
                                "environments")

        if not os.path.exists(env_root):
            os.mkdir(env_root)

        env_dir = os.path.join(env_root,
                               self.parsed_input['env_name'])

        if not os.path.exists(env_dir):
            os.mkdir(env_dir)

        # Copy the necessary files to working dir.
        main_src = os.path.join(template_dir, "main.tf")
        variables_src = os.path.join(tf_common_dir, "variables.tf")
        outputs_src = os.path.join(template_dir, "outputs.tf")
        environment_src = os.path.join(tf_common_dir, "environment.txt")
        cloudconfig_src = os.path.join(template_dir, "cloud_config.sh")

        main_dst = os.path.join(env_dir, "main.tf")
        variables_dst = os.path.join(env_dir, "variables.tf")
        outputs_dst = os.path.join(env_dir, "outputs.tf")
        environment_dst = os.path.join(env_dir, "environment.txt")
        cloudconfig_dst = os.path.join(env_dir, "cloud_config.sh")

        print "main: ", main_dst
        try:
            shutil.copyfile(variables_src, variables_dst)
            shutil.copyfile(outputs_src, outputs_dst)
            shutil.copy(cloudconfig_src, cloudconfig_dst)
        except IOError as ioerr:
            self.slog.logger.error("IOError: [%s]", ioerr)
            sys.exit()

        self.render_terraform_file(environment_src,
                                   environment_dst)
        self.render_terraform_file(main_src,
                                   main_dst)

    def run_terraform_commands(self, working_dir):
        '''
        Execute the terraform commands to build and generate the environment
        '''
        print "Run terraform commands"
        env_root = os.path.join(working_dir,
                                "environments")
        if not os.path.exists(env_root):
            sys.exit()

        env_dir = os.path.join(env_root,
                               self.parsed_input['env_name'])
        if not os.path.exists(env_dir):
            sys.exit()

        env_file = os.path.join(env_dir, "environment.txt")
        if not os.path.exists(env_file):
            sys.exit()

        # Terraform get all modules.
        tf_get_cmd = ["terraform", "get"]

        sproc = subprocess.Popen(tf_get_cmd,
                                 cwd=env_dir,
                                 stdout=subprocess.PIPE)
        while True:
            nextline = sproc.stdout.readline()
            if nextline == "" and sproc.poll() is not None:
                break

            sys.stdout.write(nextline)
            sys.stdout.flush()

        # Terraform plan.
        tf_plan_cmd = ["terraform", "plan", "-var-file", env_file]
        sproc = subprocess.Popen(tf_plan_cmd,
                                 cwd=env_dir,
                                 stdout=subprocess.PIPE)
        while True:
            nextline = sproc.stdout.readline()
            if nextline == "" and sproc.poll() is not None:
                break

            sys.stdout.write(nextline)
            sys.stdout.flush()

        # Terraform apply
        tf_apply_cmd = ["terraform", "apply", "-var-file", env_file]
        sproc = subprocess.Popen(tf_apply_cmd,
                                 cwd=env_dir,
                                 stdout=subprocess.PIPE)
        while True:
            nextline = sproc.stdout.readline()
            if nextline == "" and sproc.poll() is not None:
                break

            sys.stdout.write(nextline)
            sys.stdout.flush()

    def generate_environment(self):
        print "Generate Environment"
        template_root = self.parsed_input['template_root']
        working_dir = self.parsed_input['working_dir']

        if not os.path.exists(template_root):
            self.slog.logger.error("[%s] template_root does not exist",
                                   template_root)
            sys.exit()

        if not os.path.exists(working_dir):
            self.slog.logger.error("[%s] working_dir does not exist",
                                   working_dir)
            sys.exit()

        self.setup_environment_directory(template_root, working_dir)
        self.run_terraform_commands(working_dir)

    def list_environments(self, envdir):
        '''
        List environments
        '''
        self.slog.logger.debug("List Environments root: %s", envdir)

        # Get a list of all the terraform state files.
        if not os.path.exists(envdir):
            self.slog.logger.error("Invalid envdir %s", envdir)
            return

        envobj = {}
        for dirpath, dirs, files in os.walk(envdir):
            dirname = os.path.basename(dirpath)
            if dirname == "" or dirname == ".terraform":
                continue

            if "terraform.tfstate" in files:
                envobj[dirname] = {}
                envobj[dirname]['filepath'] = os.path.join(dirpath,
                                                           "terraform.tfstate")

            self.slog.logger.debug("Dirpath: %s, Dirs: %s, Files: %s",
                                   dirpath, dirs, files)

        header = ["ENV", "Details"]
        table = prettytable.PrettyTable(header)
        table.align['ENV'] = "l"
        table.align["Details"] = "l"

        for env in envobj.keys():
            table.add_row(["Environment: ", env])
            table.add_row(["-" * 10, "-" * 10])
            with open(envobj[env]['filepath'], "r") as fp:
                state = json.load(fp)
                for module in state['modules']:
                    for reskey, resval in module['resources'].items():
                        attributes = resval['primary']['attributes']
                        if resval['type'] == "aws_instance":
                            table.add_row([resval['type'],
                                           attributes['tags.Name']])
                        elif resval['type'] == "aws_key_pair":
                            table.add_row([resval['type'],
                                           attributes['key_name']])
                        elif resval['type'] == "aws_security_group":
                            table.add_row([resval['type'],
                                           attributes['name']])

        print table



class GeneratorCli(object):
    def __init__(self, args):
        self.namespace = self.__build_parser(args)

    def __build_parser(self, args):
        operation = None
        if len(args) == 1:
            # No arguments provided.
            parser = argparse.ArgumentParser(
                prog="generator",
                formatter_class=argparse.RawTextHelpFormatter,
                description=self.show_help_basic())
        elif args[1] == "build":
            sys.argv.pop(1)
            # Build operation.
            operation = "build"
            parser = argparse.ArgumentParser(
                prog="generator",
                formatter_class=argparse.RawTextHelpFormatter,
                description="Symphony Generator - Build Environment")

            parser.add_argument("--input",
                                required=True,
                                type=open,
                                help="User input file (yaml format)")
        elif args[1] == "list":
            sys.argv.pop(1)
            # List environments.
            operation = "listenv"
            parser = argparse.ArgumentParser(
                prog="generator",
                formatter_class=argparse.RawTextHelpFormatter,
                description="Sympthon Generator - Build Environment")

            parser.add_argument("--envdir",
                                required=True,
                                help="Root directory to all tf state files")

        else:
            operation = None
            parser = argparse.ArgumentParser(
                prog="generator",
                formatter_class=argparse.RawTextHelpFormatter,
                description=self.show_help_basic())

        namespace = parser.parse_args()
        namespace.operation = operation

        return namespace

    def show_help_basic(self):
        print "Symphony Generator"
        print "----------------------------"
        print "Usage: symphony <operation type> <options>"
        print "Operation Types:"
        print "-----------------"
        print "build"
        print "list"
        print ""


def main():
    gencli = GeneratorCli(sys.argv)
    try:
        generator = Generator(gencli.namespace)
    except AttributeError as attrerr:
        print "Namespace [%s] " % attrerr
        sys.exit()

    if gencli.namespace.operation == "build":
        if generator.parsed_input is None:
            sys.exit()

        generator.generate_environment()





if __name__ == '__main__':
    main()
