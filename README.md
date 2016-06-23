# HamWAN Infrastructure Configs
This repository hosts a group of ansible playbooks to deploy and manage HamWAN infrastructure.

## Prerequisites
* Ansible 2
* Python's dns
* An installed SSH cert to use when connecting with clients
* python-netaddr, dnspython, blockinfile
* Working HamWAN portal

## Usage
```bash
apt-add-repository ppa:ansible/ansible
apt-get update
apt-get install python-pip python-netaddr ansible git software-properties-common -y
pip install dnspython
ansible-galaxy install yaegashi.blockinfile
ansible-galaxy install DavidWittman.redis
ansible-galaxy install Mayeu.RabbitMQ
ansible-galaxy install Mayeu.sensu
git clone https://github.com/HamWAN/infrastructure-configs
```

A few examples:
```bash
ansible-playbook -i locales/memphis/hosts.sh linux_setup.yml -u hamwan -k -K -s --vault-password-file ~/.vault_pass.txt -vvvv --limit voip.leb.memhamwan.net
```
~/.vault_pass.txt should contain the vault password for your locale's secret values.

Here's an example using our routeros_sectors playbook to configure an existing sector:
```bash
ansible-playbook -i locales/memphis/hosts.sh routeros_sectors.yml --vault-password-file ~/.vault_pass.txt -vvvv --limit omn2.azo.memhamwan.net
ansible-playbook -i locales/memphis/hosts.sh routeros_site_router.yml --vault-password-file ~/.vault_pass.txt -vvvv --limit r1.mno.memhamwan.net
ansible-playbook -i locales/memphis/hosts.sh routeros_ptp.yml --vault-password-file ~/.vault_pass.txt -vvvv --limit ptpleb.hil.memhamwan.net
ansible-playbook -i locales/memphis/hosts.sh routeros_upgrade.yml --vault-password-file ~/.vault_pass.txt -vvvv
ansible-playbook -i locales/memphis/hosts.sh routeros_omni.yml --vault-password-file ~/.vault_pass.txt -vvvv --limit omn1.leb.memhamwan.net
```

Here's an example of configuring a new VM and then setting it up for sensu. Note that the user provided for the first command matches whatever you had configured during OS install, but then for the next command it uses your local user and key.
```bash
ansible-playbook -i locales/memphis/hosts.sh linux_setup.yml -u ryan_turner -k -K -s --vault-password-file ~/.vault_pass.txt -vvvv --limit eden.mno.memhamwan.net
ansible-playbook -i locales/memphis/hosts.sh sensu_client.yml -s --vault-password-file ~/.vault_pass.txt -vvvv --limit eden.mno.memhamwan.net
ansible-playbook -i locales/memphis/hosts.sh chat.yml -s --vault-password-file ~/.vault_pass.txt -vvvv --limit chat.mno.memhamwan.net
ansible-playbook -i locales/memphis/hosts.sh sensu_checks.yml -s --vault-password-file ~/.vault_pass.txt -vvvv --limit monitor.mno.memhamwan.net
```
The first command updates the routers and does some basic universal configuration; the second one then looks for each core router, sector, and ptp and configures them with their appropriate settings.

Let's setup field day! For memhamwan, that means a core router, three APs for general public use, and two PtP links. The expectation is that the wireless interface of the PtP link will be manually configured, since that's site specific.
```base
ansible-playbook -i locales/memphis/hosts.sh field_day.yml --vault-password-file ~/.vault_pass.txt -vvvv -u ryan_turner
```

### SSH to servers
Since we use cert auth everywhere, you'll need to have SSH'd to that remote server at least once and have your cert installed locally for connecting to that server. Also, if your local use is different than your remote user, be sure to add -u remote_user to your ansible-playbook command!

## Configuring a new appliance
* First, make sure you have the router on your LAN and with an IP and gateway (can it ping google.com?)
* Second, in your ansible-playbook command, add the following: ```--extra-vars "ansible_host=[local-ip]"```; make sure that you limit the command to only run on one host at a time!

## License
Refer to LICENSE.md
