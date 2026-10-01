# SNMP (arc .1.4)

Generated from `templates/snmp/*.tmpl` by `tools/gen.py`; the files here are the published copies, never edited by hand. CI renders them again and fails if they differ, and `tools/mibcheck.py` fails on any `smilint -l 6` diagnostic (smilint's own exit code is 0 even on errors).

| Arc | Module | Status |
|---|---|---|
| `.1.4` | `CATBOY-SMI` (`CATBOY-SMI.txt`): enterprise root, `catboySnmp`, sysObjectID, experimental arc | published |
| `.1.4.1` | `catboyAgentSysObjectID`: sysObjectID of every catboy-agent host (says "fleet host", not which one) | published |
| `.1.4.2` | `CATBOY-AGENT-MIB` (`CATBOY-AGENT-MIB.txt`): enrolment id, enrol state, version, last heartbeat (= last CatCMDB sync), trust anchor, site, disk-full and backup-failed flags, managed-services table, two notifications | published |
| `.1.4.3` | `CATBOY-PKI-MIB` (`CATBOY-PKI-MIB.txt`): CA seal state, publish epoch and age, issuer table (fingerprint, certificate expiry, CRL number and seconds to nextUpdate), seal-state, CRL-stale and publish-stale notifications. Served on the CA host by catboy-pki `snmp/` | published |
| `.1.4.4` | `CATBOY-WAF-MIB`: CatWAF site and backend health (optional) | reserved |
| `.1.4.5` | `CATBOY-FLEET-MIB` (`CATBOY-FLEET-MIB.txt`): snapshot age, pawkit release/channel/build, hub epoch, seq, sync state and state age, load finding counts by severity, guest backup table (host, VMID, name, last attempt time, result, age). Served on the pawkit host by pawkit `snmp_fleet.py` | published |
| `.1.4.6` | `CATBOY-HOST-MIB` (`CATBOY-HOST-MIB.txt`): hostsec collector status table, firewall (backend, policy, rule count, gap table), apt and unattended-upgrades, running vs newest kernel, reboot-required and uptime, sysctl hardening score and deviation table, journal counts (1 h/24 h/48 h, OOM, segfaults, coredumps, taint, last crit lines), failed units, DNS probe, sshd and account checks, PSI and temperature, derived needs-reboot/needs-intervention flags with a reason table. No notifications. Served by catboy-agent as a second AgentX session | published |
| `.1.4.99` | experimental; never stable | reserved |

Layout inside every module arc: notifications `.0`, objects `.1`, conformance `.2`.

Access: SNMPv3 authPriv only, read-only views. A host is joined to its CatCMDB record by `catboyAgentEnrolmentId`, not by sysObjectID or address.

Lint locally: `python3 tools/gen.py && python3 tools/mibcheck.py`.
