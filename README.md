# General Comments

## SSH configuration issue

SSH is used heavily by ansible to access Linux and RouterOS. Recent librar changes make it more
paranoid about accessing hosts that are not in your known hosts file. You will need to either
update your ansible.cfg file:

```
[defaults]
host_key_checking = False
```

or set the environment variable ```ANSIBLE_HOST_KEY_CHECKING=False```
on the ansible command line or for your shell session.

In addtion, recent changes to libssh restrict the default available algorithm choices
to more secure options. This will prevent connections to older RouterOS versions.
You will probably want to update your ```~/.ssh/config``` file with a stanza similar to this:

```
Host *.hamwan.net
    MACs +hmac-sha1
    KexAlgorithms +diffie-hellman-group14-sha1
    HostKeyAlgorithms +ssh-rsa
    PubkeyAcceptedAlgorithms +ssh-rsa
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

# HamWAN Infrastructure Configs

## Organization (Site) Specific Information

Information on accessing organization hosts is stored in inventories/_site_/group_vars/_group_.yml.
In the HamWAN case, all the hosts we manage are in the group owner_HamWAN, so we have a group_vars file
owner_HamWAN.yml.

RouterOS specific configuration information is in group_vars/os_routeros.yml.

```
---
# vars file for users
users_admin:
  - dylan
  - eo
  - kc7aad
  - KD7DK
  - kennyr
  - KK7LZM
  - nigel
  - N7JMV
  - NQ1E
  - nr3o
  - osburn
  - tom
  - va7dbi
  - ve7alb
users_user:
  - monitoring
group_admin: hamadmin
group_user: ham
group_managed_scope: /etc/group_managed_scope
authorized_key_scheme: ansible.builtin.url
authorized_key_location: https://monitoring.hamwan.net/keys/
test_flaky_network: false
```

users_admim are users who should be given admin access.
users_user are users who should be given an unprivileged account.
For RouterOS, admin_users are group=full and users_user are group=read.

Information specific to specific families of system (e.g. os_routeros and os_linux)
are in respective inventories/_site_/group_vars files, and group_vars/_group_.yml
(e.g. groups_vars/os_routeros.yml that has all the desired RouterOS settings).

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

(This is likely to need updates, to match what is being installed below for Debian.
 A Fedora user will need to do that.)

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
pip3 install molecule ansible-core ansible-pylibssh
pip3 install --upgrade setuptools
pip3 install "molecule-plugins[vagrant]"

ansible-galaxy collection install ansible.posix community.routeros
sudo systemctl enable --now libvirtd
sudo adduser $USER libvirt      # log out and back in for the group to take effect

vagrant up --no-parallel
...
deactivate
```

## Vagrant for the molecule tests

The two roles test against different virtual machines and need different Vagrant providers:

| Role | Boxes | Provider | Extra plugin |
|---|---|---|---|
| `users` | `generic/fedora37` | libvirt (`vagrant-libvirt`) | none |
| `routeros_common` | `cheretbe/routeros` (v6), `cheretbe/routeros7` (v7) | **VirtualBox only** | `vagrant-routeros` (cheretbe), installed automatically |

The cheretbe RouterOS boxes are built by https://github.com/cheretbe/packer-routeros and are only
published for VirtualBox, so the `routeros_common` scenario needs VirtualBox installed (from
Oracle; it is not in Debian's main archive).  The `users` scenario runs on libvirt as above.

### Which Vagrant, which VirtualBox

Distributions ship Vagrant 2.3.x: Debian's `vagrant` is a snapshot taken just before HashiCorp
moved Vagrant to a non-open-source licence (August 2023), and later versions only come from
HashiCorp's own repository.  **Vagrant 2.3.x supports VirtualBox up to 7.0**, so with the
distribution Vagrant install Oracle's `virtualbox-7.0` package.  Oracle builds 7.0 for Debian 12
("bookworm"); that package also installs cleanly on Debian 13 (tested with 7.0.26):

    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/oracle-virtualbox-2016.gpg] https://download.virtualbox.org/virtualbox/debian bookworm contrib" \
      | sudo tee /etc/apt/sources.list.d/oracle-virtualbox.list
    # (key: https://www.virtualbox.org/download/oracle_vbox_2016.asc, dearmored to the path above)
    sudo apt update
    sudo apt install linux-headers-amd64 virtualbox-7.0
    sudo usermod -aG vboxusers $USER

VirtualBox builds its kernel modules against the **running** kernel's headers.  If the machine
has a newer kernel installed than it is running, reboot first.  Watch `/boot` space: kernels with
~120 MB initramfs images fill a small `/boot` quickly, and a failed `update-initramfs` must be
fixed (remove an old kernel, rerun it) before rebooting.

### Running VirtualBox only when needed, alongside libvirt/KVM

KVM (libvirt) and VirtualBox cannot run VMs at the same time; they both need VT-x.  To let them
take turns without unloading modules, have KVM claim VT-x only while a KVM VM is running:

    echo "options kvm enable_virt_at_load=0" | sudo tee /etc/modprobe.d/kvm-virt-on-demand.conf
    # takes effect after a reboot (or reloading the kvm modules)

To keep VirtualBox from loading at boot:

    for s in vboxdrv vboxautostart-service vboxballoonctrl-service vboxweb-service; do sudo systemctl disable $s; done

and start it only for the RouterOS tests:

    sudo systemctl start vboxdrv        # loads the VirtualBox kernel modules
    cd roles/routeros_common && molecule test
    sudo systemctl stop vboxdrv

Rebuilding the modules (`sudo /sbin/vboxconfig`, e.g. after a kernel update) re-enables the
services at boot; disable them again afterwards.

### Test SSH keys

Neither scenario uses the real key site.  The `users` scenario reads `test_keys/` as files; the
`routeros_common` scenario serves its `test_keys/` from a small web server bound to 127.0.0.1
(`molecule/default/key_server.yml`, started by converge, stopped by cleanup), which the RouterOS
VMs reach through VirtualBox NAT at 10.0.2.2.  Port 18080 must be free on the test host.

### The `vagrant-routeros` plugin: do not install it by name

- **You never need to install it yourself.**  Each cheretbe RouterOS box contains
  `vagrant-routeros-<version>.gem` and its own Vagrantfile installs it the first time you
  `vagrant up` a RouterOS VM (if no `vagrant-routeros` of at least that version is installed).
  The copy is kept under `~/.vagrant.d/boxes/cheretbe-VAGRANTSLASH-routeros*/<box version>/virtualbox/`.
- **The `vagrant-routeros` gem on rubygems.org is a different plugin** (ktogias, versions 0.0.x).
  Never run `vagrant plugin install vagrant-routeros`, and avoid `vagrant plugin expunge --reinstall`
  (it re-fetches plugins by name from rubygems.org).  That plugin replaces Vagrant's `shell`
  provisioner with one that does nothing on non-RouterOS guests, so the `users` VMs boot
  unprovisioned: `eth1` gets a DHCP address, nothing listens on port 222, and molecule fails with
  "No route to host".  Check with `vagrant plugin list`: the right one is
  `vagrant-routeros (0.5.0 or later, global)`.
- **After a Vagrant or Ruby upgrade** Vagrant may refuse to start with
  `Unable to resolve dependency: user requested 'vagrant-routeros (= 0.5.0)'` (plugins are
  stored per Ruby version).  Fix it as the packer-routeros README says:

      vagrant plugin uninstall vagrant-routeros

  The next `vagrant up` of a RouterOS box reinstalls it.  If you need it before then (for
  example only `users` tests are run and Vagrant still complains), install the copy from a
  downloaded box:

      vagrant plugin install ~/.vagrant.d/boxes/cheretbe-VAGRANTSLASH-routeros7/*/virtualbox/vagrant-routeros-*.gem

### Quick checks

    vagrant plugin list                      # vagrant-libvirt; vagrant-routeros 0.5.0+ (if installed)
    cd roles/users && molecule test          # libvirt, 3 Fedora VMs
    cd roles/routeros_common && molecule test  # VirtualBox, 6 RouterOS VMs

If a `users` VM comes up without its 192.168.58.x address on `eth1`, run
`vagrant provision <name>`: a working shell provisioner prints `Running: inline script` and two
`success` lines.  If it prints nothing, check `vagrant plugin list` as above.

## See Also

roles/routeros_common/README.md
