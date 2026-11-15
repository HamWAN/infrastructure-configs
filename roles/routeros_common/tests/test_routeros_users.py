"""Unit tests for filter_plugins/routeros_users.py.

Run from anywhere:   python3 -I roles/routeros_common/tests/test_routeros_users.py

The V7_* listings are real '/user print without-paging' output from RouterOS 7 routers (names
kept, times shortened).  V6_STYLE follows the RouterOS 6 layout.
"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "routeros_users", os.path.join(HERE, "..", "filter_plugins", "routeros_users.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# No flag in use: no flag column.
V7_PLAIN = [
    "Columns: NAME, GROUP, LAST-LOGGED-IN, INACTIVITY-POLICY",
    " # NAME         GROUP  LAST-LOGGED-IN       INACTIVITY-POLICY",
    " 0 eo           full                        none             ",
    " 1 NQ1E         full                        none             ",
    " 9 ve7alb       full                        none             ",
    "10 kennyr       full                        none             ",
    "11 monitoring   read   2026-11-13 04:32:36  none             ",
    "15 KK7LZM       full                        none",
]

# The built-in admin account is disabled: flag column, X in front of the name, and a comment.
V7_DISABLED_ADMIN = [
    "Flags: X - DISABLED",
    "Columns: NAME, GROUP, LAST-LOGGED-IN, INACTIVITY-POLICY",
    " #   NAME         GROUP  LAST-LOGGED-IN       INACTIVITY-POLICY",
    ";;; system default user",
    " 0 X admin        full                        none             ",
    " 1   eo           full   2023-03-22 02:45:21  none             ",
    " 9   ryan_turner  full                        none             ",
    "10   ve7alb       full   2026-09-04 17:52:10  none             ",
    "18   N7JMV        full                        none",
]

# An expired account.
V7_EXPIRED = [
    "Flags: E - EXPIRED",
    "Columns: NAME, GROUP, LAST-LOGGED-IN, INACTIVITY-POLICY",
    " #   NAME        GROUP  LAST-LOGGED-IN       INACTIVITY-POLICY",
    " 0   eo          full                        none             ",
    " 8   KD7DK       full   2026-11-13 12:13:16  none             ",
    " 9 E eo-test     read                        none             ",
]

# An ADDRESS column, and a comment in the middle of the list.
V7_ADDRESS = [
    "Columns: NAME, GROUP, ADDRESS, LAST-LOGGED-IN, INACTIVITY-POLICY",
    " # NAME         GROUP  ADDRESS           LAST-LOGGED-IN       INACTIVITY-POLICY",
    " 7 ve7alb       full                     2026-09-05 07:36:29  none             ",
    ";;; FTP backup",
    " 8 ftpuser      ftp    44.135.219.21/32                       none             ",
    " 9 ryan_turner  full                                          none             ",
]

# RouterOS 6 layout: the comment follows the row number and the name is on the next line.
V6_STYLE = """Flags: X - disabled
 #   NAME        GROUP    ADDRESS            LAST-LOGGED-IN
 0   ;;; system default user
     admin       full                        nov/13/2026 12:00:00
 1   vagrant     full
 2 X olduser     read
"""


class UserNames(unittest.TestCase):
    def test_plain_listing(self):
        self.assertEqual(mod.routeros_user_names(V7_PLAIN),
                         ["eo", "NQ1E", "ve7alb", "kennyr", "monitoring", "KK7LZM"])

    def test_disabled_admin_is_admin_not_x(self):
        names = mod.routeros_user_names(V7_DISABLED_ADMIN)
        self.assertEqual(names, ["admin", "eo", "ryan_turner", "ve7alb", "N7JMV"])
        self.assertNotIn("X", names)

    def test_expired_flag(self):
        self.assertEqual(mod.routeros_user_names(V7_EXPIRED), ["eo", "KD7DK", "eo-test"])

    def test_address_column_and_comment_line(self):
        self.assertEqual(mod.routeros_user_names(V7_ADDRESS), ["ve7alb", "ftpuser", "ryan_turner"])

    def test_routeros6_layout(self):
        self.assertEqual(mod.routeros_user_names(V6_STYLE), ["admin", "vagrant", "olduser"])

    def test_string_with_crlf_and_empty(self):
        self.assertEqual(mod.routeros_user_names("\r\n".join(V7_EXPIRED)), ["eo", "KD7DK", "eo-test"])
        self.assertEqual(mod.routeros_user_names(""), [])
        self.assertEqual(mod.routeros_user_names(None), [])

    def test_no_header(self):
        self.assertEqual(mod.routeros_user_names([" 0 X admin full", " 1 eo full"]), ["admin", "eo"])

    def test_short_upper_case_name_is_a_name_when_there_is_no_flag_column(self):
        plain = [" # NAME  GROUP", " 0 X     full", " 1 AB    read"]
        self.assertEqual(mod.routeros_user_names(plain), ["X", "AB"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
