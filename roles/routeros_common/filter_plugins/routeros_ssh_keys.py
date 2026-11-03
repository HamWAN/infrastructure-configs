"""Filters for comparing SSH public keys with what a RouterOS device reports.

routeros_ssh_pubkey_info
    Takes the text of a master .key file (OpenSSH public key format) and returns its type,
    SHA256 and MD5 fingerprints, computed the same way ssh-keygen -l does.

routeros_ssh_keys_parse
    Takes the output of '/user ssh-keys print detail' and returns, per user, the keys the device
    holds and any fingerprints it printed.

The parser is deliberately permissive: it does not depend on a property name.  It looks for
anything that has the shape of a SHA256 (SHA256:<base64>) or MD5 (aa:bb:...) fingerprint inside
each item.  An item that shows no fingerprint (e.g. RouterOS v6) yields an empty list, which the
calling tasks treat as "cannot verify" rather than "different".
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import re

DOCUMENTATION = r"""
  name: routeros_ssh_keys
  short_description: Fingerprint helpers for RouterOS SSH key management
  version_added: "1.0"
"""

_KEY_TYPE = re.compile(r"^(ssh-[a-z0-9]+|ecdsa-sha2-\S+|sk-\S+)$")
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


def _fingerprints_of_blob(blob: bytes) -> dict:
    sha = base64.b64encode(hashlib.sha256(blob).digest()).decode("ascii").rstrip("=")
    md5 = ":".join("{:02x}".format(b) for b in hashlib.md5(blob).digest())
    return {"sha256": "SHA256:" + sha, "md5": md5}


def routeros_ssh_pubkey_info(text):
    """Describe the public key(s) found in the text of a .key file.

    Returns a dict:
      count   number of key lines found (comments and blank lines are ignored)
      valid   True only when exactly one key line was found and it decodes
      line    the first key line (what gets imported)
      type, sha256, md5   for the first key line
      error   present when something is wrong
    """
    lines = [
        ln.strip()
        for ln in _as_text(text).replace("\r", "\n").split("\n")
        if ln.strip() and not ln.lstrip().startswith("#")
    ]
    info = {"count": len(lines), "valid": False}
    if not lines:
        info["error"] = "no public key found"
        return info
    info["line"] = lines[0]
    fields = lines[0].split()
    # tolerate leading authorized_keys options: find the first token that is a key type
    idx = next((i for i, f in enumerate(fields) if _KEY_TYPE.match(f)), None)
    if idx is None or idx + 1 >= len(fields):
        info["error"] = "line does not look like an OpenSSH public key"
        return info
    info["type"] = fields[idx]
    try:
        blob = base64.b64decode(fields[idx + 1], validate=True)
    except (binascii.Error, ValueError):
        info["error"] = "key data is not valid base64"
        return info
    info.update(_fingerprints_of_blob(blob))
    if len(lines) != 1:
        info["error"] = "%d keys in file; only one key per user is supported" % len(lines)
        return info
    info["valid"] = True
    return info


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
            "routeros_ssh_pubkey_info": routeros_ssh_pubkey_info,
            "routeros_ssh_keys_parse": routeros_ssh_keys_parse,
        }
