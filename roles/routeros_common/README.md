# routeros_common Role

This role is designed to query various routeros settings and update or create them if they
do not match desired settings.  The configruation is split into two locations.
 - roles/routeros_common/vars/main.yml holds the description of each setting and how to change it.
 - group_vars/os_routeros.yml sets the site specific values used by the file above.
By putting the values in group_vars, the can be overriden where needed by entries in host_vars.

It is currently tested against routeros versions up to 6.1-6.49.x and 7.1-7.16.

The user is expected to have SSH access to the devices.

NOTE: Due to the way RouterOS echos characters back on the SSH session, you will need to change
the ansible remote username when using this role against RouterOS devices. If your username is
"myname", then you will need to set the ansible remote user to "myname+cet512w". The "+cet512w"
sets some terminal options for the ssh session to ensure anssible can parse the output successfully.
This is explained in some more detail here:
https://docs.ansible.com/projects/ansible/latest/network/user_guide/platform_routeros.html
and here: https://help.mikrotik.com/docs/spaces/ROS/pages/328134/Command+Line+Interface

## SSH public keys for users

`manage_users.yml` keeps each user's SSH public key on the device in step with the master copy
(`<authorized_key_location><user>.key`, default https://monitoring.hamwan.net/keys/).  For every
user in `users_admin` + `users_user` it compares the fingerprint of the master key with the
fingerprint(s) the device reports in `/user ssh-keys print detail`:

| Device state | Action |
|---|---|
| user has no key | key fetched and imported |
| key present, fingerprint matches master (SHA256 or MD5) | nothing |
| key present, fingerprint differs | master key imported, then the old key(s) removed |
| key present, device shows no fingerprint (older RouterOS) | per `routeros_ssh_key_unverifiable_action` |
| master key missing, unreadable, or more than one key in the file | nothing; reported |
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

### Protecting the account Ansible connects as

The account Ansible logs in as is **not**
changed - its key is not replaced, it is not cleaned up by exclusive mode, and it is not deleted
via `users_delete` - unless you pass:

    ansible-playbook psdr.yml -e routeros_allow_update_connecting_user=true

The name is the one Ansible really logs in with, wherever it came from (`-u myname+cet512w` on
the command line, `ansible_user` in inventory, `remote_user` in ansible.cfg), minus the `+...`
suffix.  If it cannot be determined the play stops rather than guess; set
`routeros_connecting_user` in that case.  All variables are documented in `defaults/main.yml`.

## Testing

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
