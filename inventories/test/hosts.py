#!/usr/bin/python3
import json
import subprocess
import locale

class VagrantIdentityFiles:
    """Caches all Vagrant SSH IdentityFile locations for fast lookup"""

    __identities = []

    def __init__(self):
        completed = subprocess.run(['/bin/sh', '-c', 'vagrant ssh-config | grep -F IdentityFile'],
                                   capture_output=True, encoding=locale.getpreferredencoding())
        self.__identities = self.__extract_identityfiles_only(completed.stdout.splitlines())

    def __extract_identityfiles_only(self, identityfile_list):
        out = []
        for identity in identityfile_list:
            out.append(identity.strip()[len('IdentityFile '):])
        return out

    def get_identityfile_or_empty(self, host):
        for identity in self.__identities:
            if f'/{host}/' in identity:
                return identity
        return ''


def make_hostvars(hosts, identities, common_vars):
    hostvars = {}
    for host in hosts.keys():
        identityfile = identities.get_identityfile_or_empty(host)
        if not identityfile:
            continue
        tmp = {}
        tmp.update(common_vars)
        tmp["instance"] = host
        tmp["ansible_host"] = hosts[host]
        tmp["ansible_ssh_private_key_file"] = identityfile
        hostvars[host] = tmp;
    return hostvars


if __name__ == "__main__":
    identities = VagrantIdentityFiles()        
    hosts = {
        "test.missing.users": "192.168.222.10",
        "test.extra.users": "192.168.222.11",
    }
    common_vars = {
        "ansible_user": "vagrant",
        "ansible_port": "222",
        "ansible_ssh_common_args": "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PubkeyAcceptedKeyTypes=+ssh-rsa",
    }
    hostvars = make_hostvars(hosts, identities, common_vars)
    inventory = {
        "_meta": {
            "hostvars": hostvars,
        },
        "all": {
            "hosts": list(hostvars.keys()),
        },
    }
    print(json.dumps(inventory))
