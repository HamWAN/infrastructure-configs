# HamWAN Infrastructure Configs

## Operator Workstation Setup (Fedora)

```
cd ~
sudo dnf -y install ansible git jq
git clone --recursive https://github.com/HamWAN/infrastructure-configs.git
cd infrastructure-configs
cp .ansible.cfg ~
ansible-galaxy install -r roles/requirements.yml
```

### Listing all hosts in PSDR inventory

```
ansible --list-hosts all
```

### Listing all hosts in PSDR with OS=Linux

```
ansible --list-hosts os_linux
```

### Listing all hosts in PSDR with OS=Linux and Owner=HamWAN

```
ansible --list-hosts 'os_linux:&owner_HamWAN'
```

### Listing all hosts in PSDR with OS=Linux and Owner=HamWAN that aren't Type=Container

```
ansible --list-hosts 'os_linux:&owner_HamWAN:!type_container'
```

### General inventory exploration

Now that you know the basics of group matching, you can surf the available inventory:

```
~/infrastructure-configs/inventories/psdr/hosts.sh | jq | less
```

More details about selecting inventory subsets [here](https://docs.ansible.com/ansible/latest/inventory_guide/intro_patterns.html#pattern-processing-order).

### Running the PSDR playbook against a single server

```
ansible-playbook --limit <server> psdr.yml
```

### Running the PSDR playbook against the targets predefined inside it

```
ansible-playbook psdr.yml
```

## Testing Strategy

We use [Ansible Molecule](https://github.com/ansible/molecule) for testing.
This user role includes the necessary vagrant and molecule configuration to test various user management
tasks using virtual machines under vagrant/libvirt. It also tests for behavior in the face of flakey connections.
The routeros_common role tests for setting or changing settings that are both present or missing beforehand on both RouterOS 6 and 7.

## Developer Workstation Setup (Fedora)

First, run the Operator Workstation Setup, then:

```
sudo dnf -y install vagrant-libvirt rubygem-rexml @virtualization
sudo systemctl enable --now libvirtd
sudo usermod --append --groups libvirt `whoami`
vagrant up --no-parallel
```

## Developer Workstation Setup (Debian)

```
sudo apt install virtualenv
sudo apt install python3-pip libssl-dev
sudo apt install vagrant-libvirt
sudo apt install qemu-system libvirt-daemon-system

cd infrastructure_configs
virtualenv venv
. venv/bin/activate
pip3 install ansible-dev-tools
pip3 install molecule ansible-core
pip3 install --upgrade setuptools
pip3 install "molecule-plugins[vagrant]"

ansible-galaxy collection install ansible.posix
sudo systemctl enable --now libvirtd
sudo adduser libvirt

vagrant up --no-parallel
...
deactivate
```
