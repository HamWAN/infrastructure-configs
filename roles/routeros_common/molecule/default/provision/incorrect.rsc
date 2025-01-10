:put "Incorrect settings for HamWAN RouterOS devices"

:put "Set remote logging destination"
/system logging action set [find name=remote] bsd-syslog=no name=remote remote=1.2.3.4 remote-port=514 src-address=0.0.0.0 syslog-facility=daemon syslog-severity=auto target=remote

:put "Setting SNMP address range"
/snmp community set name=hamwan addresses=44.24.240.0/20 read-access=yes write-access=no numbers=0

:put "Setting HamWAN DNS servers"
/ip dns set servers=44.24.245.1,44.24.244.1

:put "Disabling remote DNS requests (DNS proxy)"
/ip dns set allow-remote-requests=yes

:put "Create dummy interface with DHCP on subnet 44.24.243.0/28"
/ip pool add name=pool1 ranges=44.24.243.2-44.24.243.14
/in bridge add name=dummy1
/ip address add interface=dummy1 address=44.24.243.1/28
/ip dhcp-server add address-pool=pool1 authoritative=after-2sec-delay interface=dummy1 lease-time=1h name=dhcp99
/ip dhcp-server network add address=44.24.243.0/28 dns-server=44.24.244.1,44.24.245.1 domain=HamWAN.net gateway=44.25.243.1 ntp-server=44.24.244.4,44.24.245.4

# Setup NTP client settings
:put "Setting client NTP servers"
:local rosver [/system resource get version]
:if ($rosver~"^7.*") do={
    ;put "RouterOS 7.x settings";
    :global command [:parse "/system ntp client set enabled=yes servers=44.24.244.4,44.24.245.4"]
} else={
    ;put "RouterOS 6.x settings";
    :global command [:parse "/system ntp client set enabled=yes primary-ntp=44.24.244.4 secondary-ntp=44.24.245.4"]
}
:put "Using command $command"
$command

# Not part of the core yet
:put "Setting time zone to America/Los_Angeles"
/system clock set time-zone-name=America/Chicago
:put "Setting up SNMP"
/snmp set enabled=yes contact="#hamwan-support on some other irc.chat.com"
