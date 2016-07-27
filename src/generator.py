#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Generator: The porgram reads a user input file
and builds the app environment.

'''

import sys
import os
import yaml
import argparse
import jinja2
import utils.symphony_logger as logger


class Generator(object):
    '''
    Read the user input file. Perform validations
    and provide APIs to access data.
    '''
    def __init__(self, inputfile, build_dir):
        self.inputfilename = inputfile.name
        self.build_dir = build_dir

        self.slog = logger.Logger(name="Generator")
        self.parsed_input = self.__parse_userinput(inputfile)
        if self.parsed_input is None:
            self.slog.logger.error("Parsing Failed for %s",
                                   self.inputfilename)
        else:
            self.slog.logger.info("Parsed %s successfull",
                                  self.inputfilename)

    def __is_valid_userinput(self, parsed_data):
        required_valid_keys = ['services', 'cloud', 'name']

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

    def setup_environment_directory(self):
        print "Setup env dir"

    def generate_environment(self):
        print "Generate Environment"
        self.setup_environment_directory()


class GeneratorCli(object):
    def __init__(self, args):
        slog = logger.Logger(name="GeneratorCLI")
        self.namespace = self.__build_parser(args)
        if self.namespace.operation == "build":
            # Check if the path to build dir is valid.
            if not os.path.exists(self.namespace.build_dir):
                slog.logger.error("Build Dir %s not valid",
                                  self.namespace.build_dir)
                return
        elif self.namespace.operation is None:
            print "No operation"

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

            parser.add_argument("--build_dir",
                                required=True,
                                help="Build Directory")
            parser.add_argument("--input",
                                required=True,
                                type=open,
                                help="User input file (yaml format)")
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
        print ""



def main():
    gencli = GeneratorCli(sys.argv)
    try:
        generator = Generator(gencli.namespace.input,
                              gencli.namespace.build_dir)
    except AttributeError as attrerr:
        print "Invalid Namespace [%s] " % attrerr
        sys.exit()

    if generator.parsed_input is None:
        sys.exit()

    generator.generate_environment()





if __name__ == '__main__':
    main()
