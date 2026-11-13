"""Unit tests for filter_plugins/routeros_ssh_keys.py.

Run from anywhere:   python3 -I roles/routeros_common/tests/test_routeros_ssh_keys.py

NOTE: V7_OUTPUT, V6_OUTPUT and MD5_OUTPUT below are synthetic.  REAL_OUTPUT and REAL_725_OUTPUT are
real RouterOS 7 captures; REAL_V6_OUTPUT (6.49.19) and REAL_722_OUTPUT (7.22) were captured from
the molecule test routers with '/user ssh-keys print detail without-paging'.
"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "..", "filter_plugins", "routeros_ssh_keys.py")
spec = importlib.util.spec_from_file_location("routeros_ssh_keys", PLUGIN)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
# Master key checks live in the shared role (ssh_pubkeys_info, called with max_keys=1 for RouterOS).
SHARED = os.path.join(HERE, "..", "..", "hamwan_ssh_common", "filter_plugins", "ssh_keys.py")
sspec = importlib.util.spec_from_file_location("ssh_keys", SHARED)
shared = importlib.util.module_from_spec(sspec)
sspec.loader.exec_module(shared)

# GitHub's published ed25519 host key and its published SHA256 fingerprint
GH_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl"
GH_SHA256 = "SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU"

V7_OUTPUT = """Flags: X - disabled
 0 user=tom key-type=ed25519 bits=256
   fingerprint="SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU" info="tom@laptop"

 1 user="alice" key-type=rsa bits=4096 fingerprint="SHA256:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
 2 user=tom key-type=rsa bits=2048 fingerprint="SHA256:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
"""

V6_OUTPUT = """ 0 user="tom" bits=2048 key-owner="tom@laptop"
 1 user="alice" bits=2048 key-owner="alice@host"
"""

MD5_OUTPUT = ' 0 user=bob bits=2048 fingerprint="AB:cd:00:11:22:33:44:55:66:77:88:99:aa:bb:cc:dd"\n'


# Captured from a real device (R1.Beacon): key-type=(unknown) for DSA keys, padded SHA256 values,
# empty info="", two-digit indexes.
REAL_OUTPUT = """ 0  user=NQ1E key-type=(unknown) bits=1024 info="NQ1E-dsa" fingerprint="SHA256:iBP7716/ZzAzQ7nmikCZjXALfdGceQ2lwzbC7UawM/E="

 1  user=nigel key-type=rsa bits=2048 info="nigel" fingerprint="SHA256:UJBleZ72T4iU7DaQoqdoAtL4APFt3CGb/mSP5ARBYfI="

 7  user=ve7alb key-type=(unknown) bits=1024 info="" fingerprint="SHA256:YOg4XfYhZNC/corprjZ57zAjbt6DdhldsCk539d8klk="

10  user=kennyr key-type=rsa bits=2048 info="kennyr@kgrMBP.local" fingerprint="SHA256:xPcgrE9ndGJnc8cuOTN0cuw6KVHa/jZzU5WcSqu8VYk="
"""


# Real RouterOS 7.25 capture (CRS328, via network_cli with +cet512w, 2026-11-03).  Note the key="..."
# value wrapped onto a continuation line, and the blank ' ' separator lines.
REAL_725_OUTPUT = (
    '0  user=KD7DK key-type=ed25519 bits=256 info="dpk-20261003@randomnotes.org"\n'
    '   fingerprint="SHA256:ohxfKLN/+snqXS9/vwstXssOmsxAbq5tveTMcpx6mOc"\n'
    '   key="ssh-ed25519 \n'
    '      AAAAC3NzaC1lZDI1NTE5AAAAIMiczZBeXw1bqKREjxMnE/vp+BGuCcZIvt22uick66Ne"\n'
    ' \n'
    '1  user=claudetest key-type=ed25519 bits=256 info="claudetest@cowork"\n'
    '   fingerprint="SHA256:OZDCzCBc7uPuFcw6bKl2tvLxtfrGVPiglX9B24JM2wg"\n'
    '   key="ssh-ed25519 \n'
    '      AAAAC3NzaC1lZDI1NTE5AAAAIEQzwgfW5i0UZEhYMSEhlbdA6+4BWw0OWt1BGAtOJMxz"\n'
)
CLAUDETEST_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEQzwgfW5i0UZEhYMSEhlbdA6+4BWw0OWt1BGAtOJMxz claudetest@cowork"

# RouterOS 6.49.19: a flags line, a flag column (R = RSA), no fingerprints, CR LF line ends.
REAL_V6_OUTPUT = (
    'Flags: R - RSA, D - DSA \r\n'
    ' 0 R user=vagrant bits=2048 key-owner="" \r\n'
    '\r\n'
    ' 1 R user=admin1 bits=2048 key-owner="admin1@molecule-test" \r\n'
    '\r\n'
    ' 2 R user=admin2 bits=2048 key-owner="admin2@molecule-test" \r\n'
    '\r\n'
    ' 3 R user=user1 bits=2048 key-owner="user1@molecule-test" \r\n'
    '\r\n'
)

# RouterOS 7.22: one line per key, fingerprint with base64 padding ('=' at the end).
REAL_722_OUTPUT = (
    ' 0 user=vagrant key-type=rsa bits=2048 info="" fingerprint="SHA256:1M4RzhMyWuFS/86uPY/ce2prh/dVTHW7iD2RhpquOZA=" \r\n'
    '\r\n'
    ' 1 user=admin1 key-type=rsa bits=2048 info="admin1@molecule-test" fingerprint="SHA256:qZ0Ggl67RtKT8GNfN1fZMkraksPyqHkh6vKcLfc9qTo=" \r\n'
    '\r\n'
)
ADMIN1_SHA256 = "SHA256:qZ0Ggl67RtKT8GNfN1fZMkraksPyqHkh6vKcLfc9qTo"


class DeviceParse(unittest.TestCase):
    def test_real_v6_capture(self):
        keys = mod.routeros_ssh_keys_parse(REAL_V6_OUTPUT)
        self.assertEqual(sorted(keys), ["admin1", "admin2", "user1", "vagrant"])
        for user in keys:
            self.assertEqual(len(keys[user]), 1)
            self.assertEqual(keys[user][0]["fingerprints"], [])

    def test_real_v7_22_capture_matches_the_test_master_key(self):
        keys = mod.routeros_ssh_keys_parse(REAL_722_OUTPUT)
        self.assertEqual(sorted(keys), ["admin1", "vagrant"])
        self.assertEqual(keys["admin1"][0]["fingerprints"], [ADMIN1_SHA256])
        here = os.path.join(HERE, "..", "molecule", "default", "test_keys", "admin1.key")
        with open(here) as fh:
            master = shared.ssh_pubkeys_info(fh.read(), max_keys=1)
        self.assertEqual(master["sha256"], ADMIN1_SHA256)

    def test_v7_wrapped_items_and_multiple_keys(self):
        keys = mod.routeros_ssh_keys_parse(V7_OUTPUT)
        self.assertEqual(sorted(keys), ["alice", "tom"])
        self.assertEqual(len(keys["tom"]), 2)
        self.assertIn(GH_SHA256, keys["tom"][0]["fingerprints"])
        self.assertEqual(keys["tom"][0]["type"], "ed25519")
        self.assertEqual(keys["alice"][0]["bits"], "4096")

    def test_real_v7_capture(self):
        keys = mod.routeros_ssh_keys_parse(REAL_OUTPUT)
        self.assertEqual(sorted(keys), ["NQ1E", "kennyr", "nigel", "ve7alb"])
        self.assertEqual(keys["NQ1E"][0]["fingerprints"], ["SHA256:iBP7716/ZzAzQ7nmikCZjXALfdGceQ2lwzbC7UawM/E"])
        self.assertEqual(keys["ve7alb"][0]["type"], "(unknown)")
        self.assertEqual(len(keys["kennyr"][0]["fingerprints"]), 1)

    def test_v6_has_no_fingerprints(self):
        keys = mod.routeros_ssh_keys_parse(V6_OUTPUT)
        self.assertEqual(keys["tom"][0]["fingerprints"], [])
        self.assertEqual(keys["alice"][0]["fingerprints"], [])

    def test_md5_normalised_to_lowercase(self):
        keys = mod.routeros_ssh_keys_parse(MD5_OUTPUT)
        self.assertEqual(keys["bob"][0]["fingerprints"], ["ab:cd:00:11:22:33:44:55:66:77:88:99:aa:bb:cc:dd"])

    def test_empty_and_none(self):
        self.assertEqual(mod.routeros_ssh_keys_parse(""), {})
        self.assertEqual(mod.routeros_ssh_keys_parse(None), {})

    def test_info_text_containing_user_equals_does_not_confuse(self):
        out = ' 0 user=tom key-type=rsa bits=2048 info="was user=mallory"\n'
        self.assertEqual(list(mod.routeros_ssh_keys_parse(out)), ["tom"])

    def test_master_fingerprint_matches_device_value(self):
        want = shared.ssh_pubkeys_info(GH_KEY)
        have = mod.routeros_ssh_keys_parse(V7_OUTPUT)["tom"][0]["fingerprints"]
        self.assertIn(want["sha256"], have)


    def test_real_v7_25_capture_with_wrapped_key(self):
        got = mod.routeros_ssh_keys_parse(REAL_725_OUTPUT)
        self.assertEqual(sorted(got), ["KD7DK", "claudetest"])
        self.assertEqual(got["KD7DK"][0]["fingerprints"], ["SHA256:ohxfKLN/+snqXS9/vwstXssOmsxAbq5tveTMcpx6mOc"])
        self.assertEqual(got["claudetest"][0]["type"], "ed25519")
        want = shared.ssh_pubkeys_info(CLAUDETEST_KEY)
        self.assertIn(want["sha256"], got["claudetest"][0]["fingerprints"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
