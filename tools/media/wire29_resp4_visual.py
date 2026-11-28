#!/usr/bin/env python3
"""Writes docs/media/wire29-resp4-intermission.gif (wire 29): the genuine engine and Rust on RESP4's intermission.

    wire29_resp4_visual.py [--work DIR] [--cargo-target DIR] [--check]

Item RESP4 (Nightmare, tests/reference/m6b_scripts/RESP4.lmp on our synthetic WADs and generated art; no IWAD): the player
kills two respawning demons, one of them twice, so the kills exceed the level's total of 5 and the intermission counts the
kill percentage past 100 (ruling N10). Panels as m6a2_readme_visual.py draws them: the genuine linuxdoom-1.10 frame, the
Rust wire 29 session frame and their difference (red where pixels differ, so black is identical), every 4th tic of the
intermission (tics 1316 to 1515) at half speed, each caption with the genuine kill counter of that tic.

Needs a C compiler and cargo (a local check, not in CI): the strict M6b runner of tools/reference/m6b_build.py is built under
--work (sources untouched) and relinked with tools/media/m6a2_pixel_tap.c, an observer that writes screens[0] after each
genuine WI_Drawer; the Rust frames come from crates/doom-game/examples/wire29_pause_frames.rs. Checked before drawing, and
nothing is written on a failure: every one of the 200 intermission pictures, genuine and Rust, equals the G row digest of
tests/reference/m6b_frames/RESP4.sb10.frames; genuine equals Rust byte for byte; the genuine kill counter (the J rows of the
runner's session stream) equals the committed tests/reference/m6b_session/RESP4.session and reaches 200. --selftest flips
one pixel of the genuine picture of tic 1400 before those checks; the script must then exit with the digest message. The file has no timestamp or path, so a rerun
writes the same bytes. --work must lie outside the repository.
"""
import argparse, hashlib, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
for d in ('tools/reference', 'tools/media'):
    sys.path.insert(0, str(ROOT / d))
import m3h9c_build as base, m5c_build as C, m5c_reference as M5C, m6a_build, m6b_build, m6b_goldens as G6B, m6b_wad as WAD   # noqa: E402
import m5b_readme_visual as B, m6a2_readme_visual as V                                                                    # noqa: E402

REF, OUT = ROOT / 'tests/reference', ROOT / 'docs/media/wire29-resp4-intermission.gif'
NAME, SB, EVERY, SLOW, HOLD_CS, PIXELS = 'RESP4', 10, 4, 2, 150, 64000
sha = lambda b: hashlib.sha256(b).hexdigest()


def build(work, cargo_target):
    p = subprocess.run(['cargo', 'build', '-p', 'doom-game', '--release', '--locked', '--example', 'wire29_pause_frames'],
                       cwd=ROOT, env=dict(os.environ, CARGO_TARGET_DIR=str(cargo_target)), capture_output=True, text=True)
    if p.returncode:
        sys.exit(f'cargo build failed:\n{p.stderr[-2000:]}')
    so, sys.stdout = sys.stdout, open(os.devnull, 'w')
    try:
        m6b_build.build('strict', work / 'build')
    finally:
        sys.stdout = so
    b = work / 'build/strict'
    flags, tap = base.VARIANTS['strict'], b / 'obj/m6a2_pixel_tap.o'
    units = [*m6a_build.UNITS, 'layout_probe.c', m6a_build.STUBS_NAME, m6b_build.DRIVER_NAME]
    for cmd in ([*flags, '-I', str(b / 'src'), '-c', str(ROOT / 'tools/media/m6a2_pixel_tap.c'), '-o', str(tap)],
                [*flags, *m6a_build.LINK_FLAGS, *m6b_build.LINK_FLAGS, '-Wl,--wrap=F_Drawer,--wrap=WI_Drawer,--wrap=wipe_ScreenWipe',
                 *[str(b / 'obj' / (f[:-2] + '.o')) for f in units], str(tap), *C.LIBS, '-o', str(b / 'tapped')]):
        p = subprocess.run(['cc', *cmd], capture_output=True, text=True)
        if p.returncode:
            sys.exit(f'tap build failed:\n{p.stderr[-2000:]}')
    return b / 'tapped', cargo_target / 'release/examples/wire29_pause_frames'


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--work', type=Path, default=Path.home() / 'scratch/wire29-resp4-visual')
    ap.add_argument('--cargo-target', type=Path, default=None)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--selftest', action='store_true', help='plant a flipped pixel in the genuine picture of tic 1400: must fail')
    a = ap.parse_args()
    work = a.work.resolve()
    if work == ROOT or ROOT in work.parents:
        sys.exit('--work must lie outside the repository')
    work.mkdir(parents=True, exist_ok=True)
    tapped, rust = build(work, (a.cargo_target or work / 'target').resolve())
    out = work / NAME
    shutil.rmtree(out, ignore_errors=True)
    (out / 'g').mkdir(parents=True), (out / 'r').mkdir()
    wads = [ROOT / w for w in WAD.wads(NAME)]
    lmp = ROOT / f'{WAD.SCRIPT_DIR}/{NAME}.lmp'
    p = subprocess.run([str(tapped), *[x for w in [*wads, lmp] for x in ('--wad', str(w))], '--demo', NAME, '--game-mode', 'registered',
                        '--no-dump', *[x for k, v in M5C.RECOMMENDED.items() for x in (k, v)], '--render', 'every', '--screenblocks', str(SB),
                        '--frames', str(out / 'frames.txt'), '--sound-out', str(out / 'sound.txt'), '--session-out', str(out / 'session.txt'),
                        '--m6b-out', str(out / 'm6b.txt')], capture_output=True, text=True,
                       env=dict(G6B.ENV, M6A_TAP=str(out / 'g')))
    if p.returncode:
        sys.exit(f'the genuine runner failed: {p.stderr[-500:]}')
    p = subprocess.run([str(rust), *[x for w in wads for x in ('--wad', str(w))], '--demo', str(lmp), '--mode', 'registered',
                        '--screenblocks', str(SB), '--out', str(out / 'r')], capture_output=True, text=True)
    if p.returncode:
        sys.exit(f'the Rust frame dump failed: {p.stderr[-500:]}')
    gold = {int(f[1]): (f[3], int(f[4])) for f in (l.split(',') for l in (REF / f'm6b_frames/{NAME}.sb{SB}.frames').read_text().splitlines())
            if f[0] == 'G'}
    tics = sorted(gold)
    gen = {int(f.stem[2:]): f.read_bytes() for f in (out / 'g').glob('d_*.raw')}
    rus = {t: (out / 'r' / f't_{t}.raw').read_bytes() for t in tics}
    n_eq = n_diff = 0
    for t in tics:
        g, r = gen.get(t), rus[t]
        if a.selftest and t == 1400:
            g = bytes([g[0] ^ 1]) + g[1:]
        if g is None or len(g) != PIXELS or len(r) != PIXELS:
            sys.exit(f'tic {t}: no genuine or Rust picture of {PIXELS} bytes')
        if sha(g) != gold[t][0] or sha(r) != gold[t][0]:
            sys.exit(f'tic {t}: a picture does not match the committed genuine digest')
        n_diff += sum(x != y for x, y in zip(g, r))
        n_eq += g == r
    if n_diff:
        sys.exit(f'{len(tics) - n_eq} of {len(tics)} intermission pictures differ from Rust ({n_diff} pixels)')
    sess = lambda path: {int(f[1]): int(f[9]) for f in (l.split(',') for l in path.read_text().splitlines()) if f[0] == 'J'}
    kills = sess(out / 'session.txt')
    if kills != sess(REF / f'm6b_session/{NAME}.session') or sorted(kills) != tics:
        sys.exit('the genuine kill counter differs from the committed session stream')
    top = max(kills.values())
    pal = V.playpal({'wads': wads})
    shown = tics[::EVERY] + ([tics[-1]] if (len(tics) - 1) % EVERY else [])
    job = dict(what='RESP4: NIGHTMARE INTERMISSION, KILLS PAST 100 PERCENT, HALF SPEED',
               note=f'{len(tics)} INTERMISSION TICS, EVERY {EVERY}TH SHOWN, COMPARED ON PALETTE INDICES. SYNTHETIC TEST MAP AND ART, NOT THE GAMES')
    frames = V.compose(job, pal, [(gen[t], rus[t], gold[t][1], f'TIC {t}, KILLS {max(kills[t], 0)} PERCENT') for t in shown])
    ends = [round((k + 1) * EVERY * 100 * SLOW / 35) for k in range(len(frames))]
    ds = [ends[0]] + [b - x for x, b in zip(ends, ends[1:])]
    ds[-1] += HOLD_CS
    gif, shown_rgb = B.write_gif(frames, ds)
    B.self_check(gif, shown_rgb, ds)
    secs = sum(ds) / 100
    if len(gif) >= 2_000_000 or secs >= 15:
        sys.exit(f'exceeds 2 MB or 15 s ({len(gif)} bytes, {secs} s)')
    print(f'{OUT.name}: {len(frames)} frames, {secs:.2f} s, {len(gif)} bytes, sha256 {sha(gif)}; {n_eq} of {len(tics)} intermission '
          f'pictures equal (genuine and Rust), {n_diff} differing pixels; kill counter peaks at {top} percent')
    if a.check:
        if not OUT.exists() or OUT.read_bytes() != gif:
            sys.exit(f'{OUT.relative_to(ROOT)} differs from the regenerated animation')
        print(f'{OUT.relative_to(ROOT)}: identical to the regenerated animation')
    else:
        OUT.write_bytes(gif)
        print(f'wrote {OUT}')


if __name__ == '__main__':
    main()
