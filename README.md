# HamWAN Infrastructure Configs
This repository hosts a group of ansible playbooks to deploy and manage HamWAN infrastructure.

## Prerequisites
* Ansible, as installed using their [docs](http://docs.ansible.com/intro_installation.html)
* Python's dns
* An installed SSH cert to use when connecting with clients
* sshpass if you want to use the management-user-creation part

## Usage
```bash
pip install dnspython
```
To use the playbooks, clone this repository. Then edit the "hosts" inventory file to contain the hostnames of the routers which you want to be configured (make sure to update the groups to be relevant as well!). Finally run the playbook like this:
```bash
ansible-playbook -i hosts demo.yml
```
Note that by default this does *everything*. You probably just want to do specific things, which is when --tags and --skip-tags comes in handy. We've got specifically so far:
* management-user-creation - this uses the default admin user with password auth to create the management user
* upgrade-ros - this upgrades the version of routeros

## License
Refer to LICENSE.md
