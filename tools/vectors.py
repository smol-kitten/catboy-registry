#!/usr/bin/env python3
"""Write tests/vectors/*.json from the Python reference implementation (build/python/oid.py).
Run tools/gen.py first. `--check` compares instead of writing (CI: committed vectors are current).
Every generated language must reproduce these files (tests/runners/*, CI job "vectors")."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build" / "python"))
import oid as o  # noqa: E402

VEC = ROOT / "tests" / "vectors"

DOMAINS = [
    "example.com", "Example.COM", "example.com.", "EXAMPLE.org.", "www.example.org",
    "Bücher.Example.", "bücher.example", "xn--bcher-kva.example", "XN--BCHER-KVA.EXAMPLE",
    "straße.example", "STRASSE.example", "Ελληνικά.example", "ΣΊΣΥΦΟΣ.example", "пример.example",
    "例え.テスト.example", "münchen。example", "café.example．", "*.example.com", "_acme.example.com",
    "a-b.example", "1.example",
    # errors: empty, empty label, bad characters, bad hyphens in an IDN label, too long
    "", ".", "a..example", ".example.com", "exa mple.com", "example.com:8443", "ab--ü.example",
    "-ü.example", "ü-.example", "α0--r.example", "a" * 64 + ".example", ".".join(["abcdefghi"] * 26),
]

PATHS = [
    "/", "", "/a", "/a/", "/a/b/", "/a//", "/A/b", "/a/%2f", "/a/%2F", "/a/%2fb", "/%7Euser", "/%7euser",
    "/%41%42%43", "/a%2Db", "/a%20b", "/a b", "/ü", "/%C3%BC", "/%c3%bc", "/./a", "/a/./b", "/a/../b",
    "/a/b/../../c", "/../a", "/a/..", "/a/.", "/a/%2E%2E/b", "/a/%2e/b", "/a/.b/..c", "/a//b",
    "/foo;bar=1/x", "/path:with@colon", "/!$&'()*+,;=", "/%25", "/%3F", "/%23",
    # errors
    "a", "/a?b", "/a#b", "/%", "/%2", "/%zz", "/a%g0",
]

SITE_DOMAIN = "example.com"


def dom_case(d):
    try:
        c = o.canonical_domain(d)
    except ValueError:
        return {"input": d, "error": True}
    s = o.site_id(d)
    return {"input": d, "canonical": c, "site_id": s, "site_oid": o.oid_from_uuid(s)}


def path_case(site, p):
    try:
        c = o.canonical_path(p)
    except ValueError:
        return {"input": p, "error": True}
    r = o.route_id(site, p)
    return {"input": p, "canonical": c, "route_id": r, "route_oid": o.oid_from_uuid(r)}


def hlc_vectors():
    t = 1790000000000  # 2026-09-21T14:13:20Z in Unix ms
    E = o.hlc_encode
    s = lambda v: str(v)  # 64-bit values as decimal strings: JSON numbers lose precision above 2^53
    enc = [{"ms": s(ms), "logical": s(lg), "hlc": s(E(ms, lg))} for ms, lg in [(0, 0), (0, 1), (1, 0), (t, 0), (t, 65535), ((1 << 47) - 1, 7)]]
    enc += [{"ms": s(ms), "logical": s(lg), "error": True} for ms, lg in [(t, 65536), (1 << 48, 0)]]
    send = [{"name": n, "last": s(last), "now": s(now), "want": s(o.hlc_send(last, now))} for n, last, now in [
        ("first event", 0, t), ("clock moved on", E(t, 3), t + 5), ("same ms", E(t, 3), t),
        ("local clock went back 2 s", E(t, 3), t - 2000), ("logical counter overflow carries into ms", E(t, 65535), t)]]
    recv = []
    for n, last, remote, now, drift in [
        ("remote behind, local clock wins", E(t, 0), E(t - 500, 9), t + 10, 60000),
        ("remote ahead within drift (skew 5 s)", E(t, 2), E(t + 5000, 4), t, 60000),
        ("same ms, remote logical higher", E(t, 2), E(t, 8), t, 60000),
        ("same ms, local logical higher", E(t, 9), E(t, 8), t, 60000),
        ("local clock behind both (skew -3 s)", E(t, 1), E(t, 1), t - 3000, 60000),
        ("all equal ms", E(t, 5), E(t, 5), t, 60000),
        ("remote exactly at the drift limit", E(t, 0), E(t + 60000, 0), t, 60000),
        ("remote 1 ms past the drift limit", E(t, 0), E(t + 60001, 0), t, 60000),
        ("remote 10 min ahead (clock skew)", E(t, 0), E(t + 600000, 0), t, 60000),
        ("remote 10 min ahead, drift allowed 1 h", E(t, 0), E(t + 600000, 3), t, 3600000),
        ("logical overflow on receive carries into ms", E(t, 65535), E(t, 65535), t, 60000),
    ]:
        c = {"name": n, "last": s(last), "remote": s(remote), "now": s(now), "max_drift_ms": s(drift)}
        try:
            c["want"] = s(o.hlc_receive(last, remote, now, drift))
        except o.HlcDriftError:
            c["error"] = "drift"
        recv.append(c)
    cmp_ = [{"a": s(a), "b": s(b), "want": o.hlc_compare(a, b)} for a, b in [(E(t, 1), E(t, 2)), (E(t, 2), E(t, 2)), (E(t + 1, 0), E(t, 65535))]]
    return {"description": "HLC = Unix ms << 16 | logical (specs/state/README.md); 64-bit values are decimal strings",
            "encode": enc, "send": send, "receive": recv, "compare": cmp_}


def main() -> int:
    check = "--check" in sys.argv
    site = o.site_id(SITE_DOMAIN)
    files = {
        "domains.json": {"description": "canonical_domain + site_id + oid_from_uuid (specs/uuid/namespace.md, algorithm D)",
                         "cases": [dom_case(d) for d in DOMAINS]},
        "paths.json": {"description": "canonical_path + route_id under the site of example.com (algorithm P)",
                       "site_domain": SITE_DOMAIN, "site_id": site, "cases": [path_case(site, p) for p in PATHS]},
        "uuid.json": {"description": "uuid5, entry ids and the X.667 2.25 OID form",
                      "namespace": o.CATBOY_NAMESPACE,
                      "oid_from_uuid": [{"uuid": u, "oid": o.oid_from_uuid(u)} for u in [
                          "00000000-0000-0000-0000-000000000000", "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
                          "ffffffff-ffff-ffff-ffff-ffffffffffff", o.CATBOY_NAMESPACE]],
                      "entry_id": [{"kind": k, "key": v, "want": o.entry_id(k, v)} for k, v in [
                          ("software", "catboy-agent"), ("software", "catwaf"), ("software", "pawkit"),
                          ("state-system", "catwaf/1/sites"), ("state-system", "pawkit/2/memory"), ("route", "/")]]},
        "software.json": {"description": "software OIDs (specs/software/README.md)",
                          "channels": [{"number": n, "name": c} for n, c in sorted(o.CHANNELS.items())],
                          "products": [{"name": k, **v} for k, v in o.PRODUCTS.items()],
                          "cases": [{"fn": "software_oid", "args": [1], "want": o.software_oid(1)},
                                    {"fn": "release_oid", "args": [1, 1, 2, 3], "want": o.release_oid(1, 1, 2, 3)},
                                    {"fn": "release_oid", "args": [2, 0, 10, 0], "want": o.release_oid(2, 0, 10, 0)},
                                    {"fn": "channel_oid", "args": [3, 1], "want": o.channel_oid(3, 1)},
                                    {"fn": "channel_oid", "args": [2, 3], "want": o.channel_oid(2, 3)},
                                    {"fn": "channel_oid", "args": [2, 9], "error": True},
                                    {"fn": "build_oid", "args": [2, 18204455123], "want": o.build_oid(2, 18204455123)},
                                    {"fn": "format_oid", "args": [3, 1, 2], "want": o.format_oid(3, 1, 2)}]},
        "hlc.json": hlc_vectors(),
        "state.json": {"description": "state root = sha256 over sorted 'id:rev:content_hash\\n' lines (specs/state/README.md)",
                       "root": [{"entries": e, "want": o.state_root(e)} for e in [
                           [],
                           [[o.site_id("example.com"), 1, "a" * 64]],
                           [[o.site_id("example.org"), 3, "B" * 64], [o.site_id("example.com"), 12, "0123456789abcdef" * 4]],
                           [[o.site_id("example.com"), 12, "0123456789abcdef" * 4], [o.site_id("example.org"), 3, "b" * 64]]]]},
    }
    stale = []
    for name, data in files.items():
        text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
        p = VEC / name
        if check:
            if not p.exists() or p.read_text() != text: stale.append(name)
        else:
            VEC.mkdir(parents=True, exist_ok=True); p.write_text(text)
    n = sum(len(v) for d in files.values() for v in d.values() if isinstance(v, list))
    if stale:
        print("vectors: stale or hand-edited:", ", ".join(stale), "- run tools/vectors.py and commit"); return 1
    print(f"vectors: {n} cases in {len(files)} files ({'checked' if check else 'written'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
