#!/usr/bin/env python3
"""Wire 29, the block-walk overshoot wrap (p_maputl.c:846-876; ruling N9 (a)): certificate audit 1's item WRAP run by
the genuine linuxdoom-1.10 M6b runner and projected by the independent DSIM45 encoder level_snapshot_wire29.py; never
from Rust output.

The item is audit 1's (tools/reference/overshoot_wad.py, read-only: tests/reference/overshoot_wads/overshoot.wad and
overshoot_scripts/WRAP.lmp, skill 2): at session tic 52 an overshooting slide trace meets a notch's long edges and a
FixedMul product of P_InterceptVector leaves int (m_fixed.c:48, narrowed modulo 2^32: implementation-defined, not
undefined); the fractions come out negative and are dropped (p_maputl.c:591-592). A later walk adds a saturated step
to an intercept in int at p_maputl.c:868 or 873, which is undefined in C: the strict build (-fwrapv) wraps, the
overflow and address builds stop there.

The item STEPREAD (our own map and demo, skill 2; module comment at READER) has such a sum read again: at session tic 7
a slide walk adds the saturated ystep at p_maputl.c:868 at its first step and is not at its end cell, so its next
test (866) compares the wrapped sum with mapy. No walk can tell a wrapped sum from a saturated one: a step is taken
only when the sum's cell equals the current one (866, 871), so |sum| < 320 * 2^16 before it (|mapx|, |mapy| <= 256
+ 63: an int >> 23, then at most 63 steps); only FixedDiv's MAXINT or MININT can then overflow it (otherwise
|step| < 2^30, m_fixed.c:62-63 and 69-87), and the wrapped sum >> FRACBITS lies in -32768..-32450 or 32449..32767, as do
the saturated 32767 and -32768, never in the cells' range; every later test is false either way and the sum is never
stepped again.

Runs (the M6b runner of tools/reference/m6b_build.py and wire29_stale.run, read-only; ASAN_OPTIONS=detect_leaks=0:
leak detection disabled, not LeakSanitizer coverage):
  strict                the claim; its DSIM43 projection (wire27_goldens.project) must equal every C row of WRAP in
                        the frozen tests/reference/overshoot_state.txt, which pins this run to audit 1's
  overflow, address     must stop with a UBSan report at p_maputl.c:868 or 873, their dumps a prefix of the strict
                        ones: the captures before the stop are the defined part (`defined_captures`)
  observer              the strict build with OBSERVER (evidence only; dumps equal to strict): every int overflow of
                        the two step sums, with gametic, the walk's flags (1 lines, 2 things), the iteration and
                        whether the sum is read again (the walk ends at the end cell or the count first), and
                        every later test of an overflowed sum (WRAP must have none)
  wrapzero              a planted fault: P_InterceptVector returns 0 where its num leaves int, as for a parallel
                        line (p_maputl.c:242-243); its first differing DSIM45 capture is the V row
  saturate              a planted fault: the two step sums saturate at the int limits instead of wrapping; it must
                        equal strict at every capture of both items (STEPREAD's V row: none)
STEPREAD runs the same builds but wrapzero; its strict build is the claim with no pin.

Output (written without --check; --check regenerates and compares, writing nothing):
  tests/reference/wire29_stale/wrap_state.txt   DOOM-WIRE29-STALE-v1 as wire29_stale.py's: the I row, a C row per
                                                strict capture, the V row (variant, first differing capture, its
                                                digest) and O rows (observed facts)
  tests/reference/wire29_stale/stepread_state.txt, stepread.wad, STEPREAD.txt, STEPREAD.lmp   STEPREAD's, the same

    wire29_wrap.py [--check] [--work DIR] [--cc CC]
"""
import argparse, hashlib, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/reference'))
sys.dont_write_bytecode = True
import level_snapshot as L           # noqa: E402
import level_snapshot_m5c as M5S     # noqa: E402
import level_snapshot_m6a as S6      # noqa: E402
import level_snapshot_wire29 as E    # noqa: E402
import m6a_state as ST               # noqa: E402  (read-only: Shifted, extra_lumps)
import m6a_wad as W                  # noqa: E402  (read-only: the room builder)
import m6b_build as B                # noqa: E402  (read-only)
import m6b_goldens as G              # noqa: E402  (read-only: clean)
import m6b_wad as WAD                # noqa: E402  (read-only: SHARED)
import overshoot_wad as OW           # noqa: E402  (read-only: the item)
import wire27_goldens as W27         # noqa: E402  (read-only: project, UB, ASAN_NOTE)
import wire29_goldens as WG          # noqa: E402  (read-only: digest)
import wire29_stale as WS            # noqa: E402  (read-only: run, SCHEMA)

NAME, MAP, SKILL = 'WRAP', OW.ITEMS['WRAP'][0], 2
STATE = ROOT / 'tests/reference/wire29_stale/wrap_state.txt'
PINNED = ROOT / 'tests/reference/overshoot_state.txt'
SITES = ('p_maputl.c:868', 'p_maputl.c:873')
STEP = ('{{ int w29; if (__builtin_add_overflow ({v}, {s}, &w29)) {{ w29{a} = 1; fprintf (stderr, "W29,step,{line},%d,%d,%d,%d\\n", '
        'gametic, flags, count, (mapx + {dx} == xt2 && mapy + {dy} == yt2) || count == 63); }} }}\n')
READ = 'fprintf (stderr, "W29,read,{line},%d,%d,%d,%d,%d\\n", gametic, flags, count, {a}intercept >> FRACBITS, map{a})'
OBSERVER = {'p_maputl.c': [
    ('#include "p_local.h"\n', '#include "p_local.h"\n#include <stdio.h>\nextern int gametic;\n'),
    ('    earlyout = flags & PT_EARLYOUT;\n', '    int w29x = 0, w29y = 0;\t// a step sum overflowed (it is never added to again)\n'
     '    earlyout = flags & PT_EARLYOUT;\n'),
    ('\t    yintercept += ystep;\n',
     '\t    ' + STEP.format(v='yintercept', s='ystep', a='y', line=868, dx='mapxstep', dy='0') + '\t    yintercept += ystep;\n'),
    ('\t    xintercept += xstep;\n',
     '\t    ' + STEP.format(v='xintercept', s='xstep', a='x', line=873, dx='0', dy='mapystep') + '\t    xintercept += xstep;\n'),
    # every later read of an overflowed sum: the walk's two tests (866, 871), with the value compared and the cell
    ('\tif ( (yintercept >> FRACBITS) == mapy)\n',
     '\tif (w29y) ' + READ.format(line=868, a='y') + ';\n\tif ( (yintercept >> FRACBITS) == mapy)\n'),
    ('\telse if ( (xintercept >> FRACBITS) == mapx)\n',
     '\telse if ((w29x && ' + READ.format(line=873, a='x') + '), (xintercept >> FRACBITS) == mapx)\n')]}
# A planted fault: the two step sums saturate at the int limits instead of wrapping (FixedDiv's MAXINT and MININT)
SAT = '\t    {{ long long w29 = (long long){v} + {s}; {v} = w29 > 0x7fffffff ? 0x7fffffff : w29 < -0x7fffffff - 1 ? -0x7fffffff - 1 : w29; }}\n'
SATURATE = {'p_maputl.c': [('\t    yintercept += ystep;\n', SAT.format(v='yintercept', s='ystep')),
                           ('\t    xintercept += xstep;\n', SAT.format(v='xintercept', s='xstep'))]}
WRAPZERO = {'p_maputl.c': [('    frac = FixedDiv (num , den);\n',
                            '    if ((long long)num != ((long long)((v1->x - v2->x)>>8) * v1->dy >> 16)\n'
                            '\t+ ((long long)((v2->y - v1->y)>>8) * v1->dx >> 16))\n'
                            '\treturn 0;\t// planted fault: an overflowing num as a parallel line\n'
                            '    frac = FixedDiv (num , den);\n')]}
sha = lambda b: hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()
READER = 'STEPREAD'


def room():
    """STEPREAD: one room whose north wall (y 256) is a BLOCKMAP row line and x 256 a column line (the origin is the
    vertex minimum); the player starts facing north with his west side on that column line."""
    p = W.Room('stepread', wall='M5WALLA')
    p.sector('ROOM', [(0, 0, 512, 256)], light=192, fpic='M5FLAT1', cpic='M5FLAT2')
    p.thing(272, 212, 90, WS.PLAYER)
    return p


# Tics of forward 1 turned 32 fine angles east of north (finecosine +1,583) alternate with tics of forward 77 due north
# (finecosine -25), so momx stays within a few raw units while momy grows (P_Thrust, p_user.c:54-62). At session tic 7
# (forward 40) momx is -23 and momy 410,808: (abs(momy)>>14) >= abs(momx), so ystep saturates (m_fixed.c:62-63); the
# west side is 20 raw units east of the column line and the north wall blocks the move, so P_SlideMove's first trace
# (p_map.c:738) crosses the column and the row line. Added to wire29_stale's table in this process only, for its
# script, lump, files, run and project.
WS.ITEMS[READER] = dict(wad='stepread.wad', state='stepread_state.txt', room=room, header=(2, 0, 0),
                        lines=['cmd 1 1 0 -1 0', 'cmd 1 77 0 1 0'] * 3 + ['cmd 1 1 0 -1 0', 'cmd 1 40 0 1 0', 'idle 8'],
                        what='an overflowed step sum at p_maputl.c:868 read again by the block walk')


def wads():
    return [ROOT / w for w in OW.WADSET] + [ROOT / OW.SCRIPT_DIR / f'{NAME}.lmp']


def project(r):
    """[the DSIM45 state digest of every capture], as wire29_stale.project for this item's paths."""
    w = wads()
    it = dict(name=NAME, wads=w[:-1], lmp_path=w[-1])
    loads = S6.rows(r['session'], 'L')
    kind, p, _h, _s = S6.start_from_rows(r['session'], r['sound'], 0, str(w[0]))
    proj = E.Projector(L.MapData(str(w[0]), f'E1M{MAP}', ST.extra_lumps(it)), SKILL, MAP,
                       ST.Shifted(M5S.SoundStream(text=r['sound']), max(loads[0]['tic'], 0)), (kind, dict(p)), 0, 0)
    caps, following = [], L.Dump(str(r['dumps'] / r['names'][0]))
    for j in range(len(r['names'])):
        d, following = following, (L.Dump(str(r['dumps'] / r['names'][j + 1])) if j + 1 < len(r['names']) else None)
        caps.append(WG.digest(proj.step(d, following)[0]))
    return caps


def pinned():
    return [l.split(',')[3] for l in PINNED.read_text().splitlines() if l.startswith(f'C,{NAME},')]


def first_difference(caps, v):
    return next((j for j, (a, c) in enumerate(zip(caps, v)) if a != c), None)


def undefined(runs, fails, facts):
    """The checks and facts of the sanitizer stops and the observer, shared by both items."""
    s = runs['strict']
    if not G.clean(s): fails.append(f'strict: exit {s["code"]}: {s["stderr"][-400:]}')
    for b in ('overflow', 'address'):
        r, m = runs[b], W27.UB.search(runs[b]['stderr'])
        site = f"{m['file']}:{m['line']}" if m else None
        n = len(r['digests'])
        if site not in SITES or r['digests'] != s['digests'][:n]:
            fails.append(f'{b}: stop {site}, or its {n} dumps are not a strict prefix')
        facts[f'{b}_stop'] = f'{site} {n}'
    o = runs['observer']
    if o['code'] or o['digests'] != s['digests']: fails.append('observer: exit or dumps differ from strict')
    facts['step_overflows'] = [x for x in (l.split(',')[2:] for l in o['stderr'].splitlines() if l.startswith('W29,step,'))]
    if len({facts['overflow_stop'], facts['address_stop']}) != 1: fails.append('the two stops differ')
    facts['defined_captures'] = int(facts['overflow_stop'].split()[1])
    return [l.split(',')[2:] for l in o['stderr'].splitlines() if l.startswith('W29,read,')]


def evidence(work, cc):
    bins = {b: B.build(b, work / 'build', cc) for b in B.BUILDS}
    for b, reps in (('observer', OBSERVER), ('wrapzero', WRAPZERO), ('saturate', SATURATE)):
        bins[b] = B.variant(b, reps, work / 'build', cc)
    runs = {b: WS.run(NAME, x, work / 'runs' / b, wads()) for b, x in bins.items()}
    s, fails, facts = runs['strict'], [], {}
    w27 = [c[2] for c in W27.project(s, dict(name=NAME, map=MAP, wads=wads()[:-1], lmp_path=wads()[-1]))[0]]
    if w27 != pinned(): fails.append('strict: its DSIM43 projection is not overshoot_state.txt\'s')
    facts['pinned_dsim43_captures'] = len(w27)
    reads = undefined(runs, fails, facts)
    caps = project(s)
    v = project(runs['wrapzero'])
    k = first_difference(caps, v)
    if k is None or k >= facts['defined_captures']: fails.append(f'wrapzero: first differs at {k}')
    # Not in the golden: every overflowed sum is dead (no later read) and saturating them changes nothing
    sat = first_difference(caps, project(runs['saturate']))
    print(f'{NAME}: observer reads of an overflowed sum {len(reads)}; saturate first differs at {sat}')
    if reads or sat is not None: fails.append(f'{NAME}: {len(reads)} reads, saturate first differs at {sat}')
    return s, caps, ('wrapzero', k, v[k] if k is not None else '-'), facts, fails, bins


def stepread(work, bins):
    """STEPREAD in the strict, overflow, address, observer and saturate builds: the overflow at p_maputl.c:868 must
    be read again (`step_reads`), and the saturating variant must equal the strict build at every capture."""
    for path, data in WS.files(READER).items():
        (work / 'item' / path).parent.mkdir(parents=True, exist_ok=True)
        (work / 'item' / path).write_bytes(data)
    w = [work / 'item' / WS.DIR / 'stepread.wad'] + [ROOT / x for x in WAD.SHARED] + [work / 'item' / WS.DIR / f'{READER}.lmp']
    runs = {b: WS.run(READER, bins[b], work / 'runs' / f'{READER}_{b}', w) for b in (*B.BUILDS, 'observer', 'saturate')}
    fails, facts = [], {}
    facts['step_reads'] = undefined(runs, fails, facts)
    if not any(r[0] == '868' for r in facts['step_reads']): fails.append(f'{READER}: no read of an overflowed sum at 868')
    caps = WS.project(READER, runs['strict'], w)
    k = first_difference(caps, WS.project(READER, runs['saturate'], w))
    if k is not None: fails.append(f'{READER}: saturate first differs at {k}')
    return runs['strict'], caps, ('saturate', 'none', '-'), facts, fails


PIN = ', pinned to overshoot_state.txt'
READS = ('; step_reads: site gametic flags iteration, the sum >> FRACBITS and the cell coordinate it is compared with; '
         'V first_differing_capture none: equal at every capture')


def state_text(name, s, caps, variant, facts, pin=PIN, reads=''):
    tics = len(s['names']) - 1
    head = [f'#schema,{WS.SCHEMA}',
            f'#generator,tools/reference/wire29_wrap.py: the genuine M6b runner (strict build{pin}; '
            'overflow, address, observer, a planted-fault variant) and the independent DSIM45 encoder; never from Rust output',
            '#tics,capture j is the state after j session tics; a refusal at session tic N keeps capture N',
            '#state,as tests/reference/wire29_state.txt',
            '#columns,I,item,skill,respawnparm,fastparm,tics,captures,dumps_sha256,sequence_sha256',
            '#columns,C,item,capture,state_sha256 (strict)', '#columns,V,variant,first_differing_capture,variant_state_sha256',
            '#columns,O,fact,value (*_stop: the UBSan site and the dumps before it; step_overflows: site gametic flags '
            f'iteration dead; defined_captures: the captures before the stop{reads})']
    rows = [f"I,{name},{SKILL},0,0,{tics},{len(caps)},{sha(''.join(s['digests']))},"
            f"{sha(b''.join(bytes.fromhex(c) for c in caps))}"]
    rows += [f'C,{name},{j},{d}' for j, d in enumerate(caps)]
    rows += ['V,{},{},{}'.format(*variant)]
    rows += [f'O,{k},{";".join(" ".join(x) for x in v) if isinstance(v, list) else v}' for k, v in facts.items()]
    return '\n'.join(head + rows) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--work', type=Path, default=Path.home() / 'scratch' / 'wire29' / 'wrap')
    ap.add_argument('--cc', default='cc')
    a = ap.parse_args()
    work = a.work.resolve()
    if work == ROOT or ROOT in work.parents: sys.exit('--work must lie outside the repository')
    s, caps, variant, facts, fails, bins = evidence(work, a.cc)
    rs, rcaps, rvariant, rfacts, rfails = stepread(work, bins)
    for n, c, v, f in ((NAME, caps, variant, facts), (READER, rcaps, rvariant, rfacts)):
        print(f'{n}: {len(c)} captures (DSIM45); variant {v[0]} first differs at {v[1]}; '
              + ', '.join(f'{k} {x}' for k, x in f.items()))
    if fails + rfails: print('\n'.join(['FAILURES:'] + fails + rfails)); return 1
    out = {STATE: state_text(NAME, s, caps, variant, facts),
           ROOT / WS.DIR / 'stepread_state.txt': state_text(READER, rs, rcaps, rvariant, rfacts, '', READS)}
    out = {p: t.encode() for p, t in out.items()} | {ROOT / p: d for p, d in WS.files(READER).items()}
    shutil.rmtree(work / 'runs', ignore_errors=True)
    if a.check:
        bad = [str(p.relative_to(ROOT)) for p, d in out.items() if not p.exists() or p.read_bytes() != d]
        print((f'differs: {", ".join(bad)}' if bad else f'{len(out)} files match') + f'; {W27.ASAN_NOTE}')
        return 1 if bad else 0
    for p, d in out.items(): p.write_bytes(d)
    print(f'wrote {len(out)} files; {W27.ASAN_NOTE}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
