# hamwan_ssh_common Role

Plugin-only role (no tasks) holding the SSH-key helpers shared by `routeros_common` and `users`.
Both list it under `dependencies:` in their `meta/main.yml`, which is all it takes for Ansible
to load these plugins for them.

| Plugin | Kind | Used for |
|---|---|---|
| `hamwan_connection_user` | action (controller only) | the login name Ansible really uses for the host (`-u`, `ansible_user`, `remote_user`), so that account can be protected |
| `ssh_pubkeys_info(text, max_keys=None)` | filter | check a master `<user>.key` file and fingerprint its keys.  RouterOS uses `max_keys=1`; Linux allows several |
| `ssh_key_ids(text)` | filter | compare two authorized_keys texts, ignoring comments and options |

RouterOS-specific parsing of `/user ssh-keys print` output stays in
`roles/routeros_common/filter_plugins/routeros_ssh_keys.py`.

Tests: `python3 -I roles/hamwan_ssh_common/tests/test_ssh_keys.py`

It must be on the roles path wherever the other two run.  For `psdr.yml` it is (`roles/` next to
the playbook); molecule normally adds the role's parent directory (`roles/`) to the roles path.
