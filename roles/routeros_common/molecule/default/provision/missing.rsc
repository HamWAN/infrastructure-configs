:put "Missing setting for HamWAN RouterOS devices"

:put "Setting Empty HamWAN DNS servers"
/ip dns set servers=""

:put "Create dummy interface with DHCP on non-HamWAN subnet 44.12.1.0/28"
/ip pool add name=pool1 ranges=44.12.1.2-44.12.1.14
/in bridge add name=dummy1
/ip address add interface=dummy1 address=44.12.1.1/28
/ip dhcp-server add address-pool=pool1 authoritative=after-2sec-delay interface=dummy1 lease-time=1h name=dhcp99
/ip dhcp-server network add address=44.12.1.0/28 dns-server=1.1.1.1,2.2.2.2 domain=HamWAN.net gateway=44.12.1.1 ntp-server=3.3.3.3,4.4.4.4

:put "Setup NTP client settings"
:local rosver [/system resource get version];
:if ($rosver~"^7.*") do={
    ;put "RouterOS 7.x settings";
    :global command [:parse "/system ntp client set enabled=no servers=\"\""]
} else={
    ;put "RouterOS 6.x settings";
    :global command [:parse "/system ntp client set enabled=no primary-ntp=0.0.0.0 secondary-ntp=0.0.0.0"]
}
:put "Using command $command"
$command

# Not part of the core yet
:put "Setting time zone to America/Los_Angeles"
/system clock set time-zone-name=America/Los_Angeles
:put "Setting up SNMP"
/snmp set enabled=yes contact="#hamwan-support on libera.chat"
