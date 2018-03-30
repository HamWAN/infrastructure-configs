#!/usr/bin/env python

import json
import urllib2


librenms = json.loads(
    urllib2.urlopen(urllib2.Request(
        'https://librenms.hamwan.org/api/v0/devices',
        headers={'X-Auth-Token': '600dc6857a6e2bf200b46e56b78c0049'},
    )).read()
)

inventory = {
    "_meta": {
        "hostvars": {}
    }
}

for key in ('os', 'sysName', 'type', 'version'):
    for device in librenms['devices']:
        group = device.get(key)
        if not group:
            continue
        if not inventory.get(group):
            inventory[group] = []
        inventory[group].append(device['hostname'])

# converts the 'status' field to an 'available' list
inventory['available'] = [device['hostname'] for device in librenms['devices']
                          if int(device.get('status'))]

print json.dumps(inventory, indent=2)
