#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Ansible Dynamic inventory.
'''

import sys
import os
import argparse
import json

try:
    import symphony.tfparser as tfparser
except ImportError:
    import tfparser

try:
    import utils.symphony_logger as logger
except ImportError:
    import symphony_logger as logger


class TFInventory(object):
    def __init__(self):
        self.slog = logger.Logger(name="tf_inventory")

        self.tf_root = os.environ.get('TERRAFORM_STATE_ROOT',
                                      ".")
        self.priv_ip_flag = os.environ.get('USE_PRIVATE_IP',
                                           "True")

        self.tfparser = tfparser.TFParser(self.tf_root)
        self.tfobject = self.tfparser.tfobject
        self.slog.logger.debug("TF Inventory init done")

    def list_inventory(self):
        inventory = dict()
        inventory['_meta'] = {}
        inventory['_meta']['hostvars'] = {}
        hostvars = inventory['_meta']['hostvars']

        self.generate_server_info(hostvars)
        self.generate_host_groups(inventory)

        inventory['testgroup'] = {}
        inventory['testgroup']['hosts'] = []
        inventory['testgroup']['hosts'] = ['Consul-0', 'Consul-1']

        return inventory

    def generate_host_groups(self, inventory):
        '''
        Generate the various Ansible groups.
        '''
        for env in self.tfobject.keys():
            for module in self.tfobject[env]['modules']:

                # First lets create host groups for the explicitly set
                # output vars.
                for output in module['outputs'].keys():
                    inventory[output] = {}
                    inventory[output]['hosts'] = []
                    inventory[output]['vars'] = {}
                    inventory[output]['vars']['ipaddrs'] = []
                    for ipaddr in module['outputs'][output]['value']:
                        for host in inventory['_meta']['hostvars'].keys():
                            hostobj = inventory['_meta']['hostvars'][host]
                            if hostobj['ansible_ssh_host'] == ipaddr:
                                inventory[output]['hosts'].append(host)
                                inventory[output]['vars']['ipaddrs'].\
                                    append(ipaddr)

                # Group hosts by Tags.
                for reskey, resval in module['resources'].items():
                    attributes = resval['primary']['attributes']
                    restype = resval['type']

                    if restype != "aws_instance":
                        continue

                    hostname = attributes['tags.Name']

                    for key in attributes.keys():
                        if key.startswith("tags."):
                            hostgroup = "%s=%s" % (key, attributes[key])
                            if inventory.get(hostgroup, None) is None:
                                inventory[hostgroup] = {}
                                inventory[hostgroup]['hosts'] = []
                            else:
                                inventory[hostgroup]['hosts'].append(hostname)

    def generate_server_info(self, hostvars):
        '''
        Populate the host specific info in hostvars
        '''
        for env in self.tfobject.keys():
            for module in self.tfobject[env]['modules']:
                for reskey, resval in module['resources'].items():
                    attributes = resval['primary']['attributes']
                    restype = resval['type']
                    if restype != "aws_instance":
                        continue
                    try:
                        hostname = attributes['tags.Name']
                    except KeyError:
                        self.slog.logger.error("Tags Name not found")
                        continue

                    # Populate hostvar attributes.
                    hostvars[hostname] = {}
                    if self.priv_ip_flag:
                        hostvars[hostname]['ansible_ssh_host'] = \
                            attributes['private_ip']
                    else:
                        hostvars[hostname]['ansible_ssh_host'] = \
                            attributes['public_ip']
                    hostvars[hostname]['availability_zone'] = \
                        attributes['availability_zone']
                    hostvars[hostname]['ami'] = \
                        attributes['ami']
                    hostvars[hostname]['id'] = \
                        attributes['id']
                    hostvars[hostname]['subnet_id'] = \
                        attributes['subnet_id']


def show_help():
    msg = "Terraform Ansible Dynamic Inventory"
    return msg


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="tf_inventory",
        formatter_class=argparse.RawTextHelpFormatter,
        description=show_help())

    parser.add_argument("--list",
                        action='store_true')
    parser.add_argument("--host",
                        action='store_true')

    return parser.parse_args()


def main():

    args = parse_arguments()
    if args.list:
        tfinventory = TFInventory()
        inv = tfinventory.list_inventory()
        jinv = json.dumps(inv, indent=2, sort_keys=True)
        print jinv
    elif args.host:
        sys.exit(1)


if __name__ == '__main__':
    main()
