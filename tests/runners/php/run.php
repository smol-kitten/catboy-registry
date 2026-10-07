<?php
// Check build/php against tests/vectors (`php run.php vectors [dir]`) or print fuzz output
// (`php run.php fuzz <input.json>`, the format of tools/fuzz.py). Needs ext-intl.
declare(strict_types=1);

use Catboy\Registry\Hlc;
use Catboy\Registry\Ids;
use Catboy\Registry\Oid;

$build = __DIR__ . '/../../../build/php';
foreach (['Oid.php', 'Ids.php', 'Hlc.php'] as $f) {
    require $build . '/' . $f;
}

function orErr(callable $f): mixed
{
    try {
        return $f();
    } catch (\InvalidArgumentException) {
        return 'ERR';
    }
}

function load(string $dir, string $name): array
{
    return json_decode(file_get_contents("$dir/$name"), true, 512, JSON_THROW_ON_ERROR | JSON_BIGINT_AS_STRING);
}

function vectors(string $dir): int
{
    $n = 0;
    $fails = [];
    $check = function (string $what, mixed $got, mixed $want) use (&$n, &$fails): void {
        $n++;
        if ($got !== $want) {
            $fails[] = "$what: got " . var_export($got, true) . ', want ' . var_export($want, true);
        }
    };
    foreach (load($dir, 'domains.json')['cases'] as $c) {
        $in = $c['input'];
        $got = orErr(fn () => Ids::canonicalDomain($in));
        if (!empty($c['error'])) {
            $check("domain '$in'", $got, 'ERR');
            continue;
        }
        $check("domain '$in'", $got, $c['canonical']);
        $check("site_id '$in'", Ids::siteId($in), $c['site_id']);
        $check("site_oid '$in'", Ids::oidFromUuid($c['site_id']), $c['site_oid']);
    }
    $p = load($dir, 'paths.json');
    $check('site_id example.com', Ids::siteId($p['site_domain']), $p['site_id']);
    foreach ($p['cases'] as $c) {
        $in = $c['input'];
        $got = orErr(fn () => Ids::canonicalPath($in));
        if (!empty($c['error'])) {
            $check("path '$in'", $got, 'ERR');
            continue;
        }
        $check("path '$in'", $got, $c['canonical']);
        $check("route_id '$in'", Ids::routeId($p['site_id'], $in), $c['route_id']);
        $check("route_oid '$in'", Ids::oidFromUuid($c['route_id']), $c['route_oid']);
    }
    $u = load($dir, 'uuid.json');
    $check('namespace', Oid::CATBOY_NAMESPACE, $u['namespace']);
    foreach ($u['oid_from_uuid'] as $c) {
        $check("oid_from_uuid {$c['uuid']}", Ids::oidFromUuid($c['uuid']), $c['oid']);
    }
    foreach ($u['entry_id'] as $c) {
        $check("entry_id {$c['kind']}:{$c['key']}", Ids::entryId($c['kind'], $c['key']), $c['want']);
    }
    $s = load($dir, 'software.json');
    $check('channels', Oid::CHANNELS, array_column($s['channels'], 'name', 'number'));
    $ids = ['catboy-agent' => Oid::CATBOY_AGENT_ID, 'catwaf' => Oid::CATWAF_ID, 'pawkit' => Oid::PAWKIT_ID];
    foreach ($s['products'] as $pr) {
        $check("product {$pr['name']}", $ids[$pr['name']], $pr['id']);
        $check("product {$pr['name']} oid", Ids::softwareOid($pr['arc']), $pr['oid']);
    }
    $fns = ['software_oid' => 'softwareOid', 'release_oid' => 'releaseOid', 'channel_oid' => 'channelOid', 'build_oid' => 'buildOid', 'format_oid' => 'formatOid'];
    foreach ($s['cases'] as $c) {
        $got = orErr(fn () => Ids::{$fns[$c['fn']]}(...$c['args']));
        $check($c['fn'] . json_encode($c['args']), $got, !empty($c['error']) ? 'ERR' : $c['want']);
    }
    $h = load($dir, 'hlc.json');
    foreach ($h['encode'] as $c) {
        $what = "hlc_encode {$c['ms']},{$c['logical']}";
        if (!empty($c['error'])) {
            $check($what, orErr(fn () => Hlc::encode((int) $c['ms'], (int) $c['logical'])), 'ERR');
            continue;
        }
        $check($what, (string) Hlc::encode((int) $c['ms'], (int) $c['logical']), $c['hlc']);
        $check("hlc_decode {$c['hlc']}", Hlc::decode((int) $c['hlc']), [(int) $c['ms'], (int) $c['logical']]);
    }
    foreach ($h['send'] as $c) {
        $check("hlc_send {$c['name']}", (string) Hlc::send((int) $c['last'], (int) $c['now']), $c['want']);
    }
    foreach ($h['receive'] as $c) {
        try {
            $got = (string) Hlc::receive((int) $c['last'], (int) $c['remote'], (int) $c['now'], (int) $c['max_drift_ms']);
        } catch (\RangeException) {
            $got = 'drift';
        }
        $check("hlc_receive {$c['name']}", $got, $c['error'] ?? $c['want']);
    }
    foreach ($h['compare'] as $c) {
        $check("hlc_compare {$c['a']},{$c['b']}", Hlc::compare((int) $c['a'], (int) $c['b']), $c['want']);
    }
    foreach ($h['change_compare'] as $c) {
        [$a, $b] = [$c['a'], $c['b']];
        try {
            $got = Hlc::compareChange((int) $a['hlc'], $a['instance'], $a['change_id'], (int) $b['hlc'], $b['instance'], $b['change_id']);
        } catch (\InvalidArgumentException) {
            $got = 'ERR';
        }
        $check("change_compare {$c['name']}", $got, !empty($c['error']) ? 'ERR' : $c['want']);
    }
    foreach ($fails as $f) {
        echo "FAIL $f\n";
    }
    printf("php: %d/%d vector checks passed\n", $n - count($fails), $n);
    return $fails ? 1 : 0;
}

function fuzz(string $file): int
{
    $in = json_decode(file_get_contents($file), true, 512, JSON_THROW_ON_ERROR);
    $site = Ids::siteId('example.com');
    $out = '';
    foreach ($in['domains'] as $d) {
        try {
            $s = Ids::siteId($d);
            $out .= "D\t" . Ids::canonicalDomain($d) . "\t$s\t" . Ids::oidFromUuid($s) . "\n";
        } catch (\InvalidArgumentException) {
            $out .= "D\tERR\t-\t-\n";
        }
    }
    foreach ($in['paths'] as $p) {
        try {
            $r = Ids::routeId($site, $p);
            $out .= "P\t" . Ids::canonicalPath($p) . "\t$r\t" . Ids::oidFromUuid($r) . "\n";
        } catch (\InvalidArgumentException) {
            $out .= "P\tERR\t-\t-\n";
        }
    }
    echo $out;
    return 0;
}

if (($argv[1] ?? '') === 'fuzz') {
    exit(fuzz($argv[2]));
}
exit(vectors($argv[2] ?? __DIR__ . '/../../vectors'));
