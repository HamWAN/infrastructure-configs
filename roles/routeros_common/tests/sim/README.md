# RouterOS user / SSH-key simulator

A fast, VM-free test of `tasks/manage_users.yml` (users, SSH keys, protections) against a
**fake RouterOS device**.  It runs in about two minutes and needs nothing but Python.

It is *not* required by the unit tests or by molecule; it complements them.

## Why it exists

The molecule scenario boots real RouterOS VMs (6.49.19 and 7.22).  It checks that users get their
keys and, on RouterOS 7, that the keys match the master by fingerprint (RouterOS 6 prints no key
fingerprints, so there the role treats keys as unverifiable).  But the master keys never change
during a molecule run, so molecule never exercises **key replacement** (a master key changed:
import the new key, verify it, then remove the old one), nor the failure paths around it.  Without
this simulator those would only be covered by testing by hand against a real router.

| Covered here | Unit tests | Simulator | Molecule (real VMs) |
|---|---|---|---|
| Key-file parsing, fingerprints | yes | via the role | via the role (fingerprints on RouterOS 7 only) |
| New users get keys | | yes | yes |
| Changed master key replaced, old key removed only after the new one verifies | | **yes** | no (keys never change during a run) |
| Import that silently adds nothing: old key kept, play fails | | **yes** | no |
| Devices without fingerprints (`routeros_ssh_key_unverifiable_action` skip / replace) | | yes | skip only |
| Exclusive mode, check mode changes nothing, idempotence | | yes | idempotence |
| Connecting account: never deleted, key only updated with the flag, found from `-u` | | yes | partly |
| Admin without a key file stops before any change; read-only user only reported | | yes | |
| New-user password never shown | | yes | |
| Session not in wide mode is caught | | yes | |
| Real RouterOS command syntax and output, real SSH, real `/tool fetch` | | **no** | yes |

## How it works

- `collections/ansible_collections/community/routeros/plugins/modules/command.py` is a stand-in
  for `community.routeros.command`.  Instead of talking to a router it keeps a pretend RouterOS
  state (users, SSH keys with ids, downloaded files) in a JSON file and answers exactly the
  commands the role sends (`/user print without-paging`, `/user ssh-keys print detail ...`,
  `:put [/user ssh-keys find ...]`, `/tool fetch`, `/user ssh-keys import`, `remove *N`, the
  wide-mode probe, ...).  In check mode it refuses any command that would change something.
- `run_sim.py` starts a local web server for the master `<user>.key` files, builds a device state,
  runs the real role tasks with `ansible-playbook` (connection `local`, the fake collection first
  on `ANSIBLE_COLLECTIONS_PATH`), and checks the resulting state.  Scenarios include 1-15:
  normal run and idempotence, the connecting user's key changing (default and with
  `routeros_allow_update_connecting_user`), another user's key changing, check mode, devices
  without fingerprints, the connecting user in `users_delete`, `remote_user` / `-u` detection,
  silent import failure, missing / multi-key / read-only master keys, exclusive mode, hidden
  password, admin without a key file, and a session that is not in wide mode.
- Behaviour switches for the fake device (environment variables): `FAKE_ROS_NO_FINGERPRINT=1`,
  `FAKE_ROS_IMPORT_NOOP=1`, `FAKE_ROS_NARROW=1`.

The fake collection is only used when `run_sim.py` points `ANSIBLE_COLLECTIONS_PATH` at it; it does
not affect normal playbook runs.

## Running it

From the repo root, with the Python environment that has Ansible (e.g. the project venv):

    python3 roles/routeros_common/tests/sim/run_sim.py

Optional arguments: `run_sim.py [<repo clone> [<scratch dir>]]`.  It needs `ansible-core` and
`cryptography` (both come with Ansible).  It prints PASS/FAIL per check and ends with
`N checks, M failed`; the exit status is non-zero if anything failed.  Run it before the slower
molecule test whenever `manage_users.yml`, `install_ssh_key.yml`, `ssh_key_plan.yml`,
`check_terminal.yml` or the shared `hamwan_ssh_common` plugins change.

## Keeping it in step with the role

The fake module only understands the commands it was taught, using the syntax and output format
believed to be RouterOS's.  **When the role starts sending a new or changed RouterOS command, add
or update the matching branch in `command.py`** (an unknown command fails with
`bad command name: ...`).  The simulator proves the role's logic, not RouterOS's behaviour:
molecule and testing against a real router cover that.
