# HamWAN Infrastructure Configs
This repository hosts a group of ansible playbooks to deploy and manage HamWAN infrastructure.

## Prerequisites
* Ansible, as installed using their [docs](http://docs.ansible.com/intro_installation.html)
* Python's dns
* An installed SSH cert to use when connecting with clients
* python-netaddr

## Usage
```bash
apt-add-repository ppa:ansible/ansible
apt-get update
apt-get install python-pip python-netaddr ansible git software-properties-common -y
pip install dnspython
ansible-galaxy install yaegashi.blockinfile
ansible-galaxy install williamyeh.prometheus
ansible-galaxy install savagegus.consul
git clone https://github.com/HamWAN/infrastructure-configs
```
To use the playbooks, clone this repository. The example here is as if you're configuring a new cell site. This assumes you already have the host entries added to your DNS, but that the routers are running locally as freshly-reset routers with IPs on your lan (AKA you need to give them statics that are accessible for this stuff to work, or instead use this to update existing hosts). Take a look at "demo.yml", specifically the "ignore_ospf_and_ip_address" part; you'll want this set to false if you're configuring new radios, but set to true if you're trying to reconfigure radios that are already deployed. Then, edit the "hosts" inventory file to contain the hostnames of the routers which you want to be configured (make sure to update the groups to be relevant as well!). Finally run the playbook like this:
```bash
ansible-playbook -i locales/memphis/hosts linux_setup.yml -u hamwan -k -K -s --vault-password-file ~/.vault_pass.txt -vvvv
ansible-playbook -i locales/memphis/hosts jira.yml -u ryan_turner -s --vault-password-file ~/.vault_pass.txt -vvvv
ansible-playbook -i locales/memphis/hosts add_new_netop.yml -u ryan_turner -s --vault-password-file ~/.vault_pass.txt -vvvv
ansible-playbook -i locales/seattle/hosts shinysdr.yml -u (your-remote-username) -s --vault-password-file ~/.vault_pass.txt -vvvv
ansible-playbook -i locales/memphis/hosts base_station_core_router.yml --vault-password-file ~/.vault_pass.txt -vvvv -u ryan_turner --limit sco --extra-vars "default_user=admin"
```
~/.vault_pass.txt should contain the vault password for your locale's secret values.

Here's an example of configuring a new cell site:
Get each piece of equipment connected to your lan. Add it to your DNS and add the appropriate entries to your locale's hosts file. Then, execute the following, making the appropriate substitutions for your username:
```base
ansible-playbook -i locales/memphis/hosts playbooks/mikrotik_fresh.yml --vault-password-file ~/.vault_pass.txt -vvvv --extra-vars "default_user=admin scp_user=ryan_turner" -u admin
ansible-playbook -i locales/memphis/hosts playbooks/mikrotik_site_setup.yml --vault-password-file ~/.vault_pass.txt -vvvv --extra-vars "scp_user=ryan_turner" -u ryan_turner
```
The first command updates the routers and does some basic universal configuration; the second one then looks for each core router, sector, and ptp and configures them with their appropriate settings.

### SSH to servers
Since we use cert auth everywhere, you'll need to have SSH'd to that remote server at least once and have your cert installed locally for connecting to that server. Also, if your local use is different than your remote user, be sure to add -u remote_user to your ansible-playbook command!

## Use to configure a new appliance
* First, make sure you have the router on your LAN and with an IP and gateway (can it ping google.com?)
* Second, on the local machine running ansible, add an /etc/hosts entry for your router's hostname to point to the lan IP.
* Run as usual using your playbooks necessary

## License
Refer to LICENSE.md
