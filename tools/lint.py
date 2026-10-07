#!/usr/bin/env python3
"""Lint registry.yaml: schema shape, duplicate oids/names, parent arcs present, software and
instance entry rules, and no internal topology (IPs, private hostnames) or secrets in any tracked
file or in the generated artifacts (build/, packages/). Exit 1 on any finding."""
import re, subprocess, sys, pathlib, json
import yaml, datetime as _dt

def _load(text):
    d = yaml.safe_load(text) or {}
    for a in d.get('arcs', []):
        if isinstance(a.get('since'), _dt.date): a['since'] = a['since'].isoformat()
    return d  # PyYAML

ROOT = pathlib.Path(__file__).resolve().parents[1]
# (?<![\w.]) / (?!\.?\d): a dotted number inside a longer OID (…66963.1.11.1.1.2.3) is not an address
FORBIDDEN = [
    (re.compile(r"(?<![\w.])(10|192\.168|172\.(1[6-9]|2\d|3[01]))\.\d+\.\d+(\.\d+)?(?!\.?\d)"), "RFC 1918 address"),
    (re.compile(r"(?<![\w.])100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d+\.\d+(?!\.?\d)"), "CGNAT/overlay address"),
    (re.compile(r"(?<![\w.])\d{1,3}(\.\d{1,3}){3}(?!\.?\d)"), "IPv4 address"),
    (re.compile(r"(?i)(?<![\w:])fd[0-9a-f]{2}:[0-9a-f]{0,4}:[0-9a-f:]*"), "IPv6 ULA address"),
    (re.compile(r"\.(lan|internal|local|localdomain|home\.arpa|corp)\b"), "internal hostname suffix"),
    (re.compile(r"(?i)(?<![\w-])(ct|vm|pct|lxc)-?\d{2,4}(?![\w-])"), "internal host id"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"), "AWS access key"),
    (re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})"), "GitHub token"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\."), "JWT"),
    (re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"), "credential assignment"),
    (re.compile(r"\b(vault|kv):(secret|kv)?/?[\w-]+/[\w./-]+"), "vault key path"),
]
TOPOLOGY = {"RFC 1918 address", "CGNAT/overlay address", "IPv4 address", "IPv6 ULA address", "internal hostname suffix", "internal host id"}
SOFTWARE = re.compile(r"^1\.11\.\d+$")
INSTANCE = re.compile(r"^1\.12\.\d+$")
HOST_WORDS = {"lan", "local", "internal", "localdomain", "corp", "home", "arpa", "com", "net", "org", "cc", "systems", "localhost"}


def host_like(name: str):
    """Why an instance name looks like a host or an address, or None. Names must be neutral."""
    if "." in name: return "a dotted host name"
    parts = name.split("-")
    for i in range(len(parts) - 3):
        if all(p.isdigit() and int(p) <= 255 for p in parts[i:i + 4]): return "an IPv4 address"
    if re.search(r"(^|-)(ct|vm|pct|lxc)\d+($|-)", name): return "a host id"
    if HOST_WORDS & set(parts): return "a domain or host suffix"
    if sum(len(p) == 4 and all(c in "0123456789abcdef" for c in p) for p in parts) >= 3: return "an IPv6 address"
    return None


def scan_files():
    """Tracked files plus the generated artifacts in build/ and packages/ (git-ignored)."""
    try:
        out = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"], text=True)
        files = {ROOT / f for f in out.split("\0") if f}
    except (OSError, subprocess.CalledProcessError):
        files = {p for p in ROOT.rglob("*") if ".git" not in p.parts}
    for d in ("build", "packages"):
        files |= {p for p in (ROOT / d).rglob("*") if "__pycache__" not in p.parts}
    return sorted(p for p in files if p.is_file() and p.suffix not in {".png", ".jpg", ".pyc", ".dll", ".nupkg"})


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
    arcs = {a["oid"]: a for a in reg.get("arcs", [])}
    for a in reg.get("arcs", []):
        oid = a["oid"]
        if SOFTWARE.match(oid) and not a.get("purl"):
            findings.append(f"{oid} ({a['name']}): software entry without purl")
        if re.match(r"^1\.11\.\d+\.", oid):
            findings.append(f"{oid}: sub-arcs of a software product are minted by the product (specs/software/README.md), never registered")
        if oid.startswith("1.12.") and (why := host_like(a["name"])):
            findings.append(f"{oid}: instance name '{a['name']}' looks like {why}; use a neutral name")
        if a.get("purl") and not SOFTWARE.match(oid):
            findings.append(f"{oid}: purl is only for software entries (.1.11.<n>)")
        for ref in ("sysobjectid", "superseded_by"):
            if a.get(ref) and a[ref] not in arcs:
                findings.append(f"{oid}: {ref} {a[ref]} is not an arc in this registry")
        if a.get("superseded_by") and a["status"] != "deprecated":
            findings.append(f"{oid}: superseded_by needs status deprecated")
    for p in scan_files():
        text = p.read_text(errors="ignore")
        if "\0" in text: continue  # binary
        for rx, what in FORBIDDEN:
            for m in rx.finditer(text):
                if what == "IPv4 address" and m.group(0).startswith(("0.", "127.", "1.3.6", "2.5.", "1.2.840")):
                    continue
                shown = m.group(0) if what in TOPOLOGY else m.group(0)[:4] + "…(redacted)"  # never echo a secret into CI logs
                findings.append(f"{p.relative_to(ROOT)}: {what} '{shown}' — this repo is public; identifiers only")
                break
    st = ROOT / "specs" / "state"
    for example, schema in (("example.json", "catboy-state.schema.json"), ("sentinel-example.json", "sentinel.schema.json")):
        try:  # each state example must match its schema; the sentinel schema refers to the state schema
            import jsonschema
            from referencing import Registry, Resource
            docs = {f: json.loads((st / f).read_text()) for f in ("catboy-state.schema.json", schema)}
            reg_ = Registry().with_resources((f, Resource.from_contents(d)) for f, d in docs.items())
            jsonschema.Draft202012Validator(docs[schema], registry=reg_).validate(json.loads((st / example).read_text()))
        except ImportError:
            pass
        except FileNotFoundError as e:
            findings.append(f"specs/state: {e.filename} missing")
        except Exception as e:  # noqa: BLE001
            findings.append(f"specs/state/{example}: {getattr(e, 'message', e)}")
    for f in findings: print("LINT:", f)
    print(f"lint: {len(findings)} finding(s), {len(oids)} arcs, pen={reg.get('pen')}")
    return 1 if findings else 0

if __name__ == "__main__":
    sys.exit(main())
