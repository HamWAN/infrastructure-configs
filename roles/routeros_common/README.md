# routeros_common Role

This role is designed to query various routeros settings and update or create them if they
do not match desired settings.  The configruation is split into two locations.
 - roles/routeros_common/vars/main.yml holds the description of each setting and how to change it.
 - group_vars/os_routeros.yml sets the site specific values used by the file above.
By putting the values in group_vars, the can be overriden where needed by entries in host_vars.

It is currently tested against routeros versions up to 6.1-6.49.x and 7.1-7.16.

The user is expected to have SSH access to the devices.

## Logging in: the `+cet512w` suffix (read this first)

RouterOS takes terminal options from the login name: everything after a `+`.  This role needs
them, so if your RouterOS user is `myname` you must log in as **`myname+cet512w`**
(`c` no colours, `e` dumb terminal, `t` no terminal auto-detection, `512w` 512 columns wide).
Without them RouterOS wraps every input line longer than about 80 characters (prompt
included) and echoes it back in fragments.  The fragments end up in the output, so set
commands look as if they failed and settings never compare as correct; on every run the role
"fixes" settings that are already right, or fails.  More detail:
https://docs.ansible.com/projects/ansible/latest/network/user_guide/platform_routeros.html and
https://help.mikrotik.com/docs/spaces/ROS/pages/328134/Command+Line+Interface

Pass it on the command line, e.g.

    ansible-playbook psdr.yml -l R1.Example.hamwan.net -u myname+cet512w --tags routeros --check --diff

### Watch out: `~/.ssh/config` beats `-u`

Ansible's usual order for the login name is: `ansible_user` (inventory / host_vars /
group_vars / `-e`) over `-u` on the command line, over `remote_user` in ansible.cfg /
`ANSIBLE_REMOTE_USER`.  **But this role connects with libssh** (`ansible_network_cli_ssh_type:
libssh` in `vars/main.yml`), and libssh reads `~/.ssh/config` *after* Ansible has set the name.
If a `Host` block there matching the router has a `User` line, that name is used instead of
whatever Ansible chose, and the `+cet512w` suffix is silently lost.

Plain `ssh myname+cet512w@router` works either way, because OpenSSH lets the command line win,
which makes this hard to spot.  The router log shows the name it really got:

    /log print where message~"publickey accepted"

Fix it in `~/.ssh/config` on the machine you run Ansible from, either by removing the `User`
line from any `Host` pattern that matches the routers, or by giving the routers their own block:

    Host *.hamwan.net
        User myname+cet512w

(only if that pattern matches nothing but RouterOS devices that you manage with this role).
Setting `ansible_libssh_config_file` does not help: it is not passed through `network_cli`.

### The role checks this for you

Before anything else the role sends a long command that does nothing (`tasks/check_terminal.yml`)
and stops the play for the host if the echo comes back wrapped, with a message pointing here.
On RouterOS 7.24.2 this separates a correct login from one missing `+cet512w`.  One RouterOS
7.25 device (a CRS328) wrapped long input even with the correct login; if you have such a device
and accept that long set commands may misbehave, skip the check for it with
`routeros_require_wide_terminal: false` (host_vars) or `-e routeros_require_wide_terminal=false`.

### Host keys

libssh checks `~/.ssh/known_hosts` and ignores `ansible_ssh_args`, so the
`StrictHostKeyChecking=no` in `group_vars/os_routeros.yml` has no effect on routers.  A router you
have never connected to fails with "The authenticity of host ... can't be established".  Either:

- copy `.ansible.cfg` from the top of this repo to `~/.ansible.cfg` (or add its
  `[libssh_connection]` section to yours).  `host_key_auto_add = True` accepts and records a
  router's key without asking (stored as `[host]:222` in `~/.ssh/known_hosts`).  **It also
  accepts a key that has changed**, so it offers no protection against a swapped key - the same
  trade-off `StrictHostKeyChecking=no` was meant to make.  It can only be set in ansible.cfg or
  `ANSIBLE_LIBSSH_HOST_KEY_AUTO_ADD=True`, not as an inventory variable.  (The old
  `ansible_ssh_host_key_auto_add` in `vars/main.yml` had no effect and has been removed);
- or add routers yourself: `ssh-keyscan -p 222 router.hamwan.net >> ~/.ssh/known_hosts`;
- or, for a one-off run, `ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook ...`.

## SSH public keys for users

`manage_users.yml` keeps each user's SSH public key on the device in step with the master copy
`<base url><user>.key`.  For every user in `users_admin` + `users_user` it compares the
fingerprint of the master key with the fingerprint(s) the device reports in
`/user ssh-keys print detail`:

| Device state | Action |
|---|---|
| user has no key | key fetched and imported |
| key present, fingerprint matches master (SHA256 or MD5) | nothing |
| key present, fingerprint differs | master key imported, then the old key(s) removed |
| key present, device shows no fingerprint (older RouterOS) | per `routeros_ssh_key_unverifiable_action` |
| **admin** (`users_admin`): master key missing, unreadable, or more than one key in the file | **play stops for the host before anything is changed**; the error names each user and the reason |
| read-only user (`users_user`): master key missing, unreadable, or more than one key | nothing; reported (a new user is still created, without a key) |
| master key present, plus other keys | nothing (reported); with `routeros_ssh_keys_exclusive=true` the others are removed |

The new key is imported *before* the old one is removed, and the old one is only removed once the
key count has gone up and (where the device shows fingerprints) the master fingerprint is present.

Use `--check --diff` to see the plan without changing anything.

Tested live on RouterOS 7.25 (CRS328): install, replace after a master key change, exclusive
clean-up, idempotent re-runs, and connecting-user protection with `-u name+cet512w`.  Every print
the role parses uses `without-paging`; without it RouterOS stops at its pager prompt once output
passes the terminal height and the task times out.

Exclusive mode (`-e routeros_ssh_keys_exclusive=true`) makes the master key the only key each
managed user holds.  It re-imports the master key, checks it, then removes every older entry - the
same safe order as a replacement.  Users whose keys cannot be verified are never cleaned up.

New users are created with a random password that is not displayed (`no_log`); they log in with
their SSH key.

### Where the master keys come from

There is no built-in key site: each organisation sets its own.

| Variable | Default | Used by |
|---|---|---|
| `authorized_key_location` | none - set it in group_vars (HamWAN: `inventories/psdr/group_vars/owner_HamWAN.yml`) | both this role and the Linux `users` role |
| `routeros_ssh_key_base_url` | `authorized_key_location` | Ansible, to read and check the keys |
| `routeros_ssh_key_fetch_base_url` | `routeros_ssh_key_base_url` | the routers, to download the key (`/tool fetch`) |

Set `routeros_ssh_key_fetch_base_url` only if the routers reach the key server by a different
address than the Ansible host does (NAT, a management network).  The molecule tests do exactly
that: Ansible reads the keys at `http://127.0.0.1:<port>/` and the RouterOS VMs fetch them at
`http://10.0.2.2:<port>/`.  If no key source is configured the play stops before changing anything.

### Protecting the account Ansible connects as

The account Ansible logs in as is **never deleted** via `users_delete`, and there is no override:
to delete it, run the playbook logged in as a *different* admin.

Its SSH key is also left alone (not replaced, not cleaned up by exclusive mode) unless you pass:

    ansible-playbook psdr.yml -e routeros_allow_update_connecting_user=true

Make sure the new master key is one you hold before doing that.

The name is the one Ansible really logs in with, wherever it came from (`-u myname+cet512w` on
the command line, `ansible_user` in inventory, `remote_user` in ansible.cfg), minus the `+...`
suffix.  If it cannot be determined the play stops rather than guess; set
`routeros_connecting_user` in that case.  All variables are documented in `defaults/main.yml`.

## RouterOS 6

RouterOS 6 only offers old SSH algorithms that current libssh (this role's connection) does not
offer by default:

- **MAC:** RouterOS 6 has only `hmac-sha1`/`hmac-md5`.  Without help the connection fails with
  `kex error : no match for method mac algo ... server [hmac-sha1,hmac-md5]`.
- **Public-key signatures:** RouterOS 6 only accepts SHA-1 `ssh-rsa` signatures, so login with an
  RSA key fails (libssh then tries other keys, which can surface as an unrelated-looking error).

Both can be allowed for the RouterOS 6 devices only:

1. **MACs - an SSH client config drop-in** on the machine that runs Ansible.  libssh has no Ansible
   option for MACs, but it reads `~/.ssh/config` and `/etc/ssh/ssh_config` (which on Debian
   includes `/etc/ssh/ssh_config.d/*.conf`).  For example
   `/etc/ssh/ssh_config.d/routeros6-macs.conf`:

       # RouterOS 6 only offers hmac-sha1/hmac-md5; allow it for these hosts only.
       Host r6-a.example.net r6-b.example.net 192.0.2.17
           MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha2-256,hmac-sha2-512,hmac-sha1

   The `Host` names must match what Ansible connects to (`ansible_host`, or the inventory name).
   Don't put `User` lines in such a block: libssh lets them override `-u` (see "Logging in").
2. **Signatures - a host variable** (host_vars, or a group for your v6 devices):

       ansible_libssh_publickey_algorithms: ssh-rsa,rsa-sha2-256,rsa-sha2-512

Until you have done that, paramiko also works for v6 (`ansible_network_cli_ssh_type: paramiko`
plus `ansible_paramiko_use_rsa_sha2_algorithms: false`), but ansible-core deprecates its paramiko
connection plugin and will remove it in 2.21.

The molecule tests use the libssh settings for the `ros6.*` VMs (192.168.56.20-22) and check the
drop-in is present before converging; on the test host install:

    Host 192.168.56.20 192.168.56.21 192.168.56.22
        MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha2-256,hmac-sha2-512,hmac-sha1

## Testing

Three layers, fastest first:

- `python3 -I roles/routeros_common/tests/test_routeros_ssh_keys.py` (and
  `roles/hamwan_ssh_common/tests/test_ssh_keys.py`): unit tests for parsing RouterOS key listings
  and master key files.  Under a second.
- `python3 roles/routeros_common/tests/sim/run_sim.py`: runs the real `manage_users.yml` against a
  fake RouterOS device, about two minutes, no VMs.  It is the only automated test of SSH key
  *replacement*, which molecule does not exercise (its master keys never change during a run).
  See `tests/sim/README.md`.
- `molecule test` (from `roles/routeros_common`): real RouterOS 6 and 7 VMs under VirtualBox
  (box versions pinned in `molecule/default/Vagrantfile`: 6.49.19 and 7.22), described below.
  RouterOS 7.22 prints key fingerprints, so there molecule also checks keys match the master;
  RouterOS 6 does not, so its keys are reported as unverifiable.  See the top-level README for setting up Vagrant and VirtualBox.


We use molecule to drive automated testing using Vagrant and VirtualBox based routeros images.
Vagrant is going to build 6 RouterOS images.  Three each for RouterOS 6 and RouterOS 7.
Each is in a specific initial state for each of the settings we are going to test:

 - correct - the setting are already as we would expect.  No change should be applied.
 - incorrect - all the settings are present but wrong.  They should all be corrected.
 - missing - where possible, the setting are unset or missing.  They should be set or ignored (situationly dependent).

### References

The source for our routeros images:
https://github.com/cheretbe/packer-routeros/tree/master

Some useful description of using molecule and Vagrant for testing:
https://floatingpoint.sorint.it/blog/post/setting-up-molecule-for-testing-ansible-roles-with-vagrant-and-testinfra

Vagrant docs:
https://developer.hashicorp.com/vagrant/docs/providers/basic_usage
