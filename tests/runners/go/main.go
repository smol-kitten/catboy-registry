// Command runner checks the generated Go package (build/go) against tests/vectors
// (`runner vectors <dir>`) or prints fuzz output (`runner fuzz <input.json>`, the format of tools/fuzz.py).
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"

	registry "github.com/smol-kitten/catboy-registry/go"
)

var n int
var fails []string

func check(what string, got, want any) {
	n++
	if !reflect.DeepEqual(got, want) {
		fails = append(fails, fmt.Sprintf("%s: got %v, want %v", what, got, want))
	}
}

func load(dir, name string, v any) {
	b, err := os.ReadFile(filepath.Join(dir, name))
	if err == nil {
		err = json.Unmarshal(b, v)
	}
	if err != nil {
		fmt.Println("FAIL load", name, err)
		os.Exit(1)
	}
}

func u64(s string) uint64 {
	v, err := strconv.ParseUint(s, 10, 64)
	if err != nil {
		panic(err)
	}
	return v
}

func orErr(s string, err error) string {
	if err != nil {
		return "ERR"
	}
	return s
}

type idCase struct {
	Input     string `json:"input"`
	Error     bool   `json:"error"`
	Canonical string `json:"canonical"`
	SiteID    string `json:"site_id"`
	SiteOid   string `json:"site_oid"`
	RouteID   string `json:"route_id"`
	RouteOid  string `json:"route_oid"`
}

func vectors(dir string) int {
	var dom struct{ Cases []idCase }
	load(dir, "domains.json", &dom)
	for _, c := range dom.Cases {
		got := orErr(registry.CanonicalDomain(c.Input))
		if c.Error {
			check("domain "+strconv.Quote(c.Input), got, "ERR")
			continue
		}
		check("domain "+strconv.Quote(c.Input), got, c.Canonical)
		check("site_id "+strconv.Quote(c.Input), orErr(registry.SiteId(c.Input)), c.SiteID)
		check("site_oid "+strconv.Quote(c.Input), orErr(registry.OidFromUuid(c.SiteID)), c.SiteOid)
	}
	var paths struct {
		SiteDomain string `json:"site_domain"`
		SiteID     string `json:"site_id"`
		Cases      []idCase
	}
	load(dir, "paths.json", &paths)
	check("site_id example.com", orErr(registry.SiteId(paths.SiteDomain)), paths.SiteID)
	for _, c := range paths.Cases {
		got := orErr(registry.CanonicalPath(c.Input))
		if c.Error {
			check("path "+strconv.Quote(c.Input), got, "ERR")
			continue
		}
		check("path "+strconv.Quote(c.Input), got, c.Canonical)
		check("route_id "+strconv.Quote(c.Input), orErr(registry.RouteId(paths.SiteID, c.Input)), c.RouteID)
		check("route_oid "+strconv.Quote(c.Input), orErr(registry.OidFromUuid(c.RouteID)), c.RouteOid)
	}
	var uu struct {
		Namespace   string                             `json:"namespace"`
		OidFromUuid []struct{ UUID, Oid string }       `json:"oid_from_uuid"`
		EntryID     []struct{ Kind, Key, Want string } `json:"entry_id"`
	}
	load(dir, "uuid.json", &uu)
	check("namespace", registry.CatboyNamespace, uu.Namespace)
	for _, c := range uu.OidFromUuid {
		check("oid_from_uuid "+c.UUID, orErr(registry.OidFromUuid(c.UUID)), c.Oid)
	}
	for _, c := range uu.EntryID {
		check("entry_id "+c.Kind+":"+c.Key, orErr(registry.EntryId(c.Kind, c.Key)), c.Want)
	}
	var sw struct {
		Channels []struct {
			Number int
			Name   string
		}
		Products []struct {
			Name, Oid, ID, Purl string
			Arc                 int
		}
		Cases []struct {
			Fn    string
			Args  []uint64
			Want  string
			Error bool
		}
	}
	load(dir, "software.json", &sw)
	check("channel count", len(registry.Channels), len(sw.Channels))
	for _, c := range sw.Channels {
		check("channel "+c.Name, registry.Channels[c.Number], c.Name)
	}
	ids := map[string]string{"catboy-agent": registry.CatboyAgentId, "catwaf": registry.CatwafId, "pawkit": registry.PawkitId}
	for _, p := range sw.Products {
		check("product "+p.Name, ids[p.Name], p.ID)
		check("product "+p.Name+" oid", registry.SoftwareOid(p.Arc), p.Oid)
	}
	for _, c := range sw.Cases {
		a := c.Args
		var got string
		switch c.Fn {
		case "software_oid":
			got = registry.SoftwareOid(int(a[0]))
		case "release_oid":
			got = registry.ReleaseOid(int(a[0]), int(a[1]), int(a[2]), int(a[3]))
		case "channel_oid":
			got = orErr(registry.ChannelOid(int(a[0]), int(a[1])))
		case "build_oid":
			got = registry.BuildOid(int(a[0]), a[1])
		case "format_oid":
			got = registry.FormatOid(int(a[0]), int(a[1]), int(a[2]))
		}
		want := c.Want
		if c.Error {
			want = "ERR"
		}
		check(fmt.Sprint(c.Fn, a), got, want)
	}
	var h struct {
		Encode []struct {
			Ms, Logical, Hlc string
			Error            bool
		}
		Send    []struct{ Name, Last, Now, Want string }
		Receive []struct {
			Name, Last, Remote, Now, Want, Error string
			MaxDriftMs                           string `json:"max_drift_ms"`
		}
		Compare []struct {
			A, B string
			Want int
		}
	}
	load(dir, "hlc.json", &h)
	for _, c := range h.Encode {
		v, err := registry.HlcEncode(u64(c.Ms), u64(c.Logical))
		if c.Error {
			check("hlc_encode "+c.Ms+","+c.Logical, err != nil, true)
			continue
		}
		check("hlc_encode "+c.Ms+","+c.Logical, v, u64(c.Hlc))
		ms, lg := registry.HlcDecode(u64(c.Hlc))
		check("hlc_decode "+c.Hlc, [2]uint64{ms, lg}, [2]uint64{u64(c.Ms), u64(c.Logical)})
	}
	for _, c := range h.Send {
		check("hlc_send "+c.Name, registry.HlcSend(u64(c.Last), u64(c.Now)), u64(c.Want))
	}
	for _, c := range h.Receive {
		v, err := registry.HlcReceive(u64(c.Last), u64(c.Remote), u64(c.Now), u64(c.MaxDriftMs))
		got := strconv.FormatUint(v, 10)
		if errors.Is(err, registry.ErrHlcDrift) {
			got = "drift"
		}
		want := c.Want
		if c.Error != "" {
			want = c.Error
		}
		check("hlc_receive "+c.Name, got, want)
	}
	for _, c := range h.Compare {
		check("hlc_compare "+c.A+","+c.B, registry.HlcCompare(u64(c.A), u64(c.B)), c.Want)
	}
	var st struct {
		Root []struct {
			Entries [][]any
			Want    string
		}
	}
	load(dir, "state.json", &st)
	for _, c := range st.Root {
		es := make([]registry.StateEntry, len(c.Entries))
		for i, e := range c.Entries {
			es[i] = registry.StateEntry{ID: e[0].(string), Rev: uint64(e[1].(float64)), ContentHash: e[2].(string)}
		}
		check(fmt.Sprintf("state_root %d entries", len(es)), registry.StateRoot(es), c.Want)
	}
	for _, f := range fails {
		fmt.Println("FAIL", f)
	}
	fmt.Printf("go: %d/%d vector checks passed\n", n-len(fails), n)
	if len(fails) > 0 {
		return 1
	}
	return 0
}

func fuzz(path string) int {
	var in struct{ Domains, Paths []string }
	b, err := os.ReadFile(path)
	if err == nil {
		err = json.Unmarshal(b, &in)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	site, _ := registry.SiteId("example.com")
	var sb strings.Builder
	for _, d := range in.Domains {
		s, err := registry.SiteId(d)
		if err != nil {
			sb.WriteString("D\tERR\t-\t-\n")
			continue
		}
		c, _ := registry.CanonicalDomain(d)
		o, _ := registry.OidFromUuid(s)
		fmt.Fprintf(&sb, "D\t%s\t%s\t%s\n", c, s, o)
	}
	for _, p := range in.Paths {
		r, err := registry.RouteId(site, p)
		if err != nil {
			sb.WriteString("P\tERR\t-\t-\n")
			continue
		}
		c, _ := registry.CanonicalPath(p)
		o, _ := registry.OidFromUuid(r)
		fmt.Fprintf(&sb, "P\t%s\t%s\t%s\n", c, r, o)
	}
	os.Stdout.WriteString(sb.String())
	return 0
}

func main() {
	if len(os.Args) > 2 && os.Args[1] == "fuzz" {
		os.Exit(fuzz(os.Args[2]))
	}
	dir := "../../vectors"
	if len(os.Args) > 2 {
		dir = os.Args[2]
	}
	os.Exit(vectors(dir))
}
