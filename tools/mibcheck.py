#!/usr/bin/env python3
"""smilint every rendered MIB in build/specs/snmp at level 6 and fail on ANY diagnostic.
smilint itself exits 0 even on severity-1 errors, so its exit code cannot gate CI.
Accepted, listed diagnostics only: CATBOY-SMI is an SMI module, not a *-MIB (like SNMPv2-SMI)."""
import os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MIBS = ROOT / "build" / "specs" / "snmp"
IGNORE = {"CATBOY-SMI": ["module-name-suffix"]}
env = dict(os.environ, SMIPATH=f"{ROOT / 'templates' / 'snmp' / 'base'}:{MIBS}")
files = sorted(MIBS.glob("*.txt"))
if not files:
    print("mibcheck: no rendered MIBs - run tools/gen.py first"); sys.exit(1)
bad = 0
for f in files:
    args = ["smilint", "-l", "6", "-s", "-m"] + [f"-i{i}" for i in IGNORE.get(f.stem, [])] + [str(f)]
    r = subprocess.run(args, env=env, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if out:
        bad += 1; print(out)
    print(f"mibcheck: {f.stem}: {'FAIL' if out else 'ok'}")
sys.exit(1 if bad else 0)
