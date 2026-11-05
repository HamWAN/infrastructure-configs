# users Role

Manages HamWAN accounts on Linux hosts (`psdr.yml`, hosts in `os_linux` and `owner_HamWAN`):

- groups `group_admin` (sudo, via `/etc/sudoers.d/<group_admin>`) and `group_user`;
- one account per name in `users_admin` (in `group_admin`) and `users_user` (in `group_user`);
- each account's `~/.ssh/authorized_keys`, set from the master key file
  `<authorized_key_location><user>.key` (https://monitoring.hamwan.net/keys/ in production);
- removal of members of those groups who are no longer listed (home directory included), and of
  groups recorded in `group_managed_scope` that are no longer used.

The user lists and key location live in `inventories/psdr/group_vars/owner_HamWAN.yml`, shared
with the RouterOS role.

## SSH keys

| Situation | Action |
|---|---|
| user's `authorized_keys` differs from the master file | replaced by exactly the master key(s): changed keys are updated, any other key is removed |
| master file holds several keys | all of them are installed (Linux allows several; RouterOS does not) |
| **admin** (`users_admin`) whose master file is missing, unreadable, or has a line that is not a key | **play stops for the host before anything is changed**; the error names each user and the reason |
| read-only user (`users_user`) with no usable master file | account still managed; its `authorized_keys` is left alone; reported |

A master file with any line that is not a key (for example an HTML error page) is rejected as a
whole, so a bad download is never installed.

Run with `--check --diff` to see what would change.  The play prints
`authorized_keys to be changed for: [...]`.

## The account Ansible logs in as

The account Ansible connects as (`-u`, `ansible_user` or `remote_user`):

- is **never removed**, even if it is no longer in the user lists.  There is no override: to
  remove it, run the playbook logged in as a *different* admin;
- has its `authorized_keys` **left alone** unless you pass
  `-e users_allow_update_connecting_user=true`.  The play reports if it differs from the master.
  Make sure the new master key is one you hold before allowing the update.

If the name cannot be determined the play stops; set `users_connecting_user` in that case.

## Variables

| Variable | Where | Meaning |
|---|---|---|
| `users_admin`, `users_user` | group_vars | account names |
| `group_admin`, `group_user`, `group_managed_scope` | group_vars | group names, scope file |
| `authorized_key_scheme` | group_vars | lookup used for master keys: `ansible.builtin.url` (production) or `ansible.builtin.file` (molecule) |
| `authorized_key_location` | group_vars | prefix of the master key files |
| `users_allow_update_connecting_user` | defaults (`false`) | allow updating the connecting account's keys |
| `users_connecting_user` | optional | override the detected connecting account |
| `test_flaky_network` | molecule | enables the "Kill Persistent SSH Connection" workaround |

## Testing

- `python3 -I roles/users/tests/test_users_ssh_keys.py` - unit tests for the key-file checks.
- `molecule test` (from `roles/users`) - three Vagrant VMs (see `Vagrantfile`), logged in as `eo`.
  Besides creating/removing users and groups, it checks that:
  - `tom` (multi-key `test_keys/tom.key`) ends up with exactly those keys, and a stray key is removed;
  - `eo`, the connecting account, keeps an extra key it already had;
  - an admin with no key file stops the play and is not created (`verify_protection.yml`);
  - `eo` is not removed when it is left out of `users_admin` (`verify_protection.yml`).
