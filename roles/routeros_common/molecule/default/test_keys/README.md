Public keys for the RouterOS molecule test users (users_admin / users_user in molecule_vars.yml).
They are served by a small web server on the test host (key_server.yml) and downloaded by the
routers with /tool fetch.  RSA, because RouterOS 6 cannot import ed25519 keys.  The matching
private keys were discarded: nobody logs in as these users.
