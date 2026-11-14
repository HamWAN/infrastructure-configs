"""Filter for reading the user list a RouterOS device prints.

routeros_user_names
    Takes the output of '/user print without-paging' (a string, or a list of lines) and returns
    the user names, in the order listed.

RouterOS puts a flag column between the row number and the name (X disabled, E expired) and
only prints it when a flag is in use, so the name cannot be found by counting words: in
' 0 X admin  full' the second word is a flag, in ' 0 admin  full' it is the name.  The header
line (' #   NAME  GROUP ...') shows where the NAME column starts, so names are read from that
column.  Comment lines (';;; ...') are skipped, including RouterOS 6's form, where the comment
follows the row number and the name is on the next line.

Without a header line the name is taken as the first word after the row number and any
single-letter flags.
"""
from __future__ import annotations

import re

DOCUMENTATION = r"""
  name: routeros_users
  short_description: Parse RouterOS user listings
  version_added: "1.0"
"""

_HEADER = re.compile(r"^\s*#\s+NAME\b")
_NO_HEADER_ROW = re.compile(r"^\s*\d+\s+(?:[A-Z]\s+)*(\S+)")


def _lines(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        out = []
        for v in value:
            out.extend(_lines(v))
        return out
    return str(value).replace("\r", "").split("\n")


def routeros_user_names(output):
    lines = _lines(output)
    col = None
    names = []
    for line in lines:
        if col is None and _HEADER.match(line):
            col = line.index("NAME")
            continue
        if not line.strip() or ";;;" in line[: (col or 0) + 3] or line.lstrip().startswith(";;;"):
            continue
        if line.startswith(("Flags:", "Columns:")):
            continue
        if col is None:
            m = _NO_HEADER_ROW.match(line)
            if m:
                names.append(m.group(1))
            continue
        # Everything before the NAME column must be a row number and flags (or blank, for a
        # RouterOS 6 row whose number is on the comment line above).
        if not re.match(r"^\s*\d*\s*(?:[A-Z]\s*)*$", line[:col]):
            continue
        rest = line[col:]
        if rest and not rest[0].isspace():
            names.append(rest.split()[0])
    return names


class FilterModule(object):
    def filters(self):
        return {"routeros_user_names": routeros_user_names}
