# routeros_common Role

This role is designed to query various routeros settings and update or create them if they
do not match desired settings.  The configruation is split into two locations.
 - roles/routeros_common/vars/main.yml holds the description of each setting and how to change it.
 - group_vars/os_routeros.yml sets the site specific values used by the file above.
By putting the values in group_vars, the can be overriden where needed by entries in host_vars.

The molecule tests run it against RouterOS 6.49.19 and 7.22 (the box versions pinned in
`molecule/default/Vagrantfile`).  Earlier versions of the role were tested on 6.1-6.49.x and
7.1-7.16.

The user is expected to have SSH access to the devices.

## Logging in: the `+cet512w` suffix (read this first)

RouterOS takes terminal options from the login name: everything after a `+`.  This role needs
them: if your RouterOS user is `myname`, it must log in as **`myname+cet512w`**
(`c` no colours, `e` dumb terminal, `t` no terminal auto-detection, `512w` 512 columns wide).
Without them RouterOS wraps every input line longer than about 80 characters (prompt
included) and echoes it back in fragments.  The fragments end up in the output, so set
commands look as if they failed and settings never compare as correct; on every run the role
"fixes" settings that are already right, or fails.  More detail:
https://docs.ansible.com/projects/ansible/latest/network/user_guide/platform_routeros.html and
https://help.mikrotik.com/docs/spaces/ROS/pages/328134/Command+Line+Interface

**The role adds the options for you.**  Before it sends anything, it reads the login name
Ansible will use (from `-u`, `ansible_user` in inventory, or `remote_user` in ansible.cfg).  If
that name has no `+` part, it appends `+cet512w` and uses that for the rest of the play, so
this is enough:

    ansible-playbook psdr.yml -l R1.Example.hamwan.net -u myname --tags routeros --check --diff

A name that already has options (`-u myname+cet512w`) is used as it is.  The options added are
set by `routeros_login_options` (default `cet512w`; `''` turns this off).

Two things still beat it, and the wide-mode check below catches both:

- `-e ansible_user=myname` (extra vars outrank anything a role sets), or `ansible_user` given in
  `vars:` on an `include_role` task.  Include the options yourself there: `myname+cet512w`.
- a `User` line in `~/.ssh/config` (next section).

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
On RouterOS 7.24.2 this separates a correct login from one missing `+cet512w`.

**RouterOS 7.25 ignores the login options** (including its betas and release candidates), so
input wraps even with a correct `+cet512w` login.  MikroTik fixed this in 7.25.1 ("console - fix
custom SSH client login parameters being ignored (introduced in v7.25)").  Upgrade such routers
to 7.25.1 or later; the role names the bug in its error message when it finds 7.25.

If you cannot upgrade yet and accept that long set commands may be misread and re-applied on
every run, skip the check for that router with `routeros_require_wide_terminal: false`
(host_vars) or `-e routeros_require_wide_terminal=false`.  The role then prints a warning
instead of stopping.

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
