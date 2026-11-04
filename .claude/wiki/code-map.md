---
title: catboy-registry code map
scope: catboy-registry
tags:
- code-map
- mermaid
- structure
- auto
summary: 'Code map: catboy-registry — 7 components, 6 call-dependencies (top); core:
  Hlc, helpers.py, Ids, helpers.go'
related: []
web: []
---

Code map: catboy-registry — 7 components, 6 call-dependencies (top); core: Hlc, helpers.py, Ids, helpers.go

_Auto-generated (deterministic, no AI) from the symbol index._

## Core components (PageRank — most depended-upon)
- `Hlc` — 0.432
- `helpers.py` — 0.137
- `Ids` — 0.137
- `helpers.go` — 0.074
- `asn1check.py` — 0.074
- `vectors.py` — 0.074
- `gen.py` — 0.074

## Call dependencies (who calls whom)
```mermaid
graph LR
  n_Hlc["Hlc"]
  n_Ids["Ids"]
  n_asn1check_py["asn1check.py"]
  n_gen_py["gen.py"]
  n_helpers_go["helpers.go"]
  n_helpers_py["helpers.py"]
  n_vectors_py["vectors.py"]
  n_vectors_py -->|27| n_helpers_py
  n_gen_py -->|6| n_Ids
  n_Ids -->|4| n_Hlc
  n_asn1check_py -->|4| n_Hlc
  n_helpers_py -->|4| n_Hlc
  n_helpers_go --> n_Hlc
```

## Largest components (by member count)
- `Ids` — 29 members
- `Hlc` — 14 members
- `Program` — 11 members
