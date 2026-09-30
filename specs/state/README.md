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
| `system` | UUID | `uuid5(CATBOY_NAMESPACE, "state-system:<software>/<instance>/<store>")`. `<software>` is the registry name of the product (`catwaf`), `<instance>` is the `.1.12` number, `<store>` is a short store name that the product chooses (`sites`). It never changes. |
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
   2. Else `last = max(now << 16, last + 1, remote + 1)`.

These rules are the standard HLC rules (Kulkarni et al., 2014) in one integer. When the logical
counter overflows, the carry moves into the millisecond field. The order stays correct.

The generated helpers are `hlc_encode`, `hlc_decode`, `hlc_compare`, `hlc_send` and
`hlc_receive` (Python), the same names in CamelCase in Go (`HlcReceive`), and `Hlc::receive` (PHP)
and `Hlc.Receive` (C#).

### 3.3 Order of changes

- "Newer" means the higher `hlc`. When two changes have the same `hlc`, the change from the higher
  instance number wins.
- `rev` is a per-entry edit counter. The writer sets `rev = parent rev + 1` and every receiver
  stores the received `rev`. `rev` is never used to order changes.

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

1. keeps the change with the higher `(hlc, instance)`, by section 3.3;
2. flags a conflict for the entry and logs both `change_id` values.

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

1. The system writes `(epoch, seq)` to a small sentinel file **outside its backup set**. It updates
   the file after every commit, never before the commit. So the sentinel seq is never higher than
   the data seq in normal operation.
2. At start, the system reads the sentinel and its data:
   - Sentinel missing: first start or a new host. Write the sentinel and log it.
   - Same epoch and data `seq` < sentinel `seq`: **a restore**. Mint a new epoch (section 8).
   - Different epoch: the data comes from another epoch than the last run. Treat it as a restore
     and mint a new epoch.
   - Else: a normal start.
3. After it mints a new epoch, the system writes the sentinel again.

## 10. Test vectors

`tests/vectors/hlc.json` (encode, send, receive with clock skew and drift, compare) and
`tests/vectors/state.json` (root). CI runs the HLC vectors in Python, Go, PHP and C#, and the root
vectors in Python and Go.
