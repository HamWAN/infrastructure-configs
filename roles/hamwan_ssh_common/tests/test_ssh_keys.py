"""Unit tests for filter_plugins/ssh_keys.py (shared by routeros_common and users).

Run from anywhere:   python3 -I roles/hamwan_ssh_common/tests/test_ssh_keys.py
"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ssh_keys", os.path.join(HERE, "..", "filter_plugins", "ssh_keys.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# GitHub's published ed25519 host key and its published SHA256 fingerprint
GH_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl"
GH_SHA256 = "SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU"
OTHER_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEQzwgfW5i0UZEhYMSEhlbdA6+4BWw0OWt1BGAtOJMxz"
TWO_KEYS = GH_KEY + " github\n" + OTHER_KEY + " other\n"


class PubkeysInfo(unittest.TestCase):
    def test_known_sha256_vector(self):
        i = mod.ssh_pubkeys_info(GH_KEY + " github\n")
        self.assertTrue(i["valid"])
        self.assertEqual(i["type"], "ssh-ed25519")
        self.assertEqual(i["sha256"], GH_SHA256)
        self.assertEqual(i["fingerprints"], [GH_SHA256])
        self.assertEqual(i["key_lines"], [GH_KEY + " github"])
        self.assertRegex(i["md5"], r"^([0-9a-f]{2}:){15}[0-9a-f]{2}$")

    def test_comments_blank_lines_and_options(self):
        i = mod.ssh_pubkeys_info("# master key\n\n" + 'from="44.0.0.0/8" ' + GH_KEY + "\n")
        self.assertTrue(i["valid"])
        self.assertEqual(i["count"], 1)
        self.assertEqual(i["sha256"], GH_SHA256)

    def test_several_keys_allowed_by_default(self):
        i = mod.ssh_pubkeys_info(TWO_KEYS)
        self.assertTrue(i["valid"], i)
        self.assertEqual(i["count"], 2)
        self.assertEqual(len(i["fingerprints"]), 2)

    def test_max_keys_1_rejects_two_but_reports_count(self):
        i = mod.ssh_pubkeys_info(TWO_KEYS, max_keys=1)
        self.assertFalse(i["valid"])
        self.assertEqual(i["count"], 2)
        self.assertIn("2 keys in file", i["error"])
        self.assertEqual(i["sha256"], GH_SHA256)

    def test_max_keys_1_accepts_one(self):
        self.assertTrue(mod.ssh_pubkeys_info(GH_KEY, max_keys=1)["valid"])

    def test_empty_or_garbage_is_invalid(self):
        for t in ("", None, [], "\n# only a comment\n", "hello", "ssh-ed25519 !!!notbase64!!!", "<html>404</html>"):
            self.assertFalse(mod.ssh_pubkeys_info(t)["valid"], t)

    def test_any_non_key_line_rejects_the_file(self):
        i = mod.ssh_pubkeys_info(GH_KEY + "\n<html>502 Bad Gateway</html>\n")
        self.assertFalse(i["valid"])
        self.assertIn("line 2", i["error"])

    def test_list_input_from_query(self):
        self.assertTrue(mod.ssh_pubkeys_info([GH_KEY, ""])["valid"])


class KeyIds(unittest.TestCase):
    def test_same_keys_compare_equal_regardless_of_comment_options_and_order(self):
        b = "no-pty " + OTHER_KEY + " x\n" + GH_KEY + " y\n"
        self.assertEqual(mod.ssh_key_ids(TWO_KEYS), mod.ssh_key_ids(b))

    def test_extra_key_differs(self):
        self.assertNotEqual(mod.ssh_key_ids(GH_KEY), mod.ssh_key_ids(TWO_KEYS))


if __name__ == "__main__":
    unittest.main(verbosity=1)
