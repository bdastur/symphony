#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Symphony:
---------


'''

import sys
import argparse
import main.helper as helper


class SymphonyCli(object):
    '''
    Symphoncy CLI Handler.
    '''
    def __init__(self, args):
        self.namespace = self.__build_parser(args)

    def __build_parser(self, args):
        operation = None
        parser = argparse.ArgumentParser(
            prog="symphony",
            formatter_class=argparse.RawTextHelpFormatter,
            description=self.show_help())

        if len(args) == 1:
            # No arguments provided.
            parser = argparse.ArgumentParser(
                prog="symphony",
                formatter_class=argparse.RawTextHelpFormatter,
                description=self.show_help())
        else:
            operation = args[1]
            sys.argv.pop(1)

            if operation == "build":
                # Build Operation Options.

                parser = argparse.ArgumentParser(
                    prog="symphony",
                    formatter_class=argparse.RawTextHelpFormatter,
                    description=self.show_build_help())

                parser.add_argument("--config",
                                    required=True,
                                    type=open,
                                    help="User/Cluster configuration file")
                parser.add_argument("--environment",
                                    required=True,
                                    help="Path to environments configuration")
                parser.add_argument("--staging",
                                    required=True,
                                    help="Path to terraform staging directory")
                parser.add_argument("--template",
                                    required=False,
                                    default="./templates",
                                    help="Path to the templates")
                parser.add_argument("--skip-deploy",
                                    required=False,
                                    dest="skip_deploy",
                                    action="store_true",
                                    help="Skip Deploy step (tf apply/plan)")
            elif operation == "deploy":
                # Deploy Operation Option.
                parser = argparse.ArgumentParser(
                    prog="symphony",
                    formatter_class=argparse.RawTextHelpFormatter,
                    description=self.show_deploy_help())

                parser.add_argument("--staging",
                                    required=True,
                                    help="Path to terraform staging directory")
            elif operation == "configure":
                # Configure Operation Option.
                parser = argparse.ArgumentParser(
                    prog="symphony",
                    formatter_class=argparse.RawTextHelpFormatter,
                    description=self.show_configure_help())

                parser.add_argument("--config",
                                    required=True,
                                    type=open,
                                    help="User/Cluster configuration file")
                parser.add_argument("--environment",
                                    required=True,
                                    help="Path to environments configuration")
                parser.add_argument("--staging",
                                    required=True,
                                    help="Path to terraform staging directory")
            elif operation == "destroy":
                # Destroy Operation.
                parser = argparse.ArgumentParser(
                    prog="symphony",
                    formatter_class=argparse.RawTextHelpFormatter,
                    description=self.show_destroy_help())

                parser.add_argument("--staging",
                                    required=True,
                                    help="Path to terraform staging directory")
            elif operation == "list":
                # List Operation.
                parser = argparse.ArgumentParser(
                    prog="symphony",
                    formatter_class=argparse.RawTextHelpFormatter,
                    description=self.show_list_help())

                parser.add_argument("--staging",
                                    required=True,
                                    help="Path to terraform staging directory")

            else:
                operation = None

        namespace = parser.parse_args()
        namespace.operation = operation

        return namespace

    def __print_banner(self):
        '''
        Display generic banner
        '''
        banner = ""
        banner += "=" * 50
        banner += "\nSymphony: Build, Deploy, Configure - with a click\n"
        banner += "-" * 50
        banner += "\n"

        return banner

    def show_deploy_help(self):
        '''
        Display help for deploy operation
        '''
        msg = self.__print_banner()
        msg += "Operation: deploy\n"
        msg += "deploy operation takes the following user inputs:\n" \
            "---------------------------------------------------\n" \
            " staging: Location where terraform files are generated.\n"
        msg += "\n"
        msg += "The deploy step runs the terraform apply on the rendered\n" \
            "terraform definitions in the staging location\n"

        return msg

    def show_configure_help(self):
        '''
        Display help for configure operation
        '''
        msg = self.__print_banner()
        msg += "Operation: configure\n"
        msg += "configure operation takes the following user inputs:\n" \
            "------------------------------------------------------\n" \
            " config: The cluster configure file.\n\n" \
            " staging: Location where the terraform files are generated.\n"
        msg += "\n"
        msg += "The configure step runs through the ansible playbooks for\n" \
            "configuring the required services as asked by the user.\n"

        return msg

    def show_destroy_help(self):
        '''
        Display help for Destroy operation
        '''
        msg = self.__print_banner()
        msg += "Operation: Destroy\n"
        msg += "destroy operation takes the following user inputs:\n" \
            " staging: Location where the terraform files are generated.\n"
        msg += "\n"
        msg += "The destroy operation performs a terraform destroy \n" \
            "to destroy the cluster. There are no second changes after this\n" \
            "operation. No configs are retained, or backups taken.\n"

        return msg

    def show_list_help(self):
        '''
        Display help for List operation
        '''
        msg = self.__print_banner()
        msg += "Operation: List\n"
        msg += "list operation takes the following user inputs:\n" \
            " staging: Location where the terraform files are generated.\n"
        msg += "\n"
        msg += "The list operation parsers through the staging location\n" \
            "to display a tabular list of resources generated per cluster.\n"

        return msg

    def show_build_help(self):
        '''
        Display help for build operation
        '''
        msg = self.__print_banner()
        msg += "Operation: build\n"
        msg += "build operation takes the following user inputs:\n" \
            "--------------------------------------------------\n" \
            " config: A user provide configuration file.\n" \
            " You can look at a sample configuration file under examples.\n"
        msg += "\n"
        msg += " environment: A path to the environments configuration.\n" \
            " An environment file specifies the cloud environment like\n" \
            " vpcs, subnets, credentials for accessing the cloud, etc\n" \
            " A sample environment configuration file can be found in" \
            " examples\n"
        msg += "\n"
        msg += " staging: Location where terraform files will be generated.\n"
        msg += " symphony will generate the terraform file based on the\n" \
            " configuration specified in the config file.\n" \
            " A templates are located under templates/ folder\n"

        return msg

    def show_help(self):
        '''
        Display Help
        '''
        print self.__print_banner()
        print "\nUsage: symphony <operation> [options]"
        print "\nOperation Types:"
        print "-" * 40
        print "build"
        print "deploy"
        print "configure"
        print "destroy"
        print "list"
        print "\n"
        print "To display command specific help:"
        print "symphony <operation> -h"
        print ""

    def generate_operation_object(self, cli_namespace):
        '''
        Parse the argparse namespace object and return a
        dictionary that returns the operation and params
        '''
        obj = {}
        obj['operation'] = cli_namespace.operation

        try:
            obj['config'] = cli_namespace.config
        except AttributeError:
            pass

        try:
            obj['environment'] = cli_namespace.environment
        except AttributeError:
            pass
        try:
            obj['staging'] = cli_namespace.staging
        except AttributeError:
            pass

        try:
            obj['skip_deploy'] = cli_namespace.skip_deploy
        except AttributeError:
            pass

        try:
            obj['template'] = cli_namespace.template
        except AttributeError:
            pass

        return obj



def main():
    '''
    The Symphony CLI main Runner.
    Parse the CLI, and invoke the helper to perform the operation.
    '''
    clihandler = SymphonyCli(sys.argv)
    print "Namespace: ", clihandler.namespace

    # If the operation is not set, exit here.
    if clihandler.namespace.operation is None:
        sys.exit()

    # From the parse object generated a dictionary which can be
    # passed to the helper class.
    operobj = clihandler.generate_operation_object(clihandler.namespace)
    print operobj

    helperobj = helper.Helper(operobj)
    print helperobj.valid
    if not helperobj.valid:
        print "Helper Initialization Failed."
        sys.exit()

    helperobj.perform_operation()



if __name__ == '__main__':
    main()
