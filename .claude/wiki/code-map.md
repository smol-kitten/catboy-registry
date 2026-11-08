---
title: catboy-registry code map
scope: catboy-registry
tags:
- code-map
- mermaid
- structure
- auto
summary: 'Code map: catboy-registry — 6 components, 4 call-dependencies (top); core:
  Hlc, helpers.go, helpers.py, vectors.py'
related: []
web: []
---

Code map: catboy-registry — 6 components, 4 call-dependencies (top); core: Hlc, helpers.go, helpers.py, vectors.py

_Auto-generated (deterministic, no AI) from the symbol index._

## Core components (PageRank — most depended-upon)
- `Hlc` — 0.338
- `helpers.go` — 0.183
- `helpers.py` — 0.183
- `vectors.py` — 0.099
- `Ids` — 0.099
- `Ids.php` — 0.099

## Call dependencies (who calls whom)
```mermaid
graph LR
  n_Hlc["Hlc"]
  n_Ids["Ids"]
  n_Ids_php["Ids.php"]
  n_helpers_go["helpers.go"]
  n_helpers_py["helpers.py"]
  n_vectors_py["vectors.py"]
  n_vectors_py -->|27| n_helpers_py
  n_Ids -->|4| n_Hlc
  n_helpers_go --> n_Hlc
  n_Ids_php --> n_helpers_go
```

## Largest components (by member count)
- `Ids` — 15 members
- `Program` — 11 members
- `Hlc` — 7 members
