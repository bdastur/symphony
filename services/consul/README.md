Consul Cluster Configuration:
============================

## Install the Consul Roles by executing the below command

---
```
ansible-galaxy install savagegus.consul -p ./roles/.

```

## Required variables:
---------------------
 consul_version: 0.7.1
 consul_is_server: "true"
 consul_datacenter: "testdc"
 consul_bootstrap: "true"
 consul_is_ui: true
 consul_install_consul_cli: false 
 consul_use_systemd: true
 consul_bind_address: "{{ ansible_default_ipv4['address'] }}"
 consul_advertise_address: "{{ ansible_default_ipv4['address'] }}"
 consul_join_at_start: "true"
 consul_servers: "{{ ipaddrs }}"
 nginx_user: "ec2-user"

