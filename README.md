# catboy-registry

Source of truth for everything allocated under the IANA Private Enterprise Number of catboy.systems / m-schneider.cc (`1.3.6.1.4.1.66963`): the arc registry, the protocol specifications that use it, and generated constant packages so no project hardcodes an OID.

**Status:** IANA assigned Private Enterprise Number **66963** on 2026-09-25 (registrant: Marc Schneider; [IANA registry](https://www.iana.org/assignments/enterprise-numbers/)). The enterprise arc is `1.3.6.1.4.1.66963`. `pen` in `registry.yaml` is set once and CI refuses any later change.

## What is in here

| Path | Content |
|---|---|
| `registry.yaml` | every arc: oid (relative), name, status, owner, since, purpose, spec |
| `schema/` | JSON schema for the registry |
| `specs/` | X.509 / CMS extensions, SNMP MIB, DHCP vendor options, syslog SD-IDs, DNS-SD services, media types, UUID namespace, capability schema |
| `tools/` | `lint.py` (shape, duplicates, software and instance rules, no internal topology or secrets in tracked files, `build/` and `packages/`), `immutability.py` (numbers and meanings never change), `gen.py` (constants, id/HLC helpers + docs), `vectors.py` + `fuzz.py` (cross-language test vectors) |
| `tests/` | `vectors/*.json` (fixed test vectors) and `runners/<lang>` (Python, Go, PHP, C#) that reproduce them |
| `docs/arcs.md` | generated table of all arcs |
| `packages/` | NuGet `Catboy.Registry`, Packagist `catboy/registry`, PyPI `catboy-registry` (generated; published from tags once `pen` is set) |

## Arcs

The full, generated table is [docs/arcs.md](docs/arcs.md). The top level:

| Arc | Name | Status | Spec |
|---|---|---|---|
| `.1` | catboy-systems | active | project arc |
| `.1.1` | certificate-policies | reserved | [specs/x509](specs/x509/README.md) |
| `.1.2` | x509-cms-extensions | reserved | [specs/x509](specs/x509/README.md), [specs/cms](specs/cms/README.md) |
| `.1.3` | syslog-sd-ids | reserved | [specs/syslog](specs/syslog/sd-ids.yaml) |
| `.1.4` | snmp | reserved | [specs/snmp](specs/snmp/README.md) |
| `.1.5` | dhcp-vendor-options | reserved | [specs/dhcp](specs/dhcp/vendor-options.yaml) |
| `.1.6` | uuid-namespace | reserved | [specs/uuid](specs/uuid/namespace.md): fleet namespace, entry ids, canonicalization |
| `.1.7`–`.1.9` | ldap, ipfix, radius | reserved | unused today |
| `.1.10` | capabilities | reserved | [specs/capabilities](specs/capabilities/capability.schema.json) |
| `.1.11` | software | reserved | [specs/software](specs/software/README.md): one arc per product (catboy-agent, catwaf, pawkit), channel table |
| `.1.12` | instances | reserved | [specs/state](specs/state/README.md): one number per deployed instance, neutral names |
| `.1.13` | state-versioning | reserved | [specs/state](specs/state/README.md): epoch, seq, root, HLC, `/.well-known/catboy-state` |
| `.2` | m-schneider-cc | reserved | personal arc |
| `.9` | scratch | active | experiments, never stable |

Entry ids (sites, routes, state systems) are uuid5 values under the `.1.6` namespace, and changes
are UUIDv7. They need no registry entry. Their OID form is `2.25.<uuid integer>` (ITU-T X.667).

## Rules

1. Append-only. A merged number keeps its name and purpose forever. Only `status` moves: `reserved → active → deprecated`. A wrong entry is deprecated with `superseded_by` and replaced by a new number ([correction procedure](docs/arcs.md#correcting-a-wrong-entry)).
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
pip install idna                # IDNA 2008 / UTS #46 for the domain canonicalization
python3 tools/gen.py           # renders build/, docs/arcs.md and the published specs/
python3 tools/vectors.py --check                      # committed test vectors match the reference
python3 tests/runners/python/run.py                   # and: go run . (tests/runners/go),
php tests/runners/php/run.php                         #      dotnet run -- vectors (tests/runners/dotnet)
python3 tools/fuzz.py gen 42 1000 > /tmp/in.json      # cross-language: run each runner with `fuzz /tmp/in.json`,
python3 tools/fuzz.py compare out.py out.go out.php out.cs   # then compare the outputs
python3 tools/mibcheck.py      # smilint every MIB, fail on any diagnostic
python3 tools/asn1check.py     # compile + DER round-trip the ASN.1 modules
```
