# routeros_common Role

This role is designed to query various routeros settings and update or create them if they
do not match desired settings.  The configruation is split into two locations.
 - roles/routeros_common/vars/main.yml holds the description of each setting and how to change it.
 - group_vars/os_routeros.yml sets the site specific values used by the file above.
By putting the values in group_vars, the can be overriden where needed by entries in host_vars.

It is currently tested against routeros versions up to 6.1-6.49.x and 7.1-7.16.

The user is expected to have SSH access to the devices.

## Testing

We use molecule to drive automated testing using Vagrant and VirtualBox based routeros images.
Vagrant is going to build 6 RouterOS images.  Three each for RouterOS 6 and RouterOS 7.
Each is in a specific initial state for each of the settings we are going to test:

 - correct - the setting are already as we would expect.  No change should be applied.
 - incorrect - all the settings are present but wrong.  They should all be corrected.
 - missing - where possible, the setting are unset or missing.  They should be set or ignored (situationly dependent).

### References

The source for our routeros images:
https://github.com/cheretbe/packer-routeros/tree/master

Some useful description of using molecule and Vagrant for testing:
https://floatingpoint.sorint.it/blog/post/setting-up-molecule-for-testing-ansible-roles-with-vagrant-and-testinfra

Vagrant docs:
https://developer.hashicorp.com/vagrant/docs/providers/basic_usage
