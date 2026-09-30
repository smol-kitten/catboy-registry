#!/usr/bin/env python3
"""Cross-language canonicalization check (specs/uuid/namespace.md).
  fuzz.py gen <seed> [n]   -> JSON {"domains": [...], "paths": [...]} with n random inputs each
  fuzz.py compare a b ...  -> exit 1 unless all output files are byte-identical
Each tests/runners/<lang> prints, per input: D|P <TAB> canonical or ERR <TAB> id or - <TAB> 2.25 OID or -."""
import json, pathlib, random, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

ASCII = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
UNI = "äöüßéèêàçñøåÄÖÜÉÑÅαβγδεζλμπσςΣΩабвгджзийЖЗИЯ中文网络日本語テストカタ한국어"
PATH_CH = ASCII + "-._~!$&'()*+,;=:@ " + "üé中"
HEX = "0123456789abcdefABCDEF"


def rand_label(r: random.Random) -> str:
    k = r.random()
    n = r.randint(1, 12)
    if k < 0.45:
        s = "".join(r.choice(ASCII) for _ in range(n))
    elif k < 0.9:
        s = "".join(r.choice(ASCII + UNI * 2) for _ in range(n))
    elif k < 0.95:
        s = "".join(r.choice(ASCII) for _ in range(r.randint(60, 70)))
    else:
        s = "".join(r.choice(ASCII + UNI + " !-_*") for _ in range(n))
    if len(s) > 2 and r.random() < 0.15:  # an inner hyphen
        i = r.randint(1, len(s) - 2); s = s[:i] + "-" + s[i + 1:]
    return s


def rand_domain(r: random.Random) -> str:
    d = ".".join(rand_label(r) for _ in range(r.randint(1, 4))) + r.choice([".example", ".example.com", ".EXAMPLE.org", ""])
    k = r.random()
    if k < 0.15: d += "."
    elif k < 0.2: d = d.replace(".", "\u3002", 1)
    elif k < 0.23: d = d.replace(".", "..", 1)
    return d


def rand_segment(r: random.Random) -> str:
    k = r.random()
    if k < 0.1: return r.choice([".", "..", "", "%2e", "%2E%2e"])
    out = []
    for _ in range(r.randint(1, 8)):
        if r.random() < 0.2:
            out.append("%" + r.choice(HEX) + r.choice(HEX) if r.random() < 0.95 else "%" + r.choice(HEX + "zg"))
        else:
            out.append(r.choice(PATH_CH))
    return "".join(out)


def rand_path(r: random.Random) -> str:
    p = "/" + "/".join(rand_segment(r) for _ in range(r.randint(0, 5)))
    if r.random() < 0.3: p += "/"
    if r.random() < 0.02: p = p.lstrip("/")
    return p


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "gen":
        r = random.Random(sys.argv[2])
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
        json.dump({"domains": [rand_domain(r) for _ in range(n)], "paths": [rand_path(r) for _ in range(n)]}, sys.stdout, ensure_ascii=False)
        return 0
    if cmd == "compare":
        files = sys.argv[2:]
        ref = pathlib.Path(files[0]).read_text().splitlines()
        bad = 0
        for f in files[1:]:
            got = pathlib.Path(f).read_text().splitlines()
            if len(got) != len(ref):
                print(f"{f}: {len(got)} lines, {files[0]} has {len(ref)}"); bad += 1; continue
            diff = [i for i, (a, b) in enumerate(zip(ref, got)) if a != b]
            for i in diff[:20]:
                print(f"{f} line {i + 1}:\n  {files[0]}: {ref[i]}\n  {f}: {got[i]}")
            if diff: print(f"{f}: {len(diff)} of {len(ref)} lines differ"); bad += 1
        errs = sum(1 for l in ref if "\tERR\t" in l)
        print(f"fuzz: {len(files)} outputs, {len(ref)} lines each ({errs} errors), {'IDENTICAL' if not bad else f'{bad} DIFFER'}")
        return 1 if bad else 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main())
