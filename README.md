# catboy-registry

Source of truth for everything allocated under the IANA Private Enterprise Number of catboy.systems / m-schneider.cc (`1.3.6.1.4.1.66963`): the arc registry, the protocol specifications that use it, and generated constant packages so no project hardcodes an OID.

**Status:** IANA assigned Private Enterprise Number **66963** on 2026-09-25 (registrant: Marc Schneider; [IANA registry](https://www.iana.org/assignments/enterprise-numbers/)). The enterprise arc is `1.3.6.1.4.1.66963`. `pen` in `registry.yaml` is set once and CI refuses any later change.

## What is in here

| Path | Content |
|---|---|
| `registry.yaml` | every arc: oid (relative), name, status, owner, since, purpose, spec |
| `schema/` | JSON schema for the registry |
| `specs/` | X.509 / CMS extensions, SNMP MIB, DHCP vendor options, syslog SD-IDs, DNS-SD services, media types, UUID namespace, capability schema |
| `tools/` | `lint.py` (shape, duplicates, no internal topology), `immutability.py` (numbers and meanings never change), `gen.py` (constants + docs) |
| `docs/arcs.md` | generated table of all arcs |
| `packages/` | NuGet `Catboy.Registry`, Packagist `catboy/registry`, PyPI `catboy-registry` (generated; published from tags once `pen` is set) |

## Rules

1. Append-only. A merged number keeps its name and purpose forever. Only `status` moves: `reserved → active → deprecated`.
2. Reserve first, activate in a second PR after review.
3. Identifiers only. No addresses, hostnames or topology: this repository is public and the lint refuses them.
4. Consumers read the generated packages, never the YAML.

## Consumers (planned)

NetPaw syslog export (`netpaw@66963`), DropMeNot audit log, CatCMDB SNMP vendor map, PoloPack media types, the catboy.systems PKI (policy OIDs and the run-metadata extension), catboy-agent DHCP zero-touch enrol, DNS-SD discovery (`_catboy._tcp`).

## Develop

```
pip install pyyaml jsonschema
python3 tools/lint.py --strict
python3 tools/immutability.py origin/main
python3 tools/gen.py           # renders build/, docs/arcs.md and the published specs/
python3 tools/mibcheck.py      # smilint every MIB, fail on any diagnostic
python3 tools/asn1check.py     # compile + DER round-trip the ASN.1 modules
```
