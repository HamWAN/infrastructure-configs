"""Filter for reading the user list a RouterOS device prints.

routeros_user_names
    Takes the output of '/user print without-paging' (a string, or a list of lines) and returns
    the user names, in the order listed.

routeros_disabled_users
    The names of the accounts the same listing marks as disabled.  Which flag letter means
    disabled is read from the 'Flags:' legend the device prints ('Flags: X - DISABLED'), so a
    device that uses another letter is still read correctly; without a legend 'X' is assumed.

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
_NO_HEADER_ROW = re.compile(r"^\s*\d+\s+((?:[A-Z]\s+)*)(\S+)")
_LEGEND = re.compile(r"([A-Z])\s*-\s*([A-Za-z-]+)")


def _lines(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        out = []
        for v in value:
            out.extend(_lines(v))
        return out
    return str(value).replace("\r", "").split("\n")


def _rows(output):
    """(name, flag letters) for each row, plus the flag legend the device printed."""
    lines = _lines(output)
    col = None
    rows = []
    legend = {}
    for line in lines:
        if line.startswith("Flags:"):
            legend.update((f, m.lower()) for f, m in _LEGEND.findall(line[len("Flags:"):]))
            continue
        if col is None and _HEADER.match(line):
            col = line.index("NAME")
            continue
        if not line.strip() or ";;;" in line[: (col or 0) + 3] or line.lstrip().startswith(";;;"):
            continue
        if line.startswith("Columns:"):
            continue
        if col is None:
            m = _NO_HEADER_ROW.match(line)
            if m:
                rows.append((m.group(2), m.group(1).split()))
            continue
        # Everything before the NAME column must be a row number and flags (or blank, for a
        # RouterOS 6 row whose number is on the comment line above).
        if not re.match(r"^\s*\d*\s*(?:[A-Z]\s*)*$", line[:col]):
            continue
        rest = line[col:]
        if rest and not rest[0].isspace():
            rows.append((rest.split()[0], re.findall(r"[A-Z]", line[:col])))
    return rows, legend


def routeros_user_names(output):
    return [name for name, _flags in _rows(output)[0]]


def routeros_disabled_users(output):
    rows, legend = _rows(output)
    disabled = {f for f, meaning in legend.items() if meaning.startswith("disabl")} or {"X"}
    return [name for name, flags in rows if disabled.intersection(flags)]


class FilterModule(object):
    def filters(self):
        return {
            "routeros_user_names": routeros_user_names,
            "routeros_disabled_users": routeros_disabled_users,
        }
