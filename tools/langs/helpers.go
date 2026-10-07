
// --- entry ids, software OIDs and HLC (static part, tools/langs/helpers.go) ------------------
// Port of the Python reference implementation (build/python/oid.py). The results must be
// byte-identical: tests/vectors and the CI job "cross-language" check it.

var errInvalid = errors.New("catboy-registry: invalid input")

// SoftwareOid returns the OID of software product .1.11.<product>.
func SoftwareOid(product int) string { return Software + "." + strconv.Itoa(product) }

// ReleaseOid returns <product>.1.<major>.<minor>.<patch>.
func ReleaseOid(product, major, minor, patch int) string {
	return fmt.Sprintf("%s.1.%d.%d.%d", SoftwareOid(product), major, minor, patch)
}

// ChannelOid returns <product>.2.<channel>; the channel must be in the channel table.
func ChannelOid(product, channel int) (string, error) {
	if _, ok := Channels[channel]; !ok {
		return "", fmt.Errorf("%w: unknown channel %d", errInvalid, channel)
	}
	return fmt.Sprintf("%s.2.%d", SoftwareOid(product), channel), nil
}

// BuildOid returns <product>.3.<GitHub Actions run_id>.
func BuildOid(product int, runID uint64) string {
	return fmt.Sprintf("%s.3.%d", SoftwareOid(product), runID)
}

// FormatOid returns <product>.4.<format>.<compat>.
func FormatOid(product, format, compat int) string {
	return fmt.Sprintf("%s.4.%d.%d", SoftwareOid(product), format, compat)
}

var idnaProfile = idna.New(idna.MapForLookup(), idna.Transitional(false), idna.BidiRule(),
	idna.ValidateLabels(true), idna.CheckHyphens(true), idna.CheckJoiners(true), idna.StrictDomainName(true))

func isASCII(s string) bool {
	for i := 0; i < len(s); i++ {
		if s[i] >= 0x80 {
			return false
		}
	}
	return true
}

// CanonicalDomain implements specs/uuid/namespace.md, algorithm D.
func CanonicalDomain(domain string) (string, error) {
	if !utf8.ValidString(domain) {
		return "", fmt.Errorf("%w: domain is not valid UTF-8", errInvalid)
	}
	for _, d := range []string{"\u3002", "\uff0e", "\uff61"} {
		domain = strings.ReplaceAll(domain, d, ".")
	}
	domain = strings.TrimSuffix(domain, ".")
	if domain == "" {
		return "", fmt.Errorf("%w: empty domain", errInvalid)
	}
	labels := strings.Split(domain, ".")
	for i, label := range labels {
		if label == "" {
			return "", fmt.Errorf("%w: empty label", errInvalid)
		}
		if isASCII(label) {
			label = strings.ToLower(label)
			for j := 0; j < len(label); j++ {
				c := label[j]
				if !(c >= 'a' && c <= 'z' || c >= '0' && c <= '9' || c == '-' || c == '_' || c == '*') {
					return "", fmt.Errorf("%w: invalid character in label %q", errInvalid, label)
				}
			}
		} else {
			a, err := idnaProfile.ToASCII(label)
			if err != nil || strings.Contains(a, ".") {
				return "", fmt.Errorf("%w: invalid IDN label %q: %v", errInvalid, label, err)
			}
			// x/net/idna checks the hyphen rule on bytes, not code points; step D5 needs code points
			u, _ := idnaProfile.ToUnicode(a)
			r := []rune(u)
			if r[0] == '-' || r[len(r)-1] == '-' || len(r) >= 4 && r[2] == '-' && r[3] == '-' {
				return "", fmt.Errorf("%w: invalid IDN label %q: hyphen rule", errInvalid, label)
			}
			label = a
		}
		if len(label) > 63 {
			return "", fmt.Errorf("%w: label longer than 63 octets", errInvalid)
		}
		labels[i] = label
	}
	out := strings.Join(labels, ".")
	if len(out) > 253 {
		return "", fmt.Errorf("%w: domain longer than 253 octets", errInvalid)
	}
	return out, nil
}

func isUnreserved(c byte) bool {
	return c >= 'A' && c <= 'Z' || c >= 'a' && c <= 'z' || c >= '0' && c <= '9' || c == '-' || c == '.' || c == '_' || c == '~'
}

func isPathRaw(c byte) bool {
	return isUnreserved(c) || strings.IndexByte("!$&'()*+,;=:@/", c) >= 0
}

func unhex(c byte) (byte, bool) {
	switch {
	case c >= '0' && c <= '9':
		return c - '0', true
	case c >= 'a' && c <= 'f':
		return c - 'a' + 10, true
	case c >= 'A' && c <= 'F':
		return c - 'A' + 10, true
	}
	return 0, false
}

func removeDotSegments(path string) string {
	segs := strings.Split(path, "/")[1:]
	out := make([]string, 0, len(segs))
	for i, seg := range segs {
		last := i == len(segs)-1
		if seg == "." || seg == ".." {
			if seg == ".." && len(out) > 0 {
				out = out[:len(out)-1]
			}
			if last {
				out = append(out, "")
			}
		} else {
			out = append(out, seg)
		}
	}
	return "/" + strings.Join(out, "/")
}

// CanonicalPath implements specs/uuid/namespace.md, algorithm P.
func CanonicalPath(path string) (string, error) {
	if path == "" {
		return "/", nil
	}
	if path[0] != '/' {
		return "", fmt.Errorf("%w: path must start with '/'", errInvalid)
	}
	if strings.ContainsAny(path, "?#") {
		return "", fmt.Errorf("%w: path must not contain '?' or '#'", errInvalid)
	}
	if !utf8.ValidString(path) {
		return "", fmt.Errorf("%w: path is not valid UTF-8", errInvalid)
	}
	var b strings.Builder
	for i := 0; i < len(path); {
		c := path[i]
		switch {
		case c == '%':
			if i+2 >= len(path) {
				return "", fmt.Errorf("%w: truncated percent-escape", errInvalid)
			}
			hi, ok1 := unhex(path[i+1])
			lo, ok2 := unhex(path[i+2])
			if !ok1 || !ok2 {
				return "", fmt.Errorf("%w: invalid percent-escape", errInvalid)
			}
			v := hi<<4 | lo
			if isUnreserved(v) {
				b.WriteByte(v)
			} else {
				fmt.Fprintf(&b, "%%%02X", v)
			}
			i += 3
		case isPathRaw(c):
			b.WriteByte(c)
			i++
		default:
			fmt.Fprintf(&b, "%%%02X", c)
			i++
		}
	}
	p := strings.TrimRight(removeDotSegments(b.String()), "/")
	if p == "" {
		p = "/"
	}
	return p, nil
}

func parseUUID(s string) ([16]byte, error) {
	var u [16]byte
	h := strings.ReplaceAll(s, "-", "")
	if len(s) != 36 || len(h) != 32 {
		return u, fmt.Errorf("%w: not a UUID: %q", errInvalid, s)
	}
	if _, err := hex.Decode(u[:], []byte(h)); err != nil {
		return u, fmt.Errorf("%w: not a UUID: %q", errInvalid, s)
	}
	return u, nil
}

func formatUUID(u [16]byte) string {
	h := hex.EncodeToString(u[:])
	return h[0:8] + "-" + h[8:12] + "-" + h[12:16] + "-" + h[16:20] + "-" + h[20:32]
}

// UUID5 returns the RFC 9562 version 5 UUID of name in namespace ns.
func UUID5(ns, name string) (string, error) {
	n, err := parseUUID(ns)
	if err != nil {
		return "", err
	}
	h := sha1.New()
	h.Write(n[:])
	h.Write([]byte(name))
	var u [16]byte
	copy(u[:], h.Sum(nil))
	u[6] = u[6]&0x0f | 0x50
	u[8] = u[8]&0x3f | 0x80
	return formatUUID(u), nil
}

// SiteId returns uuid5(CatboyNamespace, "catwaf-site:" + canonical domain).
func SiteId(domain string) (string, error) {
	d, err := CanonicalDomain(domain)
	if err != nil {
		return "", err
	}
	return UUID5(CatboyNamespace, "catwaf-site:"+d)
}

// RouteId returns uuid5(site id, "route:" + canonical path).
func RouteId(siteID, path string) (string, error) {
	p, err := CanonicalPath(path)
	if err != nil {
		return "", err
	}
	return UUID5(siteID, "route:"+p)
}

// EntryId returns uuid5(CatboyNamespace, kind + ":" + key).
func EntryId(kind, key string) (string, error) { return UUID5(CatboyNamespace, kind+":"+key) }

// OidFromUuid returns the ITU-T X.667 OID form 2.25.<uuid as an unsigned integer>.
func OidFromUuid(u string) (string, error) {
	b, err := parseUUID(u)
	if err != nil {
		return "", err
	}
	return "2.25." + new(big.Int).SetBytes(b[:]).String(), nil
}

// HLC: 48 bits of Unix milliseconds << 16 | 16-bit logical counter (specs/state/README.md).
const HlcMaxDriftMs = 60000

// ErrHlcDrift: a remote HLC is further ahead of the local clock than the allowed drift.
var ErrHlcDrift = errors.New("catboy-registry: remote hlc ahead of local clock beyond max drift")

func HlcEncode(ms uint64, logical uint64) (uint64, error) {
	if ms >= 1<<48 || logical >= 1<<16 {
		return 0, fmt.Errorf("%w: hlc field out of range", errInvalid)
	}
	return ms<<16 | logical, nil
}

func HlcDecode(h uint64) (ms uint64, logical uint64) { return h >> 16, h & 0xffff }

func HlcCompare(a, b uint64) int {
	switch {
	case a < b:
		return -1
	case a > b:
		return 1
	}
	return 0
}

func max3(a, b, c uint64) uint64 {
	if b > a {
		a = b
	}
	if c > a {
		a = c
	}
	return a
}

// HlcSend is the local-event/send rule: max(now << 16, last + 1).
func HlcSend(last, nowMs uint64) uint64 { return max3(nowMs<<16, last+1, 0) }

// HlcReceive is the receive rule: max(now << 16, last + 1, remote + 1). It refuses a remote
// clock that is more than maxDriftMs ahead of nowMs.
func HlcReceive(last, remote, nowMs, maxDriftMs uint64) (uint64, error) {
	if remote>>16 > nowMs && remote>>16-nowMs > maxDriftMs {
		return 0, fmt.Errorf("%w: %d ms ahead", ErrHlcDrift, remote>>16-nowMs)
	}
	return max3(nowMs<<16, last+1, remote+1), nil
}

// ChangeCompare orders two changes by the triple (hlc, instance, change_id)
// (specs/state/README.md 3.3). A missing instance is 0. change_id compares as an
// unsigned 128-bit integer (the 16 UUID bytes, big-endian).
func ChangeCompare(aHlc, aInstance uint64, aChangeID string, bHlc, bInstance uint64, bChangeID string) (int, error) {
	if c := HlcCompare(aHlc, bHlc); c != 0 {
		return c, nil
	}
	if c := HlcCompare(aInstance, bInstance); c != 0 {
		return c, nil
	}
	a, err := parseUUID(aChangeID)
	if err != nil {
		return 0, err
	}
	b, err := parseUUID(bChangeID)
	if err != nil {
		return 0, err
	}
	return bytes.Compare(a[:], b[:]), nil
}

// StateRoot is sha256 over the sorted "id:rev:content_hash\n" lines.
type StateEntry struct {
	ID          string
	Rev         uint64
	ContentHash string
}

func StateRoot(entries []StateEntry) string {
	lines := make([]string, len(entries))
	for i, e := range entries {
		lines[i] = strings.ToLower(e.ID) + ":" + strconv.FormatUint(e.Rev, 10) + ":" + strings.ToLower(e.ContentHash) + "\n"
	}
	sort.Strings(lines)
	h := sha256.New()
	for _, l := range lines {
		h.Write([]byte(l))
	}
	return hex.EncodeToString(h.Sum(nil))
}
