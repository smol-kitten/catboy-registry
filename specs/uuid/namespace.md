# Fleet UUID namespace (arc .1.6)

`CATBOY_NAMESPACE = uuid5(NAMESPACE_OID, "1.3.6.1.4.1.66963")` = `f71da7a3-f538-5cae-b8e8-08f99e367ef3` (RFC 4122 §4.3, `NAMESPACE_OID = 6ba7b812-9dad-11d1-80b4-00c04fd430c8`).

Deterministic ids are then `uuid5(CATBOY_NAMESPACE, "<kind>:<stable key>")`, e.g. `ci:<sysid>`, `pack:<name>@<version>`, `runner:<slug>`. The constant is emitted by `tools/gen.py` (`CatboyNamespace` / `CATBOY_NAMESPACE`) and checked against this value in CI.
