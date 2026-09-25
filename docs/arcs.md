# Arcs

Enterprise arc: `1.3.6.1.4.1.66963` (assignee: Marc Schneider)

| OID | Name | Status | Owner | Since | Purpose | Spec |
|---|---|---|---|---|---|---|
| `1.3.6.1.4.1.66963.1` | catboy-systems | active | catboy.systems | 2026-09-23 | catboy.systems project arc |  |
| `1.3.6.1.4.1.66963.1.1` | certificate-policies | reserved | catboy.systems | 2026-09-23 | X.509 certificatePolicies OIDs per PKI branch | [spec](../specs/x509/README.md) |
| `1.3.6.1.4.1.66963.1.1.1` | policy-services | reserved | catboy.systems | 2026-09-23 | policy for the Services CA (TLS/mTLS/ACME) |  |
| `1.3.6.1.4.1.66963.1.1.2` | policy-identity | reserved | catboy.systems | 2026-09-23 | policy for the Identity CA (people/devices) |  |
| `1.3.6.1.4.1.66963.1.1.3` | policy-code-signing | reserved | catboy.systems | 2026-09-23 | policy for the yearly Code Signing CAs |  |
| `1.3.6.1.4.1.66963.1.1.4` | policy-timestamping | reserved | catboy.systems | 2026-09-23 | policy for the Timestamp CA |  |
| `1.3.6.1.4.1.66963.1.2` | x509-cms-extensions | reserved | catboy.systems | 2026-09-23 | private X.509 extensions and CMS signed attributes | [spec](../specs/x509/README.md) |
| `1.3.6.1.4.1.66963.1.2.1` | x509-run-metadata | reserved | catboy.systems | 2026-09-23 | CI run metadata on code-signing leaves (Fulcio-mirrored field set) | [spec](../specs/x509/README.md) |
| `1.3.6.1.4.1.66963.1.2.2` | cms-run-metadata | reserved | catboy.systems | 2026-09-23 | the same run metadata as a CMS signed attribute in detached .p7s | [spec](../specs/cms/README.md) |
| `1.3.6.1.4.1.66963.1.2.3` | x509-id-card | reserved | catboy.systems | 2026-09-23 | Catboy ID card extension (card GUID, pronoun set) for Identity CA client certs |  |
| `1.3.6.1.4.1.66963.1.3` | syslog-sd-ids | reserved | catboy.systems | 2026-09-23 | RFC 5424 SD-ID enterprise number for catboy@<pen>, netpaw@<pen>, dropmenot@<pen> | [spec](../specs/syslog/sd-ids.yaml) |
| `1.3.6.1.4.1.66963.1.4` | snmp | reserved | catboy.systems | 2026-09-23 | SMIv2 MIB root (CATBOY-AGENT-MIB) | [spec](../specs/snmp/README.md) |
| `1.3.6.1.4.1.66963.1.4.1` | snmp-sysobjectid-agent | reserved | catboy.systems | 2026-09-23 | sysObjectID value for hosts running catboy-agent |  |
| `1.3.6.1.4.1.66963.1.4.2` | snmp-agent-mib | reserved | catboy.systems | 2026-09-25 | CATBOY-AGENT-MIB module (catboy-agent AgentX subagent - enrolment id, health flags, managed services, traps) | [spec](../specs/snmp/CATBOY-AGENT-MIB.txt) |
| `1.3.6.1.4.1.66963.1.4.3` | snmp-pki-mib | reserved | catboy.systems | 2026-09-25 | CATBOY-PKI-MIB module (CA seal state, CRL freshness, issuer expiry, publish age, traps) | [spec](../specs/snmp/README.md) |
| `1.3.6.1.4.1.66963.1.4.4` | snmp-waf-mib | reserved | catboy.systems | 2026-09-25 | CATBOY-WAF-MIB module (CatWAF site and backend health), optional | [spec](../specs/snmp/README.md) |
| `1.3.6.1.4.1.66963.1.4.99` | snmp-experimental | reserved | catboy.systems | 2026-09-25 | experimental SNMP objects; never stable, promoted objects get a new number in a module arc | [spec](../specs/snmp/README.md) |
| `1.3.6.1.4.1.66963.1.5` | dhcp-vendor-options | reserved | catboy.systems | 2026-09-23 | DHCPv4 option 125 / option 43 and DHCPv6 option 17 sub-option namespace | [spec](../specs/dhcp/vendor-options.yaml) |
| `1.3.6.1.4.1.66963.1.6` | uuid-namespace | reserved | catboy.systems | 2026-09-23 | uuid5(NAMESPACE_OID, "1.3.6.1.4.1.<pen>") = the fleet UUID namespace | [spec](../specs/uuid/namespace.md) |
| `1.3.6.1.4.1.66963.1.7` | ldap | reserved | catboy.systems | 2026-09-23 | LDAP attribute types and object classes (unused today) |  |
| `1.3.6.1.4.1.66963.1.8` | ipfix | reserved | catboy.systems | 2026-09-23 | IPFIX enterprise-specific information elements (unused today) |  |
| `1.3.6.1.4.1.66963.1.9` | radius | reserved | catboy.systems | 2026-09-23 | RADIUS vendor-specific attributes (unused today) |  |
| `1.3.6.1.4.1.66963.1.10` | capabilities | reserved | catboy.systems | 2026-09-23 | capability / protocol identifiers announced via DNS-SD _catboy._tcp and future catboy protocol work | [spec](../specs/capabilities/capability.schema.json) |
| `1.3.6.1.4.1.66963.2` | m-schneider-cc | reserved | m-schneider.cc | 2026-09-23 | personal arc |  |
| `1.3.6.1.4.1.66963.9` | scratch | active | catboy.systems | 2026-09-23 | experiments; nothing under .9 is stable or published |  |
