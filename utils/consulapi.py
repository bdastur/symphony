#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Consul API: Helper utilities to interface with
consul python API client.

'''

import requests
import consulate


class ConsulAPI(object):
    def __init__(self,
                 host='localhost',
                 port=8500):
        '''
        Initialize the ConsulAPI.
        '''
        self.host = host
        self.port = port

        self.client = consulate.Consul(host=self.host, port=self.port)

    def list_nodes(self):
        '''
        Return the nodes for consul
        '''
        try:
            members = self.client.agent.members()
        except requests.ConnectionError:
            print "Connection Error: "
            return (255, None)

        return (0, members)


