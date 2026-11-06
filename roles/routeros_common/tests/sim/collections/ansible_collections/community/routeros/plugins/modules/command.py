#!/usr/bin/python
# SIMULATION ONLY.  A stand-in for community.routeros.command that pretends to be a RouterOS
# device, so the role's task flow can be exercised without a router.  It implements only the
# commands the role issues, using the syntax *I believe* RouterOS uses; it proves the Ansible
# logic, NOT that real RouterOS accepts these commands or prints this output.
#
# State lives in a JSON file named by $FAKE_ROS_STATE.  Behaviour switches (env vars):
#   FAKE_ROS_NO_FINGERPRINT=1   print ssh-keys without a fingerprint (like an old RouterOS)
#   FAKE_ROS_IMPORT_NOOP=1      'import' silently adds nothing
#   FAKE_ROS_NARROW=1           session not in wide mode: long input is echoed back wrapped
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import urllib.request

from ansible.module_utils.basic import AnsibleModule


def fps(line):
    blob = base64.b64decode(line.split()[1])
    sha = "SHA256:" + base64.b64encode(hashlib.sha256(blob).digest()).decode().rstrip("=")
    return sha


def load(path):
    with open(path) as fh:
        return json.load(fh)


def save(path, st):
    with open(path, "w") as fh:
        json.dump(st, fh, indent=1)


def run(cmd, st):
    c = cmd.strip()
    nofp = os.environ.get("FAKE_ROS_NO_FINGERPRINT") == "1"
    keys = st["keys"]

    if c == "/user print without-paging":
        rows = ["Flags: X - disabled", " #   NAME      GROUP   ADDRESS   LAST-LOGGED-IN"]
        for i, u in enumerate(st["users"]):
            rows.append(" %d   %-9s %-7s" % (i, u["name"], u["group"]))
        return "\n".join(rows)

    m = re.match(r'/user add name=(\S+) group=(\S+) password="(.*)"$', c)
    if m:
        st["users"].append({"name": m.group(1), "group": m.group(2)})
        return ""

    # wide-mode probe from tasks/check_terminal.yml: silent in wide mode, wrapped echo if narrow
    if c.startswith(":local routerosCommonWideModeCheck "):
        if os.environ.get("FAKE_ROS_NARROW") == "1":
            return c[:54] + "\n<" + c[20:60] + "\n<" + c[20:]
        return ""

    if c == "/console clear-history":
        return ""

    m = re.match(r"/user remove \[find name=(\S+)\]$", c)
    if m:
        st["users"] = [u for u in st["users"] if u["name"] != m.group(1)]
        return ""

    m = re.match(r'/user ssh-keys print detail without-paging(?: where user="(\S+)")?$', c)
    if m:
        rows = []
        n = 0
        for k in keys:
            if m.group(1) and k["user"] != m.group(1):
                continue
            row = " %d user=%s key-type=ed25519 bits=256" % (n, k["user"])
            if not nofp:
                row += '\n   fingerprint="%s"' % fps(k["line"])
            rows.append(row)
            n += 1
        return "\n\n".join(rows)

    m = re.match(r':put \[/user ssh-keys find user="(\S+)"\]$', c)
    if m:
        return ";".join(k["id"] for k in keys if k["user"] == m.group(1))

    m = re.match(r':put \[:len \[/user ssh-keys find user="(\S+)"\]\]$', c)
    if m:
        return str(len([k for k in keys if k["user"] == m.group(1)]))

    m = re.match(r'/file remove \[find name="(\S+)"\]$', c)
    if m:
        st["files"].pop(m.group(1), None)
        return ""

    m = re.match(r'/tool fetch url="(\S+)"$', c)
    if m:
        url = m.group(1)
        try:
            body = urllib.request.urlopen(url, timeout=5).read().decode()
        except Exception as e:  # noqa: BLE001
            return "failure: %s" % e
        st["files"][url.rsplit("/", 1)[1]] = body
        return "status: finished"

    m = re.match(r"/user ssh-keys import public-key-file=(\S+) user=(\S+)$", c)
    if m:
        if os.environ.get("FAKE_ROS_IMPORT_NOOP") == "1":
            return ""
        body = st["files"].get(m.group(1))
        if body is None:
            return "failure: no such file"
        st["next_id"] += 1
        keys.append({"id": "*%X" % st["next_id"], "user": m.group(2), "line": body.strip().splitlines()[0]})
        return ""

    m = re.match(r"/user ssh-keys remove (\*[0-9A-Fa-f]+)$", c)
    if m:
        st["keys"] = [k for k in keys if k["id"] != m.group(1)]
        return ""

    return "bad command name: %s" % c


def main():
    module = AnsibleModule(argument_spec=dict(commands=dict(type="list", elements="raw", required=True)),
                           supports_check_mode=True)
    path = os.environ["FAKE_ROS_STATE"]
    st = load(path)
    out = []
    for cmd in module.params["commands"]:
        res = run(str(cmd), st)
        if res.startswith(("failure:", "bad command name")):
            module.fail_json(msg=res, stdout=out)
        out.append(res)
        # a real device would never be changed by a command in check mode; fail loudly if the role tries
        if module.check_mode and not str(cmd).strip().startswith(("/user print", "/user ssh-keys print", ":put", ":local routerosCommonWideModeCheck")):
            module.fail_json(msg="mutating command issued in check mode: %s" % cmd)
    if not module.check_mode:
        save(path, st)
    module.exit_json(changed=True, stdout=out, stdout_lines=[o.splitlines() for o in out])


if __name__ == "__main__":
    main()
