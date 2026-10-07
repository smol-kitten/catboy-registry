

# --- entry ids, software OIDs and HLC (static part, tools/langs/helpers.py) -------------------
# This is the REFERENCE implementation of specs/uuid/namespace.md and specs/state/README.md.
# Go, PHP and C# must give byte-identical results (tests/vectors, CI job "cross-language").
import hashlib as _hashlib
import uuid as _uuid

_NS = _uuid.UUID(CATBOY_NAMESPACE)
_DOTS = ("\u3002", "\uff0e", "\uff61")  # ideographic, fullwidth, halfwidth full stops
_ASCII_LABEL = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_*")
_UNRESERVED = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
_PATH_RAW = _UNRESERVED | frozenset(b"!$&'()*+,;=:@/")
_HEX = frozenset(b"0123456789ABCDEFabcdef")


def software_oid(product: int) -> str:
    """OID of software product .1.11.<product>."""
    return f"{SOFTWARE}.{int(product)}"


def release_oid(product: int, major: int, minor: int, patch: int) -> str:
    return f"{software_oid(product)}.1.{int(major)}.{int(minor)}.{int(patch)}"


def channel_oid(product: int, channel: int) -> str:
    if channel not in CHANNELS:
        raise ValueError(f"unknown channel {channel}")
    return f"{software_oid(product)}.2.{channel}"


def build_oid(product: int, run_id: int) -> str:
    return f"{software_oid(product)}.3.{int(run_id)}"


def format_oid(product: int, fmt: int, compat: int) -> str:
    return f"{software_oid(product)}.4.{int(fmt)}.{int(compat)}"


def _idna_label(label: str) -> str:
    try:
        import idna  # PyPI "idna" >= 3: IDNA 2008 + UTS #46
    except ImportError as e:  # the stdlib codec is IDNA 2003 and gives different answers
        raise ImportError("canonical_domain needs the 'idna' package (pip install idna)") from e
    try:
        return idna.encode(label, uts46=True, transitional=False, std3_rules=True).decode("ascii")
    except idna.IDNAError as e:
        raise ValueError(f"invalid IDN label {label!r}: {e}") from e


def canonical_domain(domain: str) -> str:
    """specs/uuid/namespace.md, algorithm D. Raises ValueError on an invalid domain."""
    for d in _DOTS:  # D1
        domain = domain.replace(d, ".")
    if domain.endswith("."):  # D2
        domain = domain[:-1]
    if domain == "":
        raise ValueError("empty domain")
    out = []
    for label in domain.split("."):  # D3
        if label == "":
            raise ValueError("empty label")
        if label.isascii():  # D4
            label = label.lower()
            if not set(label) <= _ASCII_LABEL:
                raise ValueError(f"invalid character in label {label!r}")
        else:  # D5
            label = _idna_label(label)
        if len(label) > 63:  # D6
            raise ValueError("label longer than 63 octets")
        out.append(label)
    result = ".".join(out)
    if len(result) > 253:  # D6
        raise ValueError("domain longer than 253 octets")
    return result


def _remove_dot_segments(path: str) -> str:
    segs = path.split("/")[1:]
    out = []
    for i, seg in enumerate(segs):
        last = i == len(segs) - 1
        if seg == "." or seg == "..":
            if seg == ".." and out:
                out.pop()
            if last:
                out.append("")
        else:
            out.append(seg)
    return "/" + "/".join(out)


PATH_PROFILES = ("default", "nginx", "nginx-nomerge")


def canonical_path(path: str, profile: str = "default") -> str:
    """specs/uuid/namespace.md, algorithm P with a product profile. Raises ValueError on an
    invalid path or an unknown profile."""
    if profile not in PATH_PROFILES:
        raise ValueError(f"unknown path profile {profile!r}")
    if path == "":  # P1
        return "/"
    if not path.startswith("/"):
        raise ValueError("path must start with '/'")
    if "?" in path or "#" in path:  # P2
        raise ValueError("path must not contain '?' or '#'")
    try:
        b = path.encode("utf-8")  # P3
    except UnicodeEncodeError as e:
        raise ValueError("path is not valid Unicode") from e
    out = []
    i = 0
    while i < len(b):  # P4
        c = b[i]
        if c == 0x25:
            h = b[i + 1:i + 3]
            if len(h) != 2 or not set(h) <= _HEX:
                raise ValueError("invalid percent-escape")
            v = int(h, 16)
            out.append(chr(v) if v in _UNRESERVED else "%%%02X" % v)
            i += 3
        elif c in _PATH_RAW:
            out.append(chr(c))
            i += 1
        else:
            out.append("%%%02X" % c)
            i += 1
    s = "".join(out)
    if profile == "nginx":  # merge_slashes on: runs of '/' become one, before P5 (as nginx parses)
        while "//" in s:
            s = s.replace("//", "/")
    p = _remove_dot_segments(s)  # P5
    if profile == "default":
        return p.rstrip("/") or "/"  # P6
    return p or "/"  # nginx profiles: a trailing '/' is significant


def site_id(domain: str) -> str:
    """uuid5(CATBOY_NAMESPACE, "catwaf-site:" + canonical domain)."""
    return str(_uuid.uuid5(_NS, "catwaf-site:" + canonical_domain(domain)))


def route_id(site: str, path: str, profile: str = "default") -> str:
    """uuid5(site id, "route:" + canonical path)."""
    return str(_uuid.uuid5(_uuid.UUID(site), "route:" + canonical_path(path, profile)))


def entry_id(kind: str, key: str) -> str:
    """uuid5(CATBOY_NAMESPACE, "<kind>:<key>") for any kind in specs/uuid/namespace.md."""
    return str(_uuid.uuid5(_NS, f"{kind}:{key}"))


def oid_from_uuid(u: str) -> str:
    """ITU-T X.667: the OID form 2.25.<uuid as an unsigned 128-bit integer>."""
    return f"2.25.{_uuid.UUID(u).int}"


# HLC: 48 bits of Unix milliseconds << 16 | 16-bit logical counter, one unsigned 64-bit integer.
HLC_MAX_DRIFT_MS = 60_000


class HlcDriftError(ValueError):
    """A remote HLC is further ahead of the local clock than the allowed drift."""


def hlc_encode(ms: int, logical: int) -> int:
    if not 0 <= ms < 1 << 48 or not 0 <= logical < 1 << 16:
        raise ValueError("hlc field out of range")
    return ms << 16 | logical


def hlc_decode(h: int) -> tuple:
    return h >> 16, h & 0xFFFF


def hlc_compare(a: int, b: int) -> int:
    return (a > b) - (a < b)


def hlc_send(last: int, now_ms: int) -> int:
    """Local event or send: max(now << 16, last + 1)."""
    return max(hlc_encode(now_ms, 0), last + 1)


def hlc_receive(last: int, remote: int, now_ms: int, max_drift_ms: int = HLC_MAX_DRIFT_MS) -> int:
    """Receive: max(now << 16, last + 1, remote + 1); refuse a remote clock too far ahead."""
    if (remote >> 16) - now_ms > max_drift_ms:
        raise HlcDriftError(f"remote hlc is {(remote >> 16) - now_ms} ms ahead")
    return max(hlc_encode(now_ms, 0), last + 1, remote + 1)


def change_compare(a_hlc: int, a_instance, a_change_id: str, b_hlc: int, b_instance, b_change_id: str) -> int:
    """Order of two changes (specs/state/README.md 3.3): the triple (hlc, instance, change_id).
    A missing instance (None) counts as 0. change_id compares as an unsigned 128-bit integer."""
    a = (a_hlc, a_instance or 0, _uuid.UUID(a_change_id).int)
    b = (b_hlc, b_instance or 0, _uuid.UUID(b_change_id).int)
    return (a > b) - (a < b)

def state_root(entries) -> str:
    """sha256 over the sorted "id:rev:content_hash\\n" lines (specs/state/README.md)."""
    lines = sorted(f"{e[0].lower()}:{int(e[1])}:{e[2].lower()}\n".encode() for e in entries)
    return _hashlib.sha256(b"".join(lines)).hexdigest()
