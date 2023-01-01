# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  #
  # WARNING: Keep "inventories/test/hosts.py" in sync with these hosts!
  #

  VMs = [
    {
      "name" => 'test.missing.users',
      "ip" => '192.168.222.10',
      "custom" => '
        groupadd hamadmin
        groupadd ham
        useradd eo -G hamadmin
        mkdir -m 0700 ~eo/.ssh
        echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILkuO+XcdH7AVa326qU6Sw8Ly4Ju3mszmU4ydL6LqHhO eo@ansible.bartk.us" > ~eo/.ssh/authorized_keys
        chmod 0600 ~eo/.ssh/authorized_keys
        chown -R eo:eo ~eo/.ssh
        echo "%hamadmin ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/hamadmin
        useradd monitoring -G ham
      ',
    },
    {
      "name" => 'test.extra.users',
      "ip" => '192.168.222.11',
      "custom" => '
        groupadd hamadmin
        groupadd ham
        useradd eo -G hamadmin
        mkdir -m 0700 ~eo/.ssh
        echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILkuO+XcdH7AVa326qU6Sw8Ly4Ju3mszmU4ydL6LqHhO eo@ansible.bartk.us" > ~eo/.ssh/authorized_keys
        chmod 0600 ~eo/.ssh/authorized_keys
        chown -R eo:eo ~eo/.ssh
        echo "%hamadmin ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/hamadmin
        useradd haxxxor -G hamadmin
        useradd monitoring -G ham
        useradd soyboy -G ham
      ',
    },
    {
      "name" => 'test.group.change',
      "ip" => '192.168.222.12',
      "custom" => '
        groupadd hamwan
        useradd eo -G hamwan
        mkdir -m 0700 ~eo/.ssh
        echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILkuO+XcdH7AVa326qU6Sw8Ly4Ju3mszmU4ydL6LqHhO eo@ansible.bartk.us" > ~eo/.ssh/authorized_keys
        chmod 0600 ~eo/.ssh/authorized_keys
        chown -R eo:eo ~eo/.ssh
        echo "%hamwan ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/hamwan
        useradd monitoring
      ',
    },
  ]
 
  VMs.each do |vm|
    config.vm.define vm["name"] do |node|
      node.vm.box = "generic/fedora37"
      node.vm.hostname = vm["name"]
      node.vm.network "private_network", ip: vm["ip"], auto_config: false
      node.vm.provider :libvirt do |libvirt|
        libvirt.qemu_use_session = false
      end
      #node.ssh.port = 222
      #node.ssh.guest_port = 222
      node.vm.provision "shell", inline: <<-SHELL
        semanage port -a -t ssh_port_t -p tcp 222
        firewall-cmd --add-port=222/tcp --permanent
        firewall-cmd --reload
        IP_eth0=`ip -f inet addr show eth0 | grep -Po 'inet \\K[\\d.]+'`
        IP_eth1=#{vm["ip"]}
        CONNECTION_eth1=`nmcli dev show eth1 | grep "GENERAL.CONNECTION" | sed -e 's/.*: *//'`
        nmcli con mod "${CONNECTION_eth1}" ipv4.method manual ipv4.addresses ${IP_eth1}/24
        nmcli con up "${CONNECTION_eth1}"
        echo "ListenAddress ${IP_eth0}:22" >> /etc/ssh/sshd_config
        echo "ListenAddress ${IP_eth1}:222" >> /etc/ssh/sshd_config
        systemctl restart sshd
        #{vm["custom"]}
      SHELL
    end
  end
end
