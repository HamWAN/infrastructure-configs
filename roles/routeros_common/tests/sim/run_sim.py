#!/usr/bin/env python3
"""End-to-end simulation of roles/routeros_common/tasks/manage_users.yml against a fake device.

Usage (from anywhere, with the Python that has ansible-core and cryptography, e.g. the venv):
    python3 roles/routeros_common/tests/sim/run_sim.py [<repo clone> [<scratch dir>]]
The repo defaults to the clone this file is in; the scratch dir to a new temporary directory.
Exit status 0 when every check passes.  See README.md next to this file.

It starts a local HTTP server for the 'master' key files, builds a fake RouterOS state, runs the
real task files through ansible-playbook with a stand-in community.routeros.command module, and
checks the resulting device state for each scenario.  See the caveat at the top of the fake module.
"""
import copy
import functools
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "..", ".."))
WORK = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix="routeros-sim-"))
BIN = os.path.dirname(sys.executable)
# ansible-playbook from the same environment as this Python (a venv), else from PATH
AP = os.path.join(BIN, "ansible-playbook")
if not os.path.exists(AP):
    AP = shutil.which("ansible-playbook") or AP
os.makedirs(WORK, exist_ok=True)
KEYDIR = os.path.join(WORK, "keys")
shutil.rmtree(KEYDIR, ignore_errors=True)
os.makedirs(KEYDIR)


def newkey(tag):
    k = ed25519.Ed25519PrivateKey.generate()
    pub = k.public_key().public_bytes(serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH)
    return pub.decode() + " " + tag


def publish(user, line):
    with open(os.path.join(KEYDIR, user + ".key"), "w") as fh:
        fh.write(line + "\n")


# ---- local "monitoring.hamwan.net" -----------------------------------------------------
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=KEYDIR))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:%d/keys/" % srv.server_address[1]
os.symlink(KEYDIR, os.path.join(WORK, "keys_alias")) if not os.path.exists(os.path.join(WORK, "keys_alias")) else None
# serve at /keys/<user>.key
KEYROOT = os.path.join(WORK, "root")
shutil.rmtree(KEYROOT, ignore_errors=True)
os.makedirs(KEYROOT)
os.symlink(KEYDIR, os.path.join(KEYROOT, "keys"))
srv.shutdown()
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=KEYROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:%d/keys/" % srv.server_address[1]

MASTER = {u: newkey(u + "@master") for u in ("tom", "alice", "bob", "monitoring")}
OLD = {u: newkey(u + "@old") for u in ("tom", "alice")}


def reset_master():
    for u, line in MASTER.items():
        publish(u, line)


def initial_state():
    return {
        "users": [{"name": n, "group": g} for n, g in
                  [("admin", "full"), ("tom", "full"), ("alice", "full"), ("monitoring", "read"), ("olduser", "full")]],
        "keys": [
            {"id": "*1", "user": "tom", "line": MASTER["tom"]},
            {"id": "*2", "user": "alice", "line": OLD["alice"]},
            {"id": "*3", "user": "monitoring", "line": MASTER["monitoring"]},
        ],
        "files": {},
        "next_id": 3,
    }


PLAYBOOK = os.path.join(WORK, "sim_play.yml")
with open(PLAYBOOK, "w") as fh:
    fh.write("""---
- hosts: localhost
  gather_facts: false
  tasks:
    - ansible.builtin.include_role:
        name: routeros_common
        tasks_from: manage_users
""")

STATE = os.path.join(WORK, "device.json")


def run(state, extra=None, env=None, check=False, ansible_user="tom+cet512w", cli_user=None, verbose=False):
    with open(STATE, "w") as fh:
        json.dump(state, fh)
    ev = {
        "ansible_connection": "local",
        "ansible_python_interpreter": sys.executable,
        "users_admin": ["tom", "alice", "bob"],
        "users_user": ["monitoring"],
        "users_delete": ["olduser"],
        "routeros_ssh_key_base_url": BASE,
    }
    if ansible_user:
        ev["ansible_user"] = ansible_user
    ev.update(extra or {})
    e = dict(os.environ)
    e.update({
        "ANSIBLE_COLLECTIONS_PATH": os.path.join(HERE, "collections"),
        "ANSIBLE_ROLES_PATH": os.path.join(REPO, "roles"),
        "ANSIBLE_LOCALHOST_WARNING": "False",
        "ANSIBLE_INVENTORY_UNPARSED_WARNING": "False",
        "ANSIBLE_NOCOLOR": "1",
        "ANSIBLE_FORCE_COLOR": "0",
        "FAKE_ROS_STATE": STATE,
        "PATH": BIN + os.pathsep + e["PATH"],
    })
    e.update(env or {})
    cmd = [AP, "-i", "localhost,", PLAYBOOK, "-e", json.dumps(ev)]
    if check:
        cmd.append("--check")
    if cli_user:
        cmd += ["-u", cli_user]
    if verbose:
        cmd.append("-v")
    p = subprocess.run(cmd, capture_output=True, text=True, env=e, cwd=WORK)
    with open(STATE) as fh:
        after = json.load(fh)
    return p, after


def keyfor(st, user):
    return sorted(k["line"] for k in st["keys"] if k["user"] == user)


results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "   <-- " + detail))


def names(st):
    return sorted(u["name"] for u in st["users"])


# ---------------------------------------------------------------------------------------
reset_master()
print("== 1. normal run, connected as tom ==")
st0 = initial_state()
p, st1 = run(st0)
check("playbook succeeds", p.returncode == 0, p.stdout[-2500:] + p.stderr[-1500:])
check("bob created", "bob" in names(st1))
check("bob has master key (new user got key)", keyfor(st1, "bob") == [MASTER["bob"]])
check("alice stale key replaced by master, old one gone", keyfor(st1, "alice") == [MASTER["alice"]])
check("monitoring untouched (same key id)", [k["id"] for k in st1["keys"] if k["user"] == "monitoring"] == ["*3"])
check("tom untouched", [k["id"] for k in st1["keys"] if k["user"] == "tom"] == ["*1"])
check("olduser deleted", "olduser" not in names(st1))
check("downloaded key files cleaned up", st1["files"] == {}, str(st1["files"]))

print("== 2. second run is a no-op (idempotent) ==")
p, st2 = run(st1)
check("playbook succeeds", p.returncode == 0, p.stdout[-2500:])
check("no keys imported again", st2["next_id"] == st1["next_id"], "%s -> %s" % (st1["next_id"], st2["next_id"]))
check("device unchanged", st2 == st1)

print("== 3. master key for the CONNECTING user changes ==")
tom_new = newkey("tom@new")
publish("tom", tom_new)
st = copy.deepcopy(st1)
p, st3 = run(st)
check("default: playbook succeeds", p.returncode == 0, p.stdout[-2000:])
check("default: tom's key NOT replaced (protected)", keyfor(st3, "tom") == [MASTER["tom"]])
check("default: says how to allow it", "routeros_allow_update_connecting_user=true" in p.stdout)
p, st3b = run(st, extra={"routeros_allow_update_connecting_user": True})
check("flag: tom's key replaced", keyfor(st3b, "tom") == [tom_new], p.stdout[-2000:])
check("flag: only one key left for tom", len(keyfor(st3b, "tom")) == 1)
reset_master()

print("== 4. another user's master key changes (tom is connecting) ==")
alice_new = newkey("alice@new")
publish("alice", alice_new)
p, st4 = run(copy.deepcopy(st1))
check("alice updated to the new master key", keyfor(st4, "alice") == [alice_new], p.stdout[-2000:])
reset_master()

print("== 5. check mode changes nothing ==")
p, st5 = run(initial_state(), check=True)
check("check mode succeeds", p.returncode == 0, p.stdout[-2500:] + p.stderr[-800:])
check("device state identical to start", st5 == initial_state())
check("check mode reports the plan", "SSH keys to replace" in p.stdout and "alice" in p.stdout)

print("== 6. device that shows no fingerprints (e.g. RouterOS 6) ==")
st = copy.deepcopy(st1)
st["keys"] = [k if k["user"] != "alice" else dict(k, line=OLD["alice"]) for k in st["keys"]]
p, st6 = run(copy.deepcopy(st), env={"FAKE_ROS_NO_FINGERPRINT": "1"})
check("default: succeeds", p.returncode == 0, p.stdout[-2000:])
check("default: key left alone", keyfor(st6, "alice") == [OLD["alice"]])
check("default: tells you it could not check", "NOT checked" in p.stdout)
p, st6b = run(copy.deepcopy(st), env={"FAKE_ROS_NO_FINGERPRINT": "1"}, extra={"routeros_ssh_key_unverifiable_action": "replace"})
check("replace: alice re-imported with master", keyfor(st6b, "alice") == [MASTER["alice"]], p.stdout[-2000:])

print("== 7. connecting user listed in users_delete: never deleted, flag or not ==")
p, st7 = run(copy.deepcopy(st1), extra={"users_delete": ["tom"]})
check("tom NOT deleted", "tom" in names(st7), p.stdout[-1500:])
check("warns, says to use a different admin", "NOT deleting" in p.stdout and "different admin" in p.stdout)
p, st7b = run(copy.deepcopy(st1), extra={"users_delete": ["tom"], "routeros_allow_update_connecting_user": True})
check("with key-update flag: tom still NOT deleted", "tom" in names(st7b), p.stdout[-1500:])
p, st7c = run(copy.deepcopy(st1), extra={"users_delete": ["tom", "alice"], "users_admin": ["tom", "bob"]})
check("other users in users_delete still deleted", "alice" not in names(st7c) and "tom" in names(st7c))

print("== 8. connecting user derived from configured remote_user when ansible_user unset ==")
publish("tom", tom_new)
p, st8 = run(copy.deepcopy(st1), env={"ANSIBLE_REMOTE_USER": "tom"}, ansible_user=None)
check("tom still protected", keyfor(st8, "tom") == [MASTER["tom"]], p.stdout[-2000:])
reset_master()

print("== 9. import silently fails: old key must survive ==")
st = copy.deepcopy(st1)
st["keys"] = [k if k["user"] != "alice" else dict(k, line=OLD["alice"]) for k in st["keys"]]
p, st9 = run(st, env={"FAKE_ROS_IMPORT_NOOP": "1"})
check("playbook fails loudly", p.returncode != 0)
check("alice keeps her old key", keyfor(st9, "alice") == [OLD["alice"]])

print("== 10. master key unavailable (404) for an ADMIN who has a key: stop, change nothing ==")
os.remove(os.path.join(KEYDIR, "alice.key"))
st = copy.deepcopy(st1)
st["keys"] = [k if k["user"] != "alice" else dict(k, line=OLD["alice"]) for k in st["keys"]]
st["users"].append({"name": "dave", "group": "full"})
p, st10 = run(copy.deepcopy(st), extra={"users_delete": ["olduser", "dave"]})
check("play fails", p.returncode != 0)
check("says which admin and why", "No usable SSH public key for admin user(s): alice" in p.stdout, p.stdout[-2000:])
check("device completely unchanged (no adds, keys or deletes)", st10 == st)
p, st10c = run(copy.deepcopy(st), check=True)
check("check mode fails the same way", p.returncode != 0 and "alice" in p.stdout)
reset_master()

print("== 10b. admin's key file holds two keys: stop ==")
publish("alice", MASTER["alice"] + "\n" + newkey("alice@other"))
p, st10b = run(copy.deepcopy(st1))
check("play fails", p.returncode != 0)
check("reason given", "2 keys in file" in p.stdout, p.stdout[-1500:])
check("device unchanged", st10b == st1)
reset_master()

print("== 10c. read-only user (users_user) with key but no master: reported, run continues ==")
os.remove(os.path.join(KEYDIR, "monitoring.key"))
p, st10d = run(copy.deepcopy(st1))
check("succeeds", p.returncode == 0, p.stdout[-2000:])
check("monitoring untouched", [k["id"] for k in st10d["keys"] if k["user"] == "monitoring"] == ["*3"])
check("reported as unusable master", "no usable master key (missing, unreadable or more than one): ['monitoring']" in p.stdout)
reset_master()

print("== 11. connecting user given only by -u on the command line ==")
publish("tom", tom_new)
p, st11 = run(copy.deepcopy(st1), ansible_user=None, cli_user="tom+cet512w", env={"USER": "somebodyelse"})
check("succeeds", p.returncode == 0, p.stdout[-2000:])
check("tom protected (from -u, not $USER)", keyfor(st11, "tom") == [MASTER["tom"]], p.stdout[-2000:])
check("reports tom as protected", "Account Ansible is connected as: tom." in p.stdout,
      p.stdout[-2000:])
reset_master()

print("== 12. exclusive mode ==")
EXTRA = newkey("alice@laptop")
st = copy.deepcopy(st1)
st["next_id"] += 1
st["keys"].append({"id": "*%X" % st["next_id"], "user": "alice", "line": EXTRA})
st["next_id"] += 1
st["keys"].append({"id": "*%X" % st["next_id"], "user": "tom", "line": newkey("tom@laptop")})
p, st12 = run(copy.deepcopy(st))
check("default: succeeds", p.returncode == 0, p.stdout[-2000:])
check("default: alice keeps both keys", keyfor(st12, "alice") == sorted([MASTER["alice"], EXTRA]))
check("default: reported", "extra keys" in p.stdout and "left alone" in p.stdout)
p, st12c = run(copy.deepcopy(st), extra={"routeros_ssh_keys_exclusive": True}, check=True)
check("exclusive check mode: nothing changed", p.returncode == 0 and st12c == st, p.stdout[-2000:])
p, st12b = run(copy.deepcopy(st), extra={"routeros_ssh_keys_exclusive": True})
check("exclusive: succeeds", p.returncode == 0, p.stdout[-2500:])
check("exclusive: alice has only the master key", keyfor(st12b, "alice") == [MASTER["alice"]], str(keyfor(st12b, "alice")))
check("exclusive: protected tom keeps both keys", len(keyfor(st12b, "tom")) == 2)
check("exclusive: users without extras untouched",
      [k["id"] for k in st12b["keys"] if k["user"] == "monitoring"] == ["*3"])
p, st12d = run(copy.deepcopy(st12b), extra={"routeros_ssh_keys_exclusive": True})
check("exclusive: second run changes nothing", st12d == st12b)

print("== 13. new-user password is not shown ==")
p, st13 = run(initial_state(), verbose=True)
check("succeeds", p.returncode == 0, p.stdout[-2000:])
check("password task censored", "censored" in p.stdout)
check("no password in output", 'password="' not in p.stdout and "random_password\": \"" not in p.stdout,
      p.stdout[-2000:])

print("== 14. ADMIN listed with no master key and no key on the device: stop before any change ==")
ev14 = {"users_admin": ["tom", "alice", "bob", "carol"], "users_delete": ["olduser", "dave"]}
base14 = copy.deepcopy(st1)
base14["users"].append({"name": "dave", "group": "full"})
p, st14 = run(copy.deepcopy(base14), extra=ev14, check=True)
check("check mode fails", p.returncode != 0)
check("check mode names carol", "No usable SSH public key for admin user(s): carol" in p.stdout, p.stdout[-2000:])
p, st14b = run(copy.deepcopy(base14), extra=ev14)
check("play fails", p.returncode != 0)
check("carol NOT created, nothing changed", st14b == base14)

print("== 14b. read-only user with no master key and no key on the device: created keyless ==")
ev14b = {"users_user": ["monitoring", "carol"], "users_delete": ["olduser", "dave"]}
p, st14c = run(copy.deepcopy(base14), extra=ev14b)
check("succeeds", p.returncode == 0, p.stdout[-2500:])
check("carol created read-only, no key",
      {"name": "carol", "group": "read"} in st14c["users"] and keyfor(st14c, "carol") == [])
check("later tasks still ran (users_delete applied)", "dave" not in names(st14c))
check("no stray key file left", st14c["files"] == {}, str(st14c["files"]))
p, st14d = run(copy.deepcopy(st14c), extra=ev14b)
check("rerun changes nothing", st14d == st14c)

print("== 15. session not in wide mode (login options lost) ==")
p, st15 = run(copy.deepcopy(initial_state()), env={"FAKE_ROS_NARROW": "1"})
check("play fails", p.returncode != 0)
check("explains the +cet512w / ~/.ssh/config cause", "not in wide mode" in p.stdout and "~/.ssh/config" in p.stdout,
      p.stdout[-1500:])
check("device unchanged", st15 == initial_state())
p, st15c = run(copy.deepcopy(initial_state()), env={"FAKE_ROS_NARROW": "1"}, check=True)
check("check mode fails too", p.returncode != 0)
p, st15b = run(copy.deepcopy(initial_state()), env={"FAKE_ROS_NARROW": "1"},
               extra={"routeros_require_wide_terminal": False})
check("override: play runs", p.returncode == 0, p.stdout[-1500:])

print()
bad = [n for n, ok in results if not ok]
print("%d checks, %d failed" % (len(results), len(bad)))
sys.exit(1 if bad else 0)
