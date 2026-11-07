"""Filter for reading what a RouterOS device reports about its SSH keys.

routeros_ssh_keys_parse
    Takes the output of '/user ssh-keys print detail' and returns, per user, the keys the device
    holds and any fingerprints it printed.

The parser is deliberately permissive: it does not depend on a property name.  It looks for
anything that has the shape of a SHA256 (SHA256:<base64>) or MD5 (aa:bb:...) fingerprint inside
each item.  An item that shows no fingerprint (e.g. RouterOS v6) yields an empty list, which the
calling tasks treat as "cannot verify" rather than "different".

Checking the master .key files is done by ssh_pubkeys_info (with max_keys=1) from the shared
roles/hamwan_ssh_common role.
"""
from __future__ import annotations

import re

DOCUMENTATION = r"""
  name: routeros_ssh_keys
  short_description: Parse RouterOS SSH key listings
  version_added: "1.0"
"""

_SHA256 = re.compile(r"SHA256:([A-Za-z0-9+/]{43})=?")
_MD5 = re.compile(r"(?<![0-9A-Fa-f:])((?:[0-9A-Fa-f]{2}:){15}[0-9A-Fa-f]{2})(?![0-9A-Fa-f:])")
_ITEM_START = re.compile(r"(?m)^[ \t]*\d+[ \t]+")
_USER = re.compile(r'(?<!\S)user=(?:"([^"]*)"|(\S+))')
_TYPE = re.compile(r"(?<!\S)key-type=(\S+)")
_BITS = re.compile(r"(?<!\S)bits=(\d+)")


def _as_text(value):
    """Accept a string, or a (possibly nested) list of strings, as Ansible hands them to us."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "\n".join(_as_text(v) for v in value)
    return str(value)


def routeros_ssh_keys_parse(output):
    """Parse '/user ssh-keys print detail' output.

    Returns {username: [ {"fingerprints": [...], "type": str|None, "bits": str|None}, ... ]}.
    Fingerprints are normalised: SHA256 as 'SHA256:<unpadded base64>', MD5 as lower-case hex pairs.
    Users with no keys do not appear.
    """
    text = _as_text(output)
    starts = [m.start() for m in _ITEM_START.finditer(text)]
    result = {}
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(text)
        chunk = text[start:end]
        um = _USER.search(chunk)
        if not um:
            continue
        user = um.group(1) if um.group(1) is not None else um.group(2)
        fps = ["SHA256:" + m.group(1) for m in _SHA256.finditer(chunk)]
        fps += [m.group(1).lower() for m in _MD5.finditer(chunk)]
        tm, bm = _TYPE.search(chunk), _BITS.search(chunk)
        result.setdefault(user, []).append(
            {"fingerprints": fps, "type": tm.group(1) if tm else None, "bits": bm.group(1) if bm else None}
        )
    return result


class FilterModule(object):
    def filters(self):
        return {
            "routeros_ssh_keys_parse": routeros_ssh_keys_parse,
        }
