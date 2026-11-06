---
title: catboy-registry patch notes
scope: catboy-registry
tags:
- changelog
summary: Auto-generated commit log for catboy-registry (deterministic).
related: []
web: []
---

### 2026-11-06
- `03d83bb` chore(docs): refresh indexes + wiki

### 2026-11-05
- `9e74a2b` chore(docs): refresh indexes + wiki

### 2026-11-04
- `9a8123c` chore(docs): refresh indexes + wiki

### 2026-11-03
- `253c2d9` chore(ci): docs-refresh workflow to DOCGEN_REF 26ecf96 (#16)
- `8946b62` chore(docs): refresh indexes + wiki

### 2026-11-03
- `491e423` chore(docs): refresh indexes + wiki

### 2026-11-02
- `f5206f6` chore(ci): add docs-refresh workflow (autowiki Phase 2) [skip ci] (#5)
- `fffd14a` Activate .1.11.4 pongnet (#15)
- `ef815b7` Reserve .1.11.4 pongnet, pongnet@66963 SD-ID, pongnet role (#14)
- `923c11d` apply orchestrator decisions (m-3929): HOST-MIB sysctl V2, nginx path profiles, sentinel host-move cost
- `218175a` specs/state: change order triple + restore sentinel format; SNMP base MIBs for NetPaw
- `66b2535` fix(snmp): CATBOY-HOST-MIB expects IPv4 forwarding on docker0 hosts too
- `f9aaee6` fix(snmp): CATBOY-HOST-MIB sysctl compliance includes stricter values
- `8ceac32` fix(snmp): CATBOY-HOST-MIB review changes (reason index, health score, omissions)
- `429f898` fix(snmp): CATBOY-FLEET-MIB rev 202610011200Z - no hypervisor names in catboyFleetGuestHost (#11)
- `62f9d7a` feat(snmp): CATBOY-HOST-MIB (.1.4.6)
- `2dfde4b` feat(snmp): CATBOY-FLEET-MIB (.1.4.5) (#9)
- `69382b4` feat(snmp): CATBOY-PKI-MIB (.1.4.3) (#8)
- `33ddaba` feat(snmp): CATBOY-AGENT-MIB rev 202609300000Z - release/build OIDs, fleet role, command counters (#7)
- `c1cb20e` feat: software arc, instances, state versioning, entry-id helpers (Phase A)
- `042e82e` reserve 1.1.99 policy-staging (generation 0 staging hierarchy, no assurance)
- `0629a53` feat: PEN 66963 assigned - set pen, reserve SNMP module arcs, v1 CATBOY-AGENT-MIB, strict smilint gate
- `44030f1` feat: spec templates (SMIv2 MIB, X.509 + CMS ASN.1) rendered with the real PEN or the RFC 5612 documentation PEN 32473 in dry-run; smilint + asn1tools in CI
- `5dd17e7` ci: block scalar for the docs check (a ': ' inside a plain scalar broke the workflow file)
- `880e2e6` fix: restore top-level pen/assignee keys; _load helper in gen + immutability
- `1533852` fix: quote purposes containing commas/quotes; add generated docs/arcs.md
- `ca0bbb9` feat: registry skeleton — registry.yaml (pen: null, reserved arcs), schema, lint/immutability/gen tools, spec stubs, CI
- `9bda492` Initial commit

<!--last:03d83bb8f72c35140c99c68f4a283f478d60ce77-->
