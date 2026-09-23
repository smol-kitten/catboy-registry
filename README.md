# catboy-registry

Source of truth for everything allocated under the IANA Private Enterprise Number of catboy.systems / m-schneider.cc (`1.3.6.1.4.1.<pen>`): the arc registry, the protocol specifications that use it, and generated constant packages so no project hardcodes an OID.

**Status:** the PEN is applied for and not yet assigned. `registry.yaml` carries `pen: null`; everything builds, nothing publishes until the number arrives.

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

NetPaw syslog export (`netpaw@<pen>`), DropMeNot audit log, CatCMDB SNMP vendor map, PoloPack media types, the catboy.systems PKI (policy OIDs and the run-metadata extension), catboy-agent DHCP zero-touch enrol, DNS-SD discovery (`_catboy._tcp`).

## Develop

```
pip install pyyaml jsonschema
python3 tools/lint.py --strict
python3 tools/immutability.py origin/main
python3 tools/gen.py           # renders build/ and docs/arcs.md
```
