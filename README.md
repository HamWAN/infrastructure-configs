# HamWAN Infrastructure Configs
This repository hosts a group of ansible playbooks to deploy and manage HamWAN infrastructure.

## Prerequisites
* Ansible, as installed using their [docs](http://docs.ansible.com/intro_installation.html)

## Usage
To use the playbooks, clone this repository. Then edit the "hosts" inventory file to contain the hostnames of the routers which you want to be configured (make sure to update the groups to be relevant as well!). Finally run the playbook like this:
```bash
ansible-playbook -i hosts demo.yml
```

## License
Refer to LICENSE.md
