"""Filters for checking master SSH public key files, shared by routeros_common and users.

ssh_pubkeys_info(text, max_keys=None)
    Takes the text of a master <user>.key file (OpenSSH public key format) and returns
      count         number of key lines (blank lines and '#' comments are ignored)
      valid         True when there is at least one key, every key line decodes, and there are
                    no more than max_keys keys (no limit when max_keys is None)
      key_lines     the key lines, as they would be written to authorized_keys
      fingerprints  SHA256 fingerprint of each key, as ssh-keygen -l prints it
      md5s          MD5 fingerprint of each key (lower-case hex pairs)
      line, type, sha256, md5   the same for the first key, when there is one
      error         present when something is wrong
    A file with any line that is not a key is rejected as a whole, so a truncated download or an
    HTML error page is never installed.
    RouterOS calls this with max_keys=1 (one key per user); Linux allows several.

ssh_key_ids(text)
    The keys in an authorized_keys text as sorted 'type base64' strings.  Options and comments
    are ignored, so two files holding the same keys compare equal.  Lines that are not keys are
    skipped (this is for comparing, not validating).
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import re

DOCUMENTATION = r"""
  name: ssh_keys
  short_description: Validate and compare SSH public keys (HamWAN roles)
  version_added: "1.0"
"""

_KEY_TYPE = re.compile(r"^(ssh-[a-z0-9]+|ecdsa-sha2-\S+|sk-\S+)$")


def _as_text(value):
    """Accept a string, or a (possibly nested) list of strings, as Ansible hands them to us."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "\n".join(_as_text(v) for v in value)
    return str(value)


def _key_lines(text):
    return [
        ln.strip()
        for ln in _as_text(text).replace("\r", "\n").split("\n")
        if ln.strip() and not ln.lstrip().startswith("#")
    ]


def _split_key(line):
    """(type, base64) for an authorized_keys line, skipping any leading options; None if not a key."""
    fields = line.split()
    idx = next((i for i, f in enumerate(fields) if _KEY_TYPE.match(f)), None)
    if idx is None or idx + 1 >= len(fields):
        return None
    return fields[idx], fields[idx + 1]


def ssh_pubkeys_info(text, max_keys=None):
    lines = _key_lines(text)
    info = {"count": len(lines), "valid": False, "key_lines": [], "fingerprints": [], "md5s": []}
    if not lines:
        info["error"] = "no public key found"
        return info
    for n, line in enumerate(lines, 1):
        parts = _split_key(line)
        if parts is None:
            info["error"] = "line %d does not look like an OpenSSH public key" % n
            return info
        try:
            blob = base64.b64decode(parts[1], validate=True)
        except (binascii.Error, ValueError):
            info["error"] = "line %d: key data is not valid base64" % n
            return info
        info["key_lines"].append(line)
        info["fingerprints"].append(
            "SHA256:" + base64.b64encode(hashlib.sha256(blob).digest()).decode("ascii").rstrip("="))
        info["md5s"].append(":".join("{:02x}".format(b) for b in hashlib.md5(blob).digest()))
        if n == 1:
            info.update(line=line, type=parts[0], sha256=info["fingerprints"][0], md5=info["md5s"][0])
    if max_keys is not None and len(lines) > int(max_keys):
        info["error"] = ("%d keys in file; only one key per user is supported" % len(lines)
                         if int(max_keys) == 1 else
                         "%d keys in file; at most %d are supported" % (len(lines), int(max_keys)))
        return info
    info["valid"] = True
    return info


def ssh_key_ids(text):
    return sorted({"%s %s" % p for p in (_split_key(ln) for ln in _key_lines(text)) if p})


class FilterModule(object):
    def filters(self):
        return {"ssh_pubkeys_info": ssh_pubkeys_info, "ssh_key_ids": ssh_key_ids}
