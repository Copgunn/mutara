#!/usr/bin/env python3
"""Writes docs/media/wire29-pause.gif (wire 29): the item PAUSE, the original's pause stopping a level.

    wire29_readme_visual.py [--work DIR] [--cargo-target DIR] [--check]

The committed recording tests/reference/m6b_scripts/PAUSE.lmp (a pause command at session tic 72, the original's
byte 0x81) on our synthetic WADs and generated art (tests/reference/m6b_wads/m6b.wad and the shared synthetic
WADs; no IWAD), played by the Rust wire 29 session (crates/doom-game/examples/wire29_pause_frames.rs,
screenblocks 10), every 2nd tic at half speed. Panels: the frame, a readout of the session, and the pixels that
changed since the previous tic (red).

Only the Rust frames are drawn; no genuine-engine run is made here. What backs them: every frame of the run (341)
must hash to the F row of the committed genuine stream tests/reference/m6b_frames/PAUSE.sb10.frames, the digests the
test `wire_29_frames_sound_and_mixer_equal_the_genuine_engine` compares at every tic; every paused tic must be the
genuine B row of tests/reference/m6b_pause/PAUSE.sb10.txt (214 of them) and no other. The palette is the PLAYPAL of the synthetic WADs. The file has no timestamp or
path, so a rerun writes the same bytes. --check compares with the committed file (a local check: it runs cargo).
--work must be outside the repository.
"""
import argparse, hashlib, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
for d in ('tools/reference', 'tools/media'):
    sys.path.insert(0, str(ROOT / d))
import m5b_readme_visual as B, m6a2_readme_visual as V   # noqa: E402

REF, OUT = ROOT / 'tests/reference', ROOT / 'docs/media/wire29-pause.gif'
WADS = ['m6b_wads/m6b.wad', 'm5b_gfx.wad', 'm5c_sfx.wad', 'm6a_wads/m6a_gfx.wad', 'm6a_wads/m6a_music.wad',
        'm6b_wads/m6b_gfx.wad']
LMP = REF / 'm6b_scripts/PAUSE.lmp'
W, H, SB, EVERY, FIRST, LAST, SLOW, HOLD_CS = 320, 200, 10, 2, 56, 136, 2, 100
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--work', type=Path, default=Path.home() / 'scratch/wire29-readme-visual')
    ap.add_argument('--cargo-target', type=Path, default=None)
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    work = a.work.resolve()
    if work == ROOT or ROOT in work.parents:
        sys.exit('--work must lie outside the repository')
    target = (a.cargo_target or work / 'target').resolve()
    p = subprocess.run(['cargo', 'build', '-p', 'doom-game', '--release', '--locked', '--example', 'wire29_pause_frames'],
                       cwd=ROOT, env={**__import__('os').environ, 'CARGO_TARGET_DIR': str(target)}, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f'cargo build failed:\n{p.stderr[-2000:]}')
    wads = [REF / w for w in WADS]
    out = work / 'PAUSE'
    p = subprocess.run([str(target / 'release/examples/wire29_pause_frames'), *[x for w in wads for x in ('--wad', str(w))],
                        '--demo', str(LMP), '--mode', 'registered', '--screenblocks', str(SB), '--out', str(out)],
                       capture_output=True, text=True)
    if p.returncode:
        sys.exit(f'the Rust frame dump failed: {p.stderr[-500:]}')
    idx = {int(r[0]): [int(x) for x in r[1:]] for r in (l.split(',') for l in (out / 'index.txt').read_text().splitlines())}
    gold = {int(f[1]): f[2] for f in (l.split(',') for l in (REF / f'm6b_frames/PAUSE.sb{SB}.frames').read_text().splitlines())
            if f[0] == 'F'}
    bpause = {int(f[1]) for f in (l.split(',') for l in (REF / f'm6b_pause/PAUSE.sb{SB}.txt').read_text().splitlines())
              if f[0] == 'B'}
    pics = {t: (out / f't_{t}.raw').read_bytes() for t in idx}
    if sorted(idx) != sorted(gold):
        sys.exit('the tics are not those of the genuine stream')
    for t, g in gold.items():
        if sha(pics[t]) != g:
            sys.exit(f'tic {t}: the Rust frame differs from the genuine stream digest')
    if {t for t, v in idx.items() if v[1]} != bpause:
        sys.exit('the paused tics are not the genuine B rows')
    pal = V.playpal({'wads': wads})
    out_frames = []
    for t in range(FIRST, LAST + 1, EVERY):
        pal_no, paused, lt, gt = idx[t]
        cur, prev = pics[t], pics[t - 1]
        n = sum(x != y for x, y in zip(cur, prev))
        free = [i for i in range(255, -1, -1) if i not in set(cur) | set(prev)]
        table = bytearray(pal[pal_no * 768:(pal_no + 1) * 768])
        ui = {}
        for name, i in zip(B.UI, free):
            ui[name] = i
            table[3 * i:3 * i + 3] = bytes(B.UI[name])
        cv = bytearray([ui['bg']]) * (B.SCREEN_W * B.SCREEN_H)
        panel2 = bytes([ui['black']]) * (W * H)
        diff = bytes(ui['red'] if x != y else ui['black'] for x, y in zip(cur, prev))
        for k, img in enumerate((cur, panel2, diff)):
            for y in range(H):
                at = (B.LABEL_H + y) * B.SCREEN_W + k * (W + B.GAP)
                cv[at:at + W] = img[y * W:(y + 1) * W]
        for k, s in enumerate(('THE FRAME', 'THE SESSION', 'CHANGED SINCE LAST TIC')):
            B.text(cv, k * (W + B.GAP), 4, s, ui['white'], 1 if k == 2 else 2)
        x2, y2 = W + B.GAP + 12, B.LABEL_H + 24
        B.text(cv, x2, y2, f'SESSION TIC {t}', ui['white'])
        B.text(cv, x2, y2 + 32, f'LEVEL TIC   {lt}', ui['white'])
        B.text(cv, x2, y2 + 64, f'GAMETIC     {gt}', ui['white'])
        B.text(cv, x2, y2 + 110, 'PAUSED: LEVEL STOPPED' if paused else 'LEVEL RUNNING', ui['red'] if paused else ui['green'])
        y = B.LABEL_H + H + 4
        B.text(cv, 0, y, 'THE ORIGINAL PAUSE COMMAND ON A SYNTHETIC MAP: THE LEVEL STOPS AT TIC 72', ui['white'])
        B.text(cv, 0, y + 22, f'TIC {t}: {n} OF {W * H} PIXELS CHANGED SINCE THE PREVIOUS TIC', ui['green'])
        B.text(cv, 0, y + 46, 'RUST FRAMES, EACH EQUAL TO THE GENUINE ENGINE FRAME. EVERY 2ND TIC, HALF SPEED. SYNTHETIC ART. THE PAUSE PICTURE IS THE BLACK BOX',
               ui['grey'], 1)
        out_frames.append((bytes(table), bytes(cv), free[len(B.UI)]))
    ends = [round((k + 1) * EVERY * 100 * SLOW / 35) for k in range(len(out_frames))]
    ds = [ends[0]] + [b - x for x, b in zip(ends, ends[1:])]
    ds[-1] += HOLD_CS
    gif, shown = B.write_gif(out_frames, ds)
    B.self_check(gif, shown, ds)
    secs = sum(ds) / 100
    if len(gif) >= 2_000_000 or secs >= 15:
        sys.exit(f'exceeds 2 MB or 15 s ({len(gif)} bytes, {secs} s)')
    print(f'{OUT.name}: {len(out_frames)} frames, {secs:.2f} s, {len(gif)} bytes, sha256 {sha(gif)}; '
          f'{len(idx)} frames equal to the genuine stream digests, {len(bpause)} paused tics equal to the B rows')
    if a.check:
        if not OUT.exists() or OUT.read_bytes() != gif:
            sys.exit(f'{OUT.relative_to(ROOT)} differs from the regenerated animation')
        print(f'{OUT.relative_to(ROOT)}: identical to the regenerated animation')
    else:
        OUT.write_bytes(gif)
        print(f'wrote {OUT}')


if __name__ == '__main__':
    main()
