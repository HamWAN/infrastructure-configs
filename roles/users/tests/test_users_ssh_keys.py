"""Unit tests for filter_plugins/users_ssh_keys.py.

Run from anywhere:   python3 -I roles/users/tests/test_users_ssh_keys.py
"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("users_ssh_keys", os.path.join(HERE, "..", "filter_plugins", "users_ssh_keys.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# GitHub's published ed25519 host key and its published SHA256 fingerprint
GH_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl"
GH_SHA256 = "SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU"
TOM = open(os.path.join(HERE, "..", "molecule", "default", "test_keys", "tom.key")).read()


class PubkeysInfo(unittest.TestCase):
    def test_single_key_and_known_fingerprint(self):
        i = mod.users_pubkeys_info(GH_KEY + " github\n")
        self.assertTrue(i["valid"])
        self.assertEqual(i["fingerprints"], [GH_SHA256])
        self.assertEqual(i["key_lines"], [GH_KEY + " github"])

    def test_multiple_keys_are_valid(self):
        i = mod.users_pubkeys_info(TOM)
        self.assertTrue(i["valid"], i)
        self.assertEqual(i["count"], 2)

    def test_comments_blank_lines_and_options(self):
        i = mod.users_pubkeys_info("# master key\n\n" + 'from="44.0.0.0/8" ' + GH_KEY + "\n")
        self.assertTrue(i["valid"])
        self.assertEqual(i["fingerprints"], [GH_SHA256])

    def test_empty_is_invalid(self):
        for t in ("", None, "\n# only a comment\n", []):
            self.assertFalse(mod.users_pubkeys_info(t)["valid"], t)

    def test_any_non_key_line_rejects_the_file(self):
        i = mod.users_pubkeys_info(GH_KEY + "\n<html>502 Bad Gateway</html>\n")
        self.assertFalse(i["valid"])
        self.assertIn("line 2", i["error"])

    def test_bad_base64(self):
        self.assertFalse(mod.users_pubkeys_info("ssh-ed25519 not*base64 x")["valid"])

    def test_list_input_from_query(self):
        self.assertTrue(mod.users_pubkeys_info([GH_KEY, ""])["valid"])


class KeyIds(unittest.TestCase):
    def test_same_keys_compare_equal_regardless_of_comment_options_and_order(self):
        a = TOM
        b = "\n".join(reversed([('no-pty ' + l.rsplit(" ", 1)[0] + " other-comment") for l in TOM.strip().splitlines()]))
        self.assertEqual(mod.users_key_ids(a), mod.users_key_ids(b))

    def test_extra_key_differs(self):
        self.assertNotEqual(mod.users_key_ids(TOM), mod.users_key_ids(TOM + GH_KEY + "\n"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
