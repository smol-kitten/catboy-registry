# Software arc (`.1.11`)

Status: **reserved**. Arc: `1.3.6.1.4.1.66963.1.11`.

The registry gives each fleet product one permanent number under `.1.11`. The product then makes
its own sub-arcs with the fixed grammar below. The registry never records a release, a channel
entry, a build or a data format. `tools/lint.py` refuses a registry entry below `.1.11.<n>`.

## Registered products

| Arc | Name | purl | Repository | Notes |
|---|---|---|---|---|
| `.1.11.1` | catboy-agent | `pkg:github/polo-nyan/catboy-agent` | polo-nyan/catboy-agent | hosts report sysObjectID `.1.4.1` (field `sysobjectid`) |
| `.1.11.2` | catwaf | `pkg:github/smol-kitten/cat-waf` | smol-kitten/cat-waf | |
| `.1.11.3` | pawkit | `pkg:github/polo-nyan/pawkit` | polo-nyan/pawkit | |

`registry.yaml` is the source of truth. This table is a copy for reading.

## Entry fields

A software entry is an arc `.1.11.<n>` in `registry.yaml`. It has the normal fields and these:

| Field | Required | Content |
|---|---|---|
| `purl` | yes | [Package URL](https://github.com/package-url/purl-spec) of the product, **without** a version, qualifiers or subpath. Example: `pkg:github/smol-kitten/cat-waf`. |
| `repo` | yes | HTTPS URL of the source repository. |
| `owner` | yes | The team or project that owns the product. |
| `sysobjectid` | no | Relative OID of the SNMP sysObjectID arc that hosts with this product report (catboy-agent: `1.4.1`). |

`purl` and `sysobjectid` do not change after the merge (`tools/immutability.py`). The lint
refuses a software entry without `purl`. The entry id of a product is
`uuid5(CATBOY_NAMESPACE, "software:" + name)` (kind `software`, see
[../uuid/namespace.md](../uuid/namespace.md)).

## Sub-arc grammar

`<P>` is the product arc, for example `1.3.6.1.4.1.66963.1.11.2` for CatWAF.

| Sub-arc | Meaning | Example (CatWAF) |
|---|---|---|
| `<P>.1.<major>.<minor>.<patch>` | a release (semantic version, numbers only) | `….1.11.2.1.3.0.12` = CatWAF 3.0.12 |
| `<P>.2.<channel>` | a release channel from the channel table | `….1.11.2.2.3` = CatWAF nightly |
| `<P>.3.<run_id>` | a build: the GitHub Actions `run_id` of the build workflow | `….1.11.2.3.18204455123` |
| `<P>.4.<format>.<compat>` | a data format of the product and its compatibility level | `….1.11.2.4.1.2` = format 1, level 2 |

Rules:

1. Every component is a non-negative decimal integer without leading zeros.
2. A pre-release suffix (`-rc.1`) or build metadata (`+abc`) has no place in the release arc. Use the
   channel arc and the build arc for that information.
3. The build arc uses `run_id`, not `run_number`. `run_id` is unique in a repository.
   `run_number` restarts when somebody renames a workflow.
4. The product defines its own format numbers (`.4.<format>`). The product documents them in its
   own repository. A format number keeps its meaning forever. Increase `<compat>` when a reader of
   the previous level can no longer read the data.
5. Branch names are never arcs. OID arcs are integers, and branches get renamed. Use the channel.

## Channel table

The source of truth is [channels.yaml](channels.yaml). It is append-only, like `registry.yaml`.

| Number | Channel | Meaning |
|---|---|---|
| 1 | stable | released for production |
| 2 | beta | release candidates and previews |
| 3 | nightly | scheduled builds from the default branch |
| 4 | dev | developer and pull-request builds; never deployed to production |

## Generated helpers

`tools/gen.py` writes these helpers for Python, Go, PHP and C#. The names follow the language
style (`release_oid` in Python, `ReleaseOid` in Go and C#, `Ids::releaseOid` in PHP).

| Helper | Result |
|---|---|
| `softwareOid(product)` | `<P>` |
| `releaseOid(product, major, minor, patch)` | `<P>.1.<major>.<minor>.<patch>` |
| `channelOid(product, channel)` | `<P>.2.<channel>`; an unknown channel is an error |
| `buildOid(product, run_id)` | `<P>.3.<run_id>` |
| `formatOid(product, format, compat)` | `<P>.4.<format>.<compat>` |

The generated packages also contain the channel table (`CHANNELS`) and, per product, the arc
number, the purl and the entry id. Examples:

```python
import oid
oid.release_oid(oid.PRODUCTS["catwaf"]["arc"], 3, 0, 12)   # '1.3.6.1.4.1.66963.1.11.2.1.3.0.12'
oid.channel_oid(2, oid.CHANNEL_NIGHTLY)                    # '1.3.6.1.4.1.66963.1.11.2.2.3'
```

```go
registry.ReleaseOid(registry.CatwafArc, 3, 0, 12) // "1.3.6.1.4.1.66963.1.11.2.1.3.0.12"
registry.BuildOid(registry.CatwafArc, 18204455123)  // "1.3.6.1.4.1.66963.1.11.2.3.18204455123"
```

`tests/vectors/software.json` holds the test vectors. CI runs them in every language.

## CoSWID

CoSWID tags come later (operator decision, 2026-09-30). The purl plus the OID covers the current
needs.
