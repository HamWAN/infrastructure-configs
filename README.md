# HamWAN Infrastructure Configs

## Operator Workstation Setup (Fedora)

```
cd ~
sudo dnf -y install ansible git
git clone --recursive https://github.com/HamWAN/infrastructure-configs.git
cp infrastructure-configs/.ansible.cfg ~
```

### Running the PSDR Playbook

```
ansible-playbook psdr.yml
```

## Developer Workstation Setup (Fedora)
```
sudo dnf -y install vagrant-libvirt rubygem-rexml @virtualization
sudo systemctl enable --now libvirtd
sudo usermod --append --groups libvirt `whoami`
vagrant up --no-parallel
```
