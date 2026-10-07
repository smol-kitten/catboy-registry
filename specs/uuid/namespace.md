# Fleet UUID namespace (arc .1.6)

`CATBOY_NAMESPACE = uuid5(NAMESPACE_OID, "1.3.6.1.4.1.66963")` = `f71da7a3-f538-5cae-b8e8-08f99e367ef3` (RFC 4122 §4.3, `NAMESPACE_OID = 6ba7b812-9dad-11d1-80b4-00c04fd430c8`).

Deterministic ids are then `uuid5(CATBOY_NAMESPACE, "<kind>:<stable key>")`, e.g. `ci:<sysid>`, `pack:<name>@<version>`, `runner:<slug>`. The constant is emitted by `tools/gen.py` (`CatboyNamespace` / `CATBOY_NAMESPACE`) and checked against this value in CI.

## Kinds

`<kind>` is a fixed prefix. A kind keeps its meaning forever. The stable key after the colon is
the canonical form below. Two instances that never talk to each other compute the same id.

| Kind | Name (the uuid5 input) | Namespace | Example key |
|---|---|---|---|
| `catwaf-site` | `catwaf-site:` + canonical domain (algorithm D) | `CATBOY_NAMESPACE` | `catwaf-site:xn--bcher-kva.example` |
| `route` | `route:` + canonical path (algorithm P) | **the site id**, not `CATBOY_NAMESPACE` | `route:/api/v1` |
| `state-system` | `state-system:<software>/<instance>/<store>` ([../state/README.md](../state/README.md)) | `CATBOY_NAMESPACE` | `state-system:catwaf/1/sites` |
| `software` | `software:` + registry name of a `.1.11` product | `CATBOY_NAMESPACE` | `software:catwaf` |

- Site id = `uuid5(CATBOY_NAMESPACE, "catwaf-site:" + D(domain))`.
- Route id = `uuid5(site id, "route:" + P(path))`.
- A change id is a UUIDv7 (RFC 9562), not a uuid5. It needs no namespace.
- A site keeps its id when its domain changes later: compute the id once, at creation, and store it.

The generated helpers are `site_id(domain)`, `route_id(site_id, path)`, `entry_id(kind, key)`,
`canonical_domain`, `canonical_path` and `oid_from_uuid` (Python). Go and C# use CamelCase
(`SiteId`, `RouteId`, `OidFromUuid`); PHP uses `Ids::siteId`, `Ids::routeId` and `Ids::oidFromUuid`.

## Algorithm D: domain canonicalization

The input is a Unicode string. The result is an ASCII string, or an error.

1. Replace every U+3002, U+FF0E and U+FF61 (the ideographic, fullwidth and halfwidth full stops)
   with `.` (U+002E).
2. If the string ends with `.`, remove that one dot. If the string is then empty, fail.
3. Split the string at `.` into labels. If a label is empty, fail.
4. **ASCII label** (all code points below U+0080): convert `A`–`Z` to `a`–`z`. If the label has
   a character that is not `a`–`z`, `0`–`9`, `-`, `_` or `*`, fail. Do not change the label in any
   other way. An `xn--` label stays as it is, in lower case.
5. **Other label**: apply UTS #46 ToASCII to the label with nontransitional processing,
   `UseSTD3ASCIIRules=true`, `CheckHyphens=true`, `CheckBidi=true`, `CheckJoiners=true` and
   `VerifyDnsLength=false`. The result is the IDNA A-label. Fail on any UTS #46 error, and fail
   if the result contains a `.`. Also fail when the mapped U-label starts or ends with `-`, or has
   `-` at both code point 3 and code point 4 (the CheckHyphens rule; some libraries skip it or
   count bytes).
6. If a label is longer than 63 octets or the joined result is longer than 253 octets, fail.
7. Join the labels with `.`. The result has no trailing dot.

Examples: `Bücher.Example.` → `xn--bcher-kva.example`; `Example.COM` → `example.com`;
`münchen。example` → `xn--mnchen-3ya.example`; `straße.example` → `xn--strae-oqa.example`
(nontransitional: `ß` stays).

## Algorithm P: path canonicalization

The input is the path part of a URL, as a Unicode string. The result is an ASCII string, or an
error.

1. If the path is empty, the result is `/`. Else the path MUST start with `/`; if not, fail.
2. If the path contains `?` or `#`, fail. The query and the fragment are not part of a route.
3. Encode the path as UTF-8. If it is not valid Unicode, fail.
4. Read the octets from left to right:
   - `%` followed by two hex digits: decode the octet. If the octet is an unreserved character
     (`A`–`Z`, `a`–`z`, `0`–`9`, `-`, `.`, `_`, `~`), write the character. Else write `%` and
     the two hex digits in **upper case**. So `%2f` and `%2F` both give `%2F`, and `%7e` gives `~`.
   - `%` without two hex digits after it: fail.
   - An unreserved character, a sub-delimiter (`!$&'()*+,;=`), `:`, `@` or `/`: write it as it is.
   - Any other octet (a space, a non-ASCII octet, `"<>\^`{|}`): write `%` and two upper-case
     hex digits.
5. Remove the dot segments with the `remove_dot_segments` algorithm of RFC 3986, section 5.2.4.
   Step 4 runs first, so `%2E%2E` counts as `..`.
6. Remove all trailing `/`. If the result is then empty, the result is `/`.

The algorithm does not change the case of the path, and it does not merge `//`.

### Profiles

A product that routes by path gives its routes ids that follow its own routing rules, so two
paths that the product treats as one route get one id, and two that it treats as different get two.
The profile is a parameter of algorithm P. It does not change the uuid5 name (`route:` + result).

| Profile | Repeated `/` | Trailing `/` | Use |
|---|---|---|---|
| `default` | kept | removed (step 6) | product-neutral ids |
| `nginx` | merged to one, before step 5 | kept (`/api` and `/api/` differ) | nginx with `merge_slashes on` (the nginx default; CatWAF) |
| `nginx-nomerge` | kept | kept | nginx with `merge_slashes off` |

- `nginx`: after step 4, replace every run of `/` with one `/`, then run step 5. This is the nginx
  order: `/a//../b` gives `/b`.
- The nginx profiles skip step 6. An empty result is `/`.
- An unknown profile is an error.
- Known difference: nginx matches locations on the decoded URI, so it treats `%2F` as `/`. All profiles keep
  `%2F` encoded (step 4). A product route that contains `%2F` therefore gets its own id.

CatWAF uses `nginx`, or `nginx-nomerge` on a site with `merge_slashes off`. The helpers take the
profile as an optional last argument (`canonical_path(path, profile)`, `route_id(site, path,
profile)`; Go `CanonicalPathProfile` and `RouteIdProfile`). `tests/vectors/paths.json`
(`profile_cases`) has the vectors, and the CI fuzz run compares the profiles in all four languages.

Examples: `/a/` → `/a`; `/a/%2f` → `/a/%2F`; `/a/./b/../c/` → `/a/c`; `/%7Euser` → `/~user`;
`/ü` → `/%C3%BC`; `/..` → `/`.

## Reference implementation and cross-language check

- The Python code in `build/python/oid.py` (from `tools/langs/helpers.py`) is the reference
  implementation. It uses the PyPI package `idna` (IDNA 2008 with UTS #46) for step D5. The
  standard library codec `encodings.idna` is IDNA 2003 and gives different results. Do not use it.
- Go uses `golang.org/x/net/idna`, PHP uses `idn_to_ascii` from ext-intl (ICU), and C# uses
  `System.Globalization.IdnMapping` (ICU on Linux).
- `tests/vectors/domains.json`, `paths.json` and `uuid.json` hold the fixed test vectors. CI runs
  them in all four languages.
- CI also generates 1000 random domains and 1000 random paths (`tools/fuzz.py`) for every run,
  runs every language on them and requires byte-identical output.

## OID form of a UUID

Where an OID is needed for an entry id, use the ITU-T X.667 (ISO/IEC 9834-8) form
`2.25.<the UUID as an unsigned 128-bit decimal integer>`. Example:
`f81d4fae-7dec-11d0-a765-00a0c91e6bf6` → `2.25.329800735698586629295641978511506172918`.
The helper is `oid_from_uuid`. No registry entry is needed for these OIDs.
