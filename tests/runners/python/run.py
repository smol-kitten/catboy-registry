#!/usr/bin/env python3
"""Check build/python/oid.py against tests/vectors (`run.py vectors`) or print fuzz output
(`run.py fuzz <input.json>`, the format of tools/fuzz.py)."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "build" / "python"))
import oid as o  # noqa: E402

FNS = {"software_oid": o.software_oid, "release_oid": o.release_oid, "channel_oid": o.channel_oid,
       "build_oid": o.build_oid, "format_oid": o.format_oid}


def vectors(vec: pathlib.Path) -> int:
    fails, n = [], 0

    def check(what, got, want):
        nonlocal n
        n += 1
        if got != want: fails.append(f"{what}: got {got!r}, want {want!r}")

    def err(fn, *a):
        try:
            return fn(*a)
        except ValueError:
            return "ERR"

    for c in json.loads((vec / "domains.json").read_text())["cases"]:
        if c.get("error"):
            check(f"domain {c['input']!r}", err(o.canonical_domain, c["input"]), "ERR"); continue
        check(f"domain {c['input']!r}", o.canonical_domain(c["input"]), c["canonical"])
        check(f"site_id {c['input']!r}", o.site_id(c["input"]), c["site_id"])
        check(f"site_oid {c['input']!r}", o.oid_from_uuid(c["site_id"]), c["site_oid"])
    p = json.loads((vec / "paths.json").read_text())
    check("site_id example.com", o.site_id(p["site_domain"]), p["site_id"])
    for c in p["cases"]:
        if c.get("error"):
            check(f"path {c['input']!r}", err(o.canonical_path, c["input"]), "ERR"); continue
        check(f"path {c['input']!r}", o.canonical_path(c["input"]), c["canonical"])
        check(f"route_id {c['input']!r}", o.route_id(p["site_id"], c["input"]), c["route_id"])
        check(f"route_oid {c['input']!r}", o.oid_from_uuid(c["route_id"]), c["route_oid"])
    for c in p["profile_cases"]:
        what = f"path[{c['profile']}] {c['input']!r}"
        if c.get("error"):
            check(what, err(o.canonical_path, c["input"], c["profile"]), "ERR"); continue
        check(what, o.canonical_path(c["input"], c["profile"]), c["canonical"])
        check(f"route_id[{c['profile']}] {c['input']!r}", o.route_id(p["site_id"], c["input"], c["profile"]), c["route_id"])
    u = json.loads((vec / "uuid.json").read_text())
    check("namespace", o.CATBOY_NAMESPACE, u["namespace"])
    for c in u["oid_from_uuid"]: check(f"oid_from_uuid {c['uuid']}", o.oid_from_uuid(c["uuid"]), c["oid"])
    for c in u["entry_id"]: check(f"entry_id {c['kind']}:{c['key']}", o.entry_id(c["kind"], c["key"]), c["want"])
    s = json.loads((vec / "software.json").read_text())
    check("channels", [{"number": k, "name": v} for k, v in sorted(o.CHANNELS.items())], s["channels"])
    for pr in s["products"]:
        check(f"product {pr['name']}", o.PRODUCTS[pr["name"]]["id"], pr["id"])
        check(f"product {pr['name']} oid", o.software_oid(pr["arc"]), pr["oid"])
    for c in s["cases"]:
        check(f"{c['fn']}{c['args']}", err(FNS[c["fn"]], *c["args"]), "ERR" if c.get("error") else c["want"])
    h = json.loads((vec / "hlc.json").read_text())
    for c in h["encode"]:
        check(f"hlc_encode {c['ms']},{c['logical']}", err(o.hlc_encode, int(c["ms"]), int(c["logical"])),
              "ERR" if c.get("error") else int(c["hlc"]))
        if not c.get("error"): check(f"hlc_decode {c['hlc']}", o.hlc_decode(int(c["hlc"])), (int(c["ms"]), int(c["logical"])))
    for c in h["send"]: check(f"hlc_send {c['name']}", o.hlc_send(int(c["last"]), int(c["now"])), int(c["want"]))
    for c in h["receive"]:
        try:
            got = o.hlc_receive(int(c["last"]), int(c["remote"]), int(c["now"]), int(c["max_drift_ms"]))
        except o.HlcDriftError:
            got = "drift"
        check(f"hlc_receive {c['name']}", got, c.get("error") or int(c["want"]))
    for c in h["compare"]: check(f"hlc_compare {c['a']},{c['b']}", o.hlc_compare(int(c["a"]), int(c["b"])), c["want"])
    for c in h["change_compare"]:
        a, b = c["a"], c["b"]
        check(f"change_compare {c['name']}", err(o.change_compare, int(a["hlc"]), a["instance"], a["change_id"], int(b["hlc"]), b["instance"], b["change_id"]),
              "ERR" if c.get("error") else c["want"])
    for c in json.loads((vec / "state.json").read_text())["root"]:
        check(f"state_root {len(c['entries'])} entries", o.state_root(c["entries"]), c["want"])
    for f in fails: print("FAIL", f)
    print(f"python: {n - len(fails)}/{n} vector checks passed")
    return 1 if fails else 0


def fuzz(path: str) -> int:
    data = json.loads(pathlib.Path(path).read_text())
    site = o.site_id("example.com")
    out = []
    for d in data["domains"]:
        try:
            s = o.site_id(d); out.append(f"D\t{o.canonical_domain(d)}\t{s}\t{o.oid_from_uuid(s)}")
        except ValueError:
            out.append("D\tERR\t-\t-")
    for p in data["paths"]:
        try:
            r = o.route_id(site, p); out.append(f"P\t{o.canonical_path(p)}\t{r}\t{o.oid_from_uuid(r)}")
        except ValueError:
            out.append("P\tERR\t-\t-")
        for tag, prof in (("N", "nginx"), ("M", "nginx-nomerge")):
            try:
                out.append(f"{tag}\t{o.canonical_path(p, prof)}\t{o.route_id(site, p, prof)}")
            except ValueError:
                out.append(f"{tag}\tERR\t-")
    sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "fuzz":
        sys.exit(fuzz(sys.argv[2]))
    sys.exit(vectors(pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "tests" / "vectors"))
