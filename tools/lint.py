#!/usr/bin/env python3
"""Lint registry.yaml: schema shape, duplicate oids/names, parent arcs present, no internal
topology (IPs, private hostnames) anywhere in the repo. Exit 1 on any finding."""
import re, sys, pathlib, json
import yaml, datetime as _dt

def _load(text):
    d = yaml.safe_load(text) or {}
    for a in d.get('arcs', []):
        if isinstance(a.get('since'), _dt.date): a['since'] = a['since'].isoformat()
    return d  # PyYAML

ROOT = pathlib.Path(__file__).resolve().parents[1]
FORBIDDEN = [
    (re.compile(r"\b(10|192\.168|172\.(1[6-9]|2\d|3[01]))\.\d+\.\d+(\.\d+)?\b"), "RFC 1918 address"),
    (re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b"), "IPv4 address"),
    (re.compile(r"\.(lan|internal|local)\b"), "internal hostname suffix"),
]

def main() -> int:
    findings = []
    reg = _load((ROOT / "registry.yaml").read_text())
    schema = json.loads((ROOT / "schema" / "registry.schema.json").read_text())
    try:
        import jsonschema
        jsonschema.validate(reg, schema)
    except ImportError:
        findings.append("jsonschema not installed (pip install jsonschema) — schema check skipped") if "--strict" in sys.argv else None
    except Exception as e:  # noqa: BLE001
        findings.append(f"schema: {e.message if hasattr(e, 'message') else e}")
    oids, names = {}, {}
    for a in reg.get("arcs", []):
        if a["oid"] in oids: findings.append(f"duplicate oid {a['oid']} ({a['name']} vs {oids[a['oid']]})")
        if a["name"] in names: findings.append(f"duplicate name {a['name']}")
        oids[a["oid"]] = a["name"]; names[a["name"]] = a["oid"]
        parent = a["oid"].rsplit(".", 1)[0] if "." in a["oid"] else None
        if parent and parent not in oids and parent not in {x["oid"] for x in reg["arcs"]}:
            findings.append(f"{a['oid']} has no parent arc {parent}")
        if a.get("spec") and not (ROOT / a["spec"]).exists():
            findings.append(f"{a['oid']}: spec path missing: {a['spec']}")
    for p in ROOT.rglob("*"):
        if p.is_dir() or ".git" in p.parts or "build" in p.parts or p.suffix in {".png", ".jpg"}:
            continue
        text = p.read_text(errors="ignore")
        for rx, what in FORBIDDEN:
            for m in rx.finditer(text):
                if what == "IPv4 address" and m.group(0).startswith(("0.", "127.", "1.3.6", "2.5.", "1.2.840")):
                    continue
                findings.append(f"{p.relative_to(ROOT)}: {what} '{m.group(0)}' — this repo is public; identifiers only")
                break
    for f in findings: print("LINT:", f)
    print(f"lint: {len(findings)} finding(s), {len(oids)} arcs, pen={reg.get('pen')}")
    return 1 if findings else 0

if __name__ == "__main__":
    sys.exit(main())
