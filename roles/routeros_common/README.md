# routeros_common Role

This role is designed to query various routeros settings and update or create them if they
do not match desired settings.  The configruation is split into two locations.
 - roles/routeros_common/vars/main.yml holds the description of each setting and how to change it.
 - group_vars/os_routeros.yml sets the site specific values used by the file above.
By putting the values in group_vars, the can be overriden where needed by entries in host_vars.

It is currently tested against routeros versions up to 6.1-6.49.x and 7.1-7.16.

The user is expected to have SSH access to the devices.
