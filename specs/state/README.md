# State versioning (`.1.13`) and instances (`.1.12`)

Status: **reserved**. Arcs: `1.3.6.1.4.1.66963.1.13` (this spec) and `1.3.6.1.4.1.66963.1.12`
(instances).

This spec lets every stateful system in the fleet say three things with numbers:
"the same state", "a newer state" and "a restored state". First users: CatWAF (sites and routes),
pawkit state sync and catboy-agent.

The key words MUST, MUST NOT, SHOULD and MAY are to be interpreted as in RFC 2119.

## 1. Instances (`.1.12`)

- An instance that publishes state gets one small registered number: `.1.12.<n>`.
- The name is neutral, for example `catwaf-prod-1` or `hub-a`.
- The name MUST NOT contain a hostname, a domain, a host id or an address. `tools/lint.py`
  refuses dotted names, IPv4 or IPv6 look-alikes, host ids and domain suffixes.
- A number is never reused. A retired instance gets status `deprecated`.

## 2. Fields

Each stateful system publishes these fields:

| Field | Type | Meaning |
|---|---|---|
| `system` | UUID | `uuid5(CATBOY_NAMESPACE, "state-system:<software>/<instance>/<store>")`. `<software>` is the registry name of the product (`catwaf`), `<instance>` is the `.1.12` number in decimal, `<store>` is a short store name that the product chooses (`sites`). `<store>` MUST match `^[a-z0-9][a-z0-9-]{0,31}$`, so the key has exactly two `/`. It never changes. |
| `epoch` | UUIDv7 | A new value at init and at every restore. |
| `parent_epoch` | UUID or null | The epoch that this epoch was forked from. `null` for the first epoch. |
| `fork_seq` | integer or null | The `seq` of `parent_epoch` at the restore point. `null` for the first epoch. |
| `seq` | integer | Increases by exactly 1 for every committed change in the epoch. The first epoch starts at 0. A forked epoch starts at `fork_seq`. |
| `root` | 64 hex | The state root (section 4). |
| `hlc` | uint64 | The HLC of the last committed change (section 3). A decimal string in JSON. |

`seq` is a counter, not a clock. A backup of an epoch always has a `seq` that is lower than or
equal to the live `seq` of the same epoch.

## 3. Hybrid logical clock (HLC)

### 3.1 Encoding

An HLC is one unsigned 64-bit integer:

```
hlc = (unix_ms << 16) | logical      unix_ms: 48 bits, logical: 16 bits
```

- Compare two HLCs as plain unsigned integers.
- JSON carries an HLC as a decimal string (`"117309440000000004"`), because JSON numbers lose
  precision above 2^53.
- The PHP helpers accept `unix_ms` below 2^47 (signed 64-bit integers). That limit is the year 6429.

### 3.2 Rules

Each instance keeps `last`, the HLC of its last event. `now` is the local wall clock in Unix ms.

1. **Send or local event** (every local write, every message that carries an HLC):
   `last = max(now << 16, last + 1)`.
2. **Receive** (every remote change or state document that carries `remote`):
   1. If `(remote >> 16) - now > max_drift_ms`, refuse the remote value. Do not change `last`.
      Log the skew and raise an alarm. The default `max_drift_ms` is 60000.
      Refuse the **whole** change or document that carried the value: do not apply it, and try it
      again at the next sync. A change that is applied without its HLC merged can win over a later
      local write, because that local write can get a lower `hlc`.
   2. Else `last = max(now << 16, last + 1, remote + 1)`.

These rules are the standard HLC rules (Kulkarni et al., 2014) in one integer. When the logical
counter overflows, the carry moves into the millisecond field. The order stays correct.

The generated helpers are `hlc_encode`, `hlc_decode`, `hlc_compare`, `hlc_send` and
`hlc_receive` (Python), the same names in CamelCase in Go (`HlcReceive`), and `Hlc::receive` (PHP)
and `Hlc.Receive` (C#).

### 3.3 Order of changes

- "Newer" means the higher triple `(hlc, instance, change_id)`. Compare `hlc` first, then the
  instance number, then `change_id`. A change without an instance number counts as instance 0.
  `change_id` compares as an unsigned 128-bit integer; that is the same as comparing the canonical
  lower-case UUID strings byte by byte. Every instance compares the same triple, so every instance
  picks the same winner, also when two instances share or lack a number.
- The generated helpers are `change_compare` (Python), `ChangeCompare` (Go), `Hlc::compareChange`
  (PHP) and `Hlc.CompareChange` (C#). They return -1, 0 or 1. `tests/vectors/hlc.json`
  (`change_compare`) has the vectors.
- `rev` is a per-entry edit counter. The writer sets `rev = parent rev + 1` and every receiver
  stores the received `rev`. So `rev` is part of the replicated state, not a local counter: the
  root (section 4.3) contains `rev`, and only a carried `rev` gives the same root on every instance.
  `rev` is never used to order changes.

## 4. Entries, changes and the root

### 4.1 Entry and change fields

Each entry (a CatWAF site, a route, a memory record) has:

- `id`: the entry id (uuid5, [../uuid/namespace.md](../uuid/namespace.md)).
- `rev`: the edit counter (section 3.3).
- `content_hash`: lowercase hex sha256 of the canonical JSON (RFC 8785, JCS) of the entry content.
- `hlc` and `change_id` of the last change.

Each change has `change_id` (a UUIDv7), `parent` (the `change_id` that the writer based the change
on, or `null` for a new entry), `id`, `rev`, `hlc`, `instance` and `content_hash`.

### 4.2 Concurrent edits

A received change whose `parent` is not the current head `change_id` of the entry is a
**concurrent edit**. Then the receiver:

1. keeps the change with the higher `(hlc, instance, change_id)`, by section 3.3;
2. flags a conflict for the entry and logs both `change_id` values.

The head of an entry is always the change with the highest triple that the receiver has seen.
A change whose `change_id` the receiver already knows is a duplicate: ignore it. A change that
arrives after one of its descendants (out-of-order delivery) loses by its lower triple, so the
result is correct, but it is flagged as a conflict. A transport that keeps the order of the
changes from one writer avoids these false conflicts.

Every instance applies the same rule to the same two changes, so every instance keeps the same
winner. Concurrent edits have no true order; the rule only makes the result the same everywhere.

### 4.3 Root

```
line(e) = lower(e.id) ":" decimal(e.rev) ":" lower(e.content_hash) "\n"
root    = lower_hex(sha256(concat(sort_bytewise(line(e) for every entry e))))
```

- The root of an empty store is `sha256("")` =
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Two stores with the same root hold the same entries, revisions and content.
- `state_root` (Python) and `StateRoot` (Go) implement it. `tests/vectors/state.json` has vectors.

## 5. The document `/.well-known/catboy-state`

Each system serves its fields as JSON at `/.well-known/catboy-state` on the API that it already
has. The product decides who can read it. The document contains no secret and no address.
A service with more than one store serves a JSON array of documents.

Schema: [catboy-state.schema.json](catboy-state.schema.json) (JSON Schema 2020-12). CI validates
[example.json](example.json) against it.

```json
{
  "version": 1,
  "system": "c6e68e9f-3989-5bbb-888b-f6228f3cbb21",
  "epoch": "01928f3a-6c1e-7b3d-9a41-5f0c2e7d8b19",
  "parent_epoch": "01927b10-2f4a-7c55-8e02-3d9a6b1c4f70",
  "fork_seq": 1840,
  "seq": 1873,
  "root": "f2b88f920b851482e5df17ca63b2b79d06efc2c5d497860f9e8e4c5f930c4faf",
  "hlc": "117309440000000004",
  "instance": 1,
  "software": "1.3.6.1.4.1.66963.1.11.2.1.3.0.12"
}
```

`instance` (the `.1.12` number) and `software` (a software or release OID, see
[../software/README.md](../software/README.md)) are optional.

## 6. Peer memory

- Each peer stores the last `(system, epoch, seq, root)` that it saw for every system that it
  syncs with. It MUST keep this record across restarts.
- On every contact, the peer compares the new document with the stored record by the rules in
  section 7. Then it replaces the record.
- A peer that was offline during a restore sees the new `epoch` at its next contact, and the rules
  in section 7 find the restore.

## 7. Detection rules

The peer compares the new document (`epoch`, `seq`, `root`, `parent_epoch`, `fork_seq`) with its
stored record (section 6):

1. **Same epoch, lower seq:** a restore without a new epoch. Raise an alarm.
2. **Same epoch, same seq, different root:** divergence. Raise an alarm.
3. **New epoch with a known `parent_epoch`:** a restore. Resync from `fork_seq`.
4. **New epoch without a known parent:** a new system or a lost history. Do a full resync and log it.

The other cases are normal: same epoch and higher seq means an incremental sync; same epoch, same
seq and same root means in sync. A peer logs the rule and the reason for every resync.

## 8. Epoch chain

- At init, the system mints `epoch` (UUIDv7) with `parent_epoch = null`, `fork_seq = null` and
  `seq = 0`.
- At every restore, the system mints a new `epoch` with `parent_epoch` = the epoch of the restored
  data, `fork_seq` = the `seq` of the restored data, and `seq = fork_seq`.
- The restore path MUST mint the new epoch before the system accepts a write or serves the document.
- The system keeps the chain of all its epochs, so that a peer can ask for an older link.

## 9. Restore sentinel

A system can also find its own restore, also when no peer is online.

### 9.1 Format

The sentinel is one JSON document. Schema: [sentinel.schema.json](sentinel.schema.json);
CI validates [sentinel-example.json](sentinel-example.json) against it.

```json
{"version": 1, "system": "c6e68e9f-3989-5bbb-888b-f6228f3cbb21", "epoch": "01928f3a-6c1e-7b3d-9a41-5f0c2e7d8b19", "seq": 1873, "hlc": "117309440000000004"}
```

The fields have the meanings of section 2: `system`, `epoch` and `seq` of the last commit, and
`hlc` of that commit.

### 9.2 Location

Each system defines the sentinel location and how the location stays **outside its backup set**,
in its own repository, before it claims support for this spec. Write the sentinel atomically
(write a temporary file, flush it, rename it over the old one).

### 9.3 Rules

1. The system writes the sentinel after every commit, never before the commit. So the sentinel
   `seq` is never higher than the data `seq` in normal operation.
2. At start, the system reads the sentinel and its data:
   - Sentinel `system` differs from the data `system`: a configuration error. Do not start.
   - Sentinel missing and the store is empty (`seq` 0 and no entries): first start. Write the
     sentinel and log it.
   - Sentinel missing and the store is not empty: a restore to a new host, or a lost sentinel.
     Treat it as a restore and mint a new epoch (section 8). A wrong guess costs one epoch;
     peers find the known parent and resync from `fork_seq`, which has nothing to send.
     So a move to a new host always mints one epoch, unless the operator moves the sentinel
     with the data. That cost is accepted: an undetected restore to a new host is worse.
   - Same epoch and data `seq` < sentinel `seq`: **a restore**. Mint a new epoch.
   - Data epoch differs, and the data `parent_epoch` is the sentinel epoch and the data `seq`
     equals its `fork_seq`: an earlier start minted this epoch and stopped before it wrote the
     sentinel. Write the sentinel; this is a normal start.
   - Data epoch differs in any other way: the data comes from another epoch than the last run.
     Treat it as a restore and mint a new epoch.
   - Else: a normal start.
3. After a restore, the system sets `last = max(last, sentinel hlc)` before its next HLC event,
   so its new changes order after the changes that peers saw before the restore.
4. After it mints a new epoch, the system writes the sentinel again.

The verification for every system: restore a backup while no peer is online. At the next start,
the sentinel MUST find the restore and the system MUST mint a new epoch.

## 10. Test vectors

`tests/vectors/hlc.json` (encode, send, receive with clock skew and drift, compare, change order) and
`tests/vectors/state.json` (root). CI runs the HLC vectors in Python, Go, PHP and C#, and the root
vectors in Python and Go.
