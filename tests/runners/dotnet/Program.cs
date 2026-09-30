// Checks build/dotnet against tests/vectors (`dotnet run -- vectors [dir]`) or prints fuzz output
// (`dotnet run -- fuzz <input.json>`, the format of tools/fuzz.py).
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using Catboy.Registry;

static class Program
{
    static int n;
    static readonly List<string> Fails = new();

    static void Check(string what, object? got, object? want)
    {
        n++;
        if (!Equals(got, want)) Fails.Add($"{what}: got {got}, want {want}");
    }

    static string OrErr(Func<string> f)
    {
        try { return f(); } catch (ArgumentException) { return "ERR"; }
    }

    static JsonElement Load(string dir, string name) => JsonDocument.Parse(File.ReadAllText(Path.Combine(dir, name))).RootElement;
    static string S(JsonElement e, string k) => e.GetProperty(k).GetString()!;
    static bool Err(JsonElement e) => e.TryGetProperty("error", out var v) && v.ValueKind != JsonValueKind.False;
    static ulong U(JsonElement e, string k) => ulong.Parse(S(e, k));

    static int Vectors(string dir)
    {
        foreach (var c in Load(dir, "domains.json").GetProperty("cases").EnumerateArray())
        {
            var input = S(c, "input");
            var got = OrErr(() => Ids.CanonicalDomain(input));
            if (Err(c)) { Check($"domain '{input}'", got, "ERR"); continue; }
            Check($"domain '{input}'", got, S(c, "canonical"));
            Check($"site_id '{input}'", Ids.SiteId(input), S(c, "site_id"));
            Check($"site_oid '{input}'", Ids.OidFromUuid(S(c, "site_id")), S(c, "site_oid"));
        }
        var p = Load(dir, "paths.json");
        Check("site_id example.com", Ids.SiteId(S(p, "site_domain")), S(p, "site_id"));
        foreach (var c in p.GetProperty("cases").EnumerateArray())
        {
            var input = S(c, "input");
            var got = OrErr(() => Ids.CanonicalPath(input));
            if (Err(c)) { Check($"path '{input}'", got, "ERR"); continue; }
            Check($"path '{input}'", got, S(c, "canonical"));
            Check($"route_id '{input}'", Ids.RouteId(S(p, "site_id"), input), S(c, "route_id"));
            Check($"route_oid '{input}'", Ids.OidFromUuid(S(c, "route_id")), S(c, "route_oid"));
        }
        var u = Load(dir, "uuid.json");
        Check("namespace", Oid.CatboyNamespace, S(u, "namespace"));
        foreach (var c in u.GetProperty("oid_from_uuid").EnumerateArray()) Check($"oid_from_uuid {S(c, "uuid")}", Ids.OidFromUuid(S(c, "uuid")), S(c, "oid"));
        foreach (var c in u.GetProperty("entry_id").EnumerateArray()) Check($"entry_id {S(c, "kind")}:{S(c, "key")}", Ids.EntryId(S(c, "kind"), S(c, "key")), S(c, "want"));
        var s = Load(dir, "software.json");
        var chans = s.GetProperty("channels").EnumerateArray().ToList();
        Check("channel count", Oid.Channels.Count, chans.Count);
        foreach (var c in chans) Check($"channel {S(c, "name")}", Oid.Channels[c.GetProperty("number").GetInt32()], S(c, "name"));
        var ids = new Dictionary<string, string> { ["catboy-agent"] = Oid.CatboyAgentId, ["catwaf"] = Oid.CatwafId, ["pawkit"] = Oid.PawkitId };
        foreach (var pr in s.GetProperty("products").EnumerateArray())
        {
            Check($"product {S(pr, "name")}", ids[S(pr, "name")], S(pr, "id"));
            Check($"product {S(pr, "name")} oid", Ids.SoftwareOid(pr.GetProperty("arc").GetInt32()), S(pr, "oid"));
        }
        foreach (var c in s.GetProperty("cases").EnumerateArray())
        {
            var a = c.GetProperty("args").EnumerateArray().Select(x => x.GetUInt64()).ToArray();
            int I(int i) => (int)a[i];
            var got = OrErr(() => S(c, "fn") switch
            {
                "software_oid" => Ids.SoftwareOid(I(0)),
                "release_oid" => Ids.ReleaseOid(I(0), I(1), I(2), I(3)),
                "channel_oid" => Ids.ChannelOid(I(0), I(1)),
                "build_oid" => Ids.BuildOid(I(0), a[1]),
                "format_oid" => Ids.FormatOid(I(0), I(1), I(2)),
                _ => "unknown fn",
            });
            Check($"{S(c, "fn")}[{string.Join(",", a)}]", got, Err(c) ? "ERR" : S(c, "want"));
        }
        var h = Load(dir, "hlc.json");
        foreach (var c in h.GetProperty("encode").EnumerateArray())
        {
            var what = $"hlc_encode {S(c, "ms")},{S(c, "logical")}";
            if (Err(c))
            {
                try { Hlc.Encode(U(c, "ms"), U(c, "logical")); Check(what, "ok", "ERR"); }
                catch (ArgumentOutOfRangeException) { Check(what, "ERR", "ERR"); }
                continue;
            }
            Check(what, Hlc.Encode(U(c, "ms"), U(c, "logical")), U(c, "hlc"));
            Check($"hlc_decode {S(c, "hlc")}", Hlc.Decode(U(c, "hlc")), (U(c, "ms"), U(c, "logical")));
        }
        foreach (var c in h.GetProperty("send").EnumerateArray()) Check($"hlc_send {S(c, "name")}", Hlc.Send(U(c, "last"), U(c, "now")), U(c, "want"));
        foreach (var c in h.GetProperty("receive").EnumerateArray())
        {
            string got;
            try { got = Hlc.Receive(U(c, "last"), U(c, "remote"), U(c, "now"), U(c, "max_drift_ms")).ToString(); }
            catch (InvalidOperationException) { got = "drift"; }
            Check($"hlc_receive {S(c, "name")}", got, Err(c) ? S(c, "error") : S(c, "want"));
        }
        foreach (var c in h.GetProperty("compare").EnumerateArray()) Check($"hlc_compare {S(c, "a")},{S(c, "b")}", Hlc.Compare(U(c, "a"), U(c, "b")), c.GetProperty("want").GetInt32());
        foreach (var f in Fails) Console.WriteLine("FAIL " + f);
        Console.WriteLine($"dotnet: {n - Fails.Count}/{n} vector checks passed");
        return Fails.Count > 0 ? 1 : 0;
    }

    static int Fuzz(string file)
    {
        var input = JsonDocument.Parse(File.ReadAllText(file)).RootElement;
        var site = Ids.SiteId("example.com");
        var sb = new StringBuilder();
        foreach (var e in input.GetProperty("domains").EnumerateArray())
        {
            var d = e.GetString()!;
            try { var s = Ids.SiteId(d); sb.Append($"D\t{Ids.CanonicalDomain(d)}\t{s}\t{Ids.OidFromUuid(s)}\n"); }
            catch (ArgumentException) { sb.Append("D\tERR\t-\t-\n"); }
        }
        foreach (var e in input.GetProperty("paths").EnumerateArray())
        {
            var p = e.GetString()!;
            try { var r = Ids.RouteId(site, p); sb.Append($"P\t{Ids.CanonicalPath(p)}\t{r}\t{Ids.OidFromUuid(r)}\n"); }
            catch (ArgumentException) { sb.Append("P\tERR\t-\t-\n"); }
        }
        Console.Out.Write(sb.ToString());
        return 0;
    }

    static int Main(string[] args)
    {
        Console.OutputEncoding = new UTF8Encoding(false);
        if (args.Length > 1 && args[0] == "fuzz") return Fuzz(args[1]);
        return Vectors(args.Length > 1 ? args[1] : Path.Combine(AppContext.BaseDirectory, "../../../../../vectors"));
    }
}
