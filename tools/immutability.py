#!/usr/bin/env python3
"""Refuse changes to the number, name or purpose of any arc that already exists on the base
ref (default: origin/main). Only `status` (and `spec`, `owner`) may change; arcs may be added."""
import subprocess, sys, pathlib, yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = sys.argv[1] if len(sys.argv) > 1 else "origin/main"

def load(text): return {a["oid"]: a for a in (yaml.safe_load(text) or {}).get("arcs", [])}

try:
    old = load(subprocess.check_output(["git", "-C", str(ROOT), "show", f"{BASE}:registry.yaml"], text=True))
except subprocess.CalledProcessError:
    print(f"immutability: no {BASE}:registry.yaml (first commit) — nothing to compare"); sys.exit(0)
new = load((ROOT / "registry.yaml").read_text())
bad = []
for oid, a in old.items():
    if oid not in new: bad.append(f"{oid} ({a['name']}) removed — arcs are never removed, set status: deprecated")
    else:
        for k in ("name", "purpose", "since"):
            if new[oid].get(k) != a.get(k): bad.append(f"{oid}: {k} changed '{a.get(k)}' -> '{new[oid].get(k)}' (immutable)")
        if a["status"] == "deprecated" and new[oid]["status"] != "deprecated":
            bad.append(f"{oid}: deprecated arcs stay deprecated")
for b in bad: print("IMMUTABILITY:", b)
print(f"immutability: {len(bad)} violation(s), {len(new) - len(old)} new arc(s)")
sys.exit(1 if bad else 0)
