Base modules vendored from net-snmp (`/usr/share/snmp/mibs`) so `smilint` runs without distro MIB packages. Not part of the registry; never edited here. `tools/mibcheck.py` imports from this folder only, so a catboy MIB can import nothing else.

| Module | Source | Why |
|---|---|---|
| SNMPv2-SMI, SNMPv2-TC, SNMPv2-CONF | RFC 2578, 2579, 2580 | every SMIv2 module |
| SNMPv2-MIB | RFC 3418 | imported by IF-MIB |
| IANAifType-MIB | IANA (rev 202208170000Z) | imported by IF-MIB |
| IF-MIB | RFC 2863 | `InterfaceIndex`, `ifIndex` (NetPaw, CATBOY-NETPAW-MIB) |
| INET-ADDRESS-MIB | RFC 4001 | `InetAddressType`, `InetAddress`, `InetAddressPrefixLength` (NetPaw) |
| SNMP-FRAMEWORK-MIB | RFC 3411 | `SnmpAdminString` |
