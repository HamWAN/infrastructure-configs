# HamWAN Infrastructure Configs

## Operator Workstation Setup (Fedora)

```
cd ~
sudo dnf -y install ansible git jq
git clone --recursive https://github.com/HamWAN/infrastructure-configs.git
cp infrastructure-configs/.ansible.cfg ~
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

## Developer Workstation Setup (Fedora)

First, run the Operator Workstation Setup, then:

```
sudo dnf -y install vagrant-libvirt rubygem-rexml @virtualization
sudo systemctl enable --now libvirtd
sudo usermod --append --groups libvirt `whoami`
vagrant up --no-parallel
```
