#!/usr/bin/python3
'''Produces a json formated invemntory of Vagrant hosts that will be used
   for testing routeros_common role.  The inventory contains information that
   will be needed for connecting to the test instances.

   See roles/routeros_common/README.md for some more description of testing strategy.
'''
import json
import subprocess
import locale
import os
import stat

# Only usable if the identity file has the hostname in it.
class VagrantIdentityFiles:
    """Caches all Vagrant SSH IdentityFile locations for fast lookup"""

    def __init__(self):
        completed = subprocess.run(['/bin/sh', '-c', 'vagrant ssh-config | grep -F IdentityFile'],
                                   capture_output=True, encoding=locale.getpreferredencoding())
        #print(f'vagrant returned {completed}')
        self.__identities = self.__extract_identityfiles_only(completed.stdout.splitlines())
        #print(f'identities are {self.__identities}')

    def __extract_identityfiles_only(self, identityfile_list):
        out = []
        for identity in identityfile_list:
            out.append(identity.strip()[len('IdentityFile '):])
        return out

    def get_identityfile_or_empty(self, host):
        #print(f'get_identityfile for {host}')
        for identity in self.__identities:
            if f'/{host}/' in identity:
                print(f'get_identityfile found {identity}')
                return identity
        if len(self.__identities) == 1:
            return self.__identities[0]
        return ''


# Alternative for use when using a single common identity file.
class LocalIdentityFile:
    """ Always returns the same local identity file """

    def __init__(self, relative_filename):
        self.__identityfile = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                           relative_filename)
        os.chmod(self.__identityfile, stat.S_IRUSR | stat.S_IWUSR)

    def get_identityfile_or_empty(self, host):
        return self.__identityfile


def make_hostvars(hosts, identities, common_vars):
    hostvars = {}
    for host in hosts.keys():
        identityfile = identities.get_identityfile_or_empty(host)
        #print(f'make_hostvars - identityfile is {identityfile}')
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
    identities = LocalIdentityFile(f"{os.environ['HOME']}/.vagrant.d/insecure_private_key")
#    identities = VagrantIdentityFiles()
    # These need to match the Vagrant configuration in roles/routeros_common/molecule/default
    hosts = {
        "ros6.correct": "192.168.56.20",
        "ros6.incorrect": "192.168.56.21",
        "ros6.missing": "192.168.56.22",
        "ros7.correct": "192.168.56.23",
        "ros7.incorrect": "192.168.56.24",
        "ros7.missing": "192.168.56.25",
    }
    common_vars = {
        "ansible_user": "vagrant+ct132w",
        "ansible_port": "22",
        "ansible_connection": "local",
        "ansible_network_cli_ssh_type": "libssh",
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
        "os_routeros": list(hostvars.keys()),
    }
    print(json.dumps(inventory))
