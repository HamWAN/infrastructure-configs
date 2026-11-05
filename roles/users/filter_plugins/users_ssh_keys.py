"""Filters for the users role: check a master authorized-keys file before installing it.

users_pubkeys_info
    Takes the text of a master <user>.key file and returns
      valid         True when the file holds at least one key and every key line decodes
      count         number of key lines (blank lines and '#' comments are ignored)
      key_lines     the key lines, as they will be written to authorized_keys
      fingerprints  SHA256 fingerprint of each key, as ssh-keygen -l prints it
      error         present when something is wrong
    Unlike RouterOS, Linux authorized_keys can hold several keys, so a file with more than one
    key is valid here.  A file with any line that is not a key is rejected as a whole, so a
    truncated or HTML error page is never installed.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import re

DOCUMENTATION = r"""
  name: users_ssh_keys
  short_description: Validate master SSH public key files for the users role
  version_added: "1.0"
"""

_KEY_TYPE = re.compile(r"^(ssh-[a-z0-9]+|ecdsa-sha2-\S+|sk-\S+)$")


def _as_text(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "\n".join(_as_text(v) for v in value)
    return str(value)


def users_pubkeys_info(text):
    lines = [
        ln.strip()
        for ln in _as_text(text).replace("\r", "\n").split("\n")
        if ln.strip() and not ln.lstrip().startswith("#")
    ]
    info = {"count": len(lines), "valid": False, "key_lines": [], "fingerprints": []}
    if not lines:
        info["error"] = "no public key found"
        return info
    for n, line in enumerate(lines, 1):
        fields = line.split()
        # authorized_keys options may come first: find the first token that is a key type
        idx = next((i for i, f in enumerate(fields) if _KEY_TYPE.match(f)), None)
        if idx is None or idx + 1 >= len(fields):
            info["error"] = "line %d does not look like an OpenSSH public key" % n
            return info
        try:
            blob = base64.b64decode(fields[idx + 1], validate=True)
        except (binascii.Error, ValueError):
            info["error"] = "line %d: key data is not valid base64" % n
            return info
        info["key_lines"].append(line)
        info["fingerprints"].append(
            "SHA256:" + base64.b64encode(hashlib.sha256(blob).digest()).decode("ascii").rstrip("="))
    info["valid"] = True
    return info


def users_key_ids(text):
    """The keys in an authorized_keys text, as sorted 'type base64' strings.

    Options and comments are ignored, so two files holding the same keys compare equal.  Lines
    that are not keys are skipped (this is for comparing, not validating).
    """
    ids = set()
    for line in _as_text(text).replace("\r", "\n").split("\n"):
        fields = line.strip().split()
        if not fields or fields[0].startswith("#"):
            continue
        idx = next((i for i, f in enumerate(fields) if _KEY_TYPE.match(f)), None)
        if idx is not None and idx + 1 < len(fields):
            ids.add(fields[idx] + " " + fields[idx + 1])
    return sorted(ids)


class FilterModule(object):
    def filters(self):
        return {"users_pubkeys_info": users_pubkeys_info, "users_key_ids": users_key_ids}
