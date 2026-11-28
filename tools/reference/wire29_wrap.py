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

Runs (the M6b runner of tools/reference/m6b_build.py and wire29_stale.run, read-only; ASAN_OPTIONS=detect_leaks=0:
leak detection disabled, not LeakSanitizer coverage):
  strict                the claim; its DSIM43 projection (wire27_goldens.project) must equal every C row of WRAP in
                        the frozen tests/reference/overshoot_state.txt, which pins this run to audit 1's
  overflow, address     must stop with a UBSan report at p_maputl.c:868 or 873, their dumps a prefix of the strict
                        ones: the captures before the stop are the defined part (`defined_captures`)
  observer              the strict build with OBSERVER (evidence only; dumps equal to strict): every int overflow of
                        the two step sums, with gametic, the walk's flags (1 lines, 2 things), the iteration and
                        whether the sum is read again (the walk ends at the end cell or the count first)
  wrapzero              a planted fault: P_InterceptVector returns 0 where its num leaves int, as for a parallel
                        line (p_maputl.c:242-243); its first differing DSIM45 capture is the V row

Output (written without --check; --check regenerates and compares, writing nothing):
  tests/reference/wire29_stale/wrap_state.txt   DOOM-WIRE29-STALE-v1 as wire29_stale.py's: the I row, a C row per
                                                strict capture, the V row (variant, first differing capture, its
                                                digest) and O rows (observed facts)

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
import m6b_build as B                # noqa: E402  (read-only)
import m6b_goldens as G              # noqa: E402  (read-only: clean)
import overshoot_wad as OW           # noqa: E402  (read-only: the item)
import wire27_goldens as W27         # noqa: E402  (read-only: project, UB, ASAN_NOTE)
import wire29_goldens as WG          # noqa: E402  (read-only: digest)
import wire29_stale as WS            # noqa: E402  (read-only: run, SCHEMA)

NAME, MAP, SKILL = 'WRAP', OW.ITEMS['WRAP'][0], 2
STATE = ROOT / 'tests/reference/wire29_stale/wrap_state.txt'
PINNED = ROOT / 'tests/reference/overshoot_state.txt'
SITES = ('p_maputl.c:868', 'p_maputl.c:873')
STEP = ('{{ int w29; if (__builtin_add_overflow ({v}, {s}, &w29)) fprintf (stderr, "W29,step,{line},%d,%d,%d,%d\\n", '
        'gametic, flags, count, (mapx + {dx} == xt2 && mapy + {dy} == yt2) || count == 63); }}\n')
OBSERVER = {'p_maputl.c': [
    ('#include "p_local.h"\n', '#include "p_local.h"\n#include <stdio.h>\nextern int gametic;\n'),
    ('\t    yintercept += ystep;\n',
     '\t    ' + STEP.format(v='yintercept', s='ystep', line=868, dx='mapxstep', dy='0') + '\t    yintercept += ystep;\n'),
    ('\t    xintercept += xstep;\n',
     '\t    ' + STEP.format(v='xintercept', s='xstep', line=873, dx='0', dy='mapystep') + '\t    xintercept += xstep;\n')]}
WRAPZERO = {'p_maputl.c': [('    frac = FixedDiv (num , den);\n',
                            '    if ((long long)num != ((long long)((v1->x - v2->x)>>8) * v1->dy >> 16)\n'
                            '\t+ ((long long)((v2->y - v1->y)>>8) * v1->dx >> 16))\n'
                            '\treturn 0;\t// planted fault: an overflowing num as a parallel line\n'
                            '    frac = FixedDiv (num , den);\n')]}
sha = lambda b: hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()


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


def evidence(work, cc):
    bins = {b: B.build(b, work / 'build', cc) for b in B.BUILDS}
    bins['observer'] = B.variant('observer', OBSERVER, work / 'build', cc)
    bins['wrapzero'] = B.variant('wrapzero', WRAPZERO, work / 'build', cc)
    runs = {b: WS.run(NAME, x, work / 'runs' / b, wads()) for b, x in bins.items()}
    s, fails, facts = runs['strict'], [], {}
    if not G.clean(s): fails.append(f'strict: exit {s["code"]}: {s["stderr"][-400:]}')
    w27 = [c[2] for c in W27.project(s, dict(name=NAME, map=MAP, wads=wads()[:-1], lmp_path=wads()[-1]))[0]]
    if w27 != pinned(): fails.append('strict: its DSIM43 projection is not overshoot_state.txt\'s')
    facts['pinned_dsim43_captures'] = len(w27)
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
    caps = project(s)
    v = project(runs['wrapzero'])
    k = next((j for j, (a, c) in enumerate(zip(caps, v)) if a != c), None)
    if k is None or k >= facts['defined_captures']: fails.append(f'wrapzero: first differs at {k}')
    return s, caps, ('wrapzero', k, v[k] if k is not None else '-'), facts, fails


def state_text(s, caps, variant, facts):
    tics = len(s['names']) - 1
    head = [f'#schema,{WS.SCHEMA}',
            '#generator,tools/reference/wire29_wrap.py: the genuine M6b runner (strict build, pinned to overshoot_state.txt; '
            'overflow, address, observer, a planted-fault variant) and the independent DSIM45 encoder; never from Rust output',
            '#tics,capture j is the state after j session tics; a refusal at session tic N keeps capture N',
            '#state,as tests/reference/wire29_state.txt',
            '#columns,I,item,skill,respawnparm,fastparm,tics,captures,dumps_sha256,sequence_sha256',
            '#columns,C,item,capture,state_sha256 (strict)', '#columns,V,variant,first_differing_capture,variant_state_sha256',
            '#columns,O,fact,value (*_stop: the UBSan site and the dumps before it; step_overflows: site gametic flags '
            'iteration dead; defined_captures: the captures before the stop)']
    rows = [f"I,{NAME},{SKILL},0,0,{tics},{len(caps)},{sha(''.join(s['digests']))},"
            f"{sha(b''.join(bytes.fromhex(c) for c in caps))}"]
    rows += [f'C,{NAME},{j},{d}' for j, d in enumerate(caps)]
    rows += ['V,{},{},{}'.format(*variant)]
    rows += [f'O,{k},{";".join(" ".join(x) for x in v) if k == "step_overflows" else v}' for k, v in facts.items()]
    return '\n'.join(head + rows) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--work', type=Path, default=Path.home() / 'scratch' / 'wire29' / 'wrap')
    ap.add_argument('--cc', default='cc')
    a = ap.parse_args()
    work = a.work.resolve()
    if work == ROOT or ROOT in work.parents: sys.exit('--work must lie outside the repository')
    s, caps, variant, facts, fails = evidence(work, a.cc)
    print(f'{NAME}: {len(caps)} captures (DSIM45); variant {variant[0]} first differs at {variant[1]}; '
          + ', '.join(f'{k} {v}' for k, v in facts.items()))
    if fails: print('\n'.join(['FAILURES:'] + fails)); return 1
    text = state_text(s, caps, variant, facts)
    shutil.rmtree(work / 'runs', ignore_errors=True)
    if a.check:
        ok = STATE.exists() and STATE.read_text() == text
        print(f'{STATE.relative_to(ROOT)} ' + ('matches' if ok else 'differs from the regenerated text') + f'; {W27.ASAN_NOTE}')
        return 0 if ok else 1
    STATE.write_text(text)
    print(f'wrote {STATE.relative_to(ROOT)}; {W27.ASAN_NOTE}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
