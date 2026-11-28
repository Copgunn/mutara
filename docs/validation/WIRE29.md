# Wire 29 evidence record (Nightmare, respawn, fast and the original's pause)

Observed results of wire 29 (`PlayerMonstersEpisode1V7`, captures `DSIM` 45, session state `DSES` 4, display state `DDSP` 5,
sound state `DSND` 4, demo reader and writer version 4), recorded 2026-11-26 and 2026-11-27 (America/Los_Angeles; recording
file-name stamps are UTC) on branch `feat/m6b-wire29`, [draft PR #89](https://github.com/Copgunn/mutara/pull/89). The rule and what is
admitted are in [COMPATIBILITY](../COMPATIBILITY.md#wire-29-nightmare-respawn-fast-and-the-originals-pause), the formats in
[STATE_FORMAT](../STATE_FORMAT.md#dsim-v45--wire-29-nightmare-and-the-originals-pause), the C facts and the owner's rulings N1 to N11 in
the [M6b note](../M6B_REFERENCE_INVESTIGATION.md), the commands in [TESTING](../TESTING.md#m6b-phase-2-wire-29-against-the-genuine-engine)
and the quirk rows in the [register](../QUIRKS.md). Exact review commits and CI belong to GitHub. Only counts, pass/fail facts,
digest prefixes and map names from the commercial IWAD appear here; nothing is said of any map's things or geometry.

**Tic convention (as in [WIRE27](WIRE27.md)).** A session tic is the 0-based index of a tic; a refusal at session tic N keeps the
state after N tics. **Everything labelled Rust-only is Rust-only:** no genuine engine ran it. Figures marked
`REAL-MAP-FIGURES-PENDING` come from the real-map replays, which were being rerun when this record was written; they are filled in
afterwards and nothing here stands in for them.

## 1. What wire 29 is, in one paragraph

Wire 28's simulation plus: skill 4 (Nightmare: double ammunition, spawn bit 4, reaction time 0 at spawn, the fast table and the
two `A_Chase` rules, the corpse respawn); the original's `-respawn` and `-fast` as two options (`GameParameters`) saved in the state;
the pause as a command byte (bit 7, `0x81` from the Pause key; a live player's buttons zeroed, a dead player's read raw), the
paused tic, the turbo message tested against the session's `gametic`, and the session's pause (the stopped level, the status bar
and message timer that go on, the M_PAUSE picture, the sound's pause and resume calls); kills above the level total; the `p_maputl.c`
wrapping step sum. `doom-play` plays it for every skill, with `--respawn`, `--fast` and the Pause key. Wires 1 to 28 keep their
bytes, admission and refusals.

## 2. Decisions

N1 to N11 are the owner's, in the note's [Rulings](../M6B_REFERENCE_INVESTIGATION.md#rulings) table. D1 to D53 below are decisions of
the building steps. **Only the ones marked "owner" were ruled on by the owner; the others were taken by the building agent and are
changeable before merge.** D43 and D45 to D48 are not in the fact sheet the record is written from: nothing is claimed for them.

| D | Chosen | Not taken |
| --- | --- | --- |
| D1 | The two options live in a new pub `GameParameters`, canonical as `actors.parameters` | New fields in `ActorOptions` (an existing test builds it field by field); widening `actors.options`; reusing `MapContextOptions::respawn_monsters` (it names the derived value) |
| D2 | `level.gametic_lead` (gametic minus the level's tic count) after `level.start.gametic`, outside the start group | A paused-tic count; a field in the start group |
| D3 | Temporary refusals as one `Wire29Pending` error, all removed by step 4 | A load refusal of skill 4, fast or respawn (compares nothing) |
| D4 | The DSIM45 reader's fast-table rule also bounds the slow table's thirteen durations | Leaving the slow table unchecked |
| D5 | The golden projects the first level of each run | Projecting `PAUSEWI`'s second level (no load dump in the runner) |
| D6 | Encoder: a respawned monster carries its corpse's spawn point; a `target` or `attacker` naming a freed corpse is its stale handle | Refusing such dumps |
| D7 | Test modules `nightmare_genuine_tests` and `nightmare_tests` | `wire29_*` names (rustfmt would put them last in `lib.rs`) |
| D8 | The fast table is applied at use (state entry, missile launch) | A non-pristine per-simulation registry |
| D9 | Planted faults by a `cfg(test)` thread-local switch with constant-false hooks | Crate-private state mutation only; altered-golden comparison only |
| D10 | Under the `react` fault the spawn witnesses expect the type's reaction time | Letting the fault be refused at load |
| D11 | At wire 29 a map monster that does not fit its sector is spawned on its floor, as the C does (item `GIB4`) | Skipping the fit for every map thing; keeping `GIB4` refused; a witness at the door |
| D12 | The roster preflight admits a roster monster after the player and impact suffix while respawning holds | Also requiring it to carry a pending corpse's spawn point |
| D13 | A read of a freed respawned corpse is a refuse-the-tic witness, `FreedRead` | A model of the zone allocator; reading it as NULL; reading the last record forever |
| D14 | The preflight leaves a removed corpse named as a live monster's target to `A_Chase`'s read (item `STALE2`) | The old preflight refusal (89 tics early in `STALE2`) |
| D15 | The real-map check is at the simulation level, the genuine load schedule being the only input (the intermission's length) | The session level (it did not exist yet) |
| D16 | `BOSS2` and `FASTOUT` in `wire29_stale.py` with per-item header bytes | A new tool |
| D17 | A missile far beyond the map's rectangle (past 32,767 minus margins) stays refused | Reproducing the overflowing arithmetic there (not reached) |
| D18 | A paused display runs the status bar and message tickers and was first drawn without M_PAUSE (temporary, removed in step 7) | Refusing every paused tic until the picture existed |
| D19 | A paused load tic is reproduced (the load's sounds on the load tic, stripped from tic 0's records later) | A refuse-the-tic witness |
| D20 | `DSES` 4 = `DSES` 3 plus 3 bytes after screenblocks and a display kind byte | A separate layout per embedded version; the flag in the `DSIM` (N6 (a)) |
| D21 | Saving refused once any paused frame was shown (step 6; superseded: step 7's `DSES` 4 saves while paused) | Refusing only while paused |
| D22 | The session test reads the 13 missing M6b session streams from new goldens pinned by `m6b_genuine.txt`'s digests | Comparing Rust-built text with the digests |
| D23 | The encoder correction regenerates this PR's `wire29_state.txt` (15 C rows of `PAUSE` and `PAUSE0`) | Keeping the mis-projected rows |
| D24 | A missing or malformed M_PAUSE is refused at the tic whose frame would first be paused | Refusing at session start; drawing nothing |
| D25 | `DDSP` 5 = `DDSP` 4 plus 9 bytes at offset 8 | A new whole layout; deriving `level_paused` from the capture |
| D26 | `DSND` 4 = `DSND` 3 plus 9 bytes at offset 67 | Storing level tics; dropping `mus_paused` |
| D27 | New constructors with an internal `Option<Pause>` (`Display::new_session_pause`, `ChainSound::new_pause`) | New `SessionConfig`/`ChainMode` variants (every exhaustive match of the frozen configurations) |
| D28 | The session sets the display's flag and the sound's toggle before the state switch and takes them back on a refused tic | Passing `paused` through every call |
| D29 | `viewz` 1 at a world-done load, for pause displays only | All configurations (they never draw that frame) |
| D30 | `head_owed` derived on a `DSES` 4 restore | A stored byte |
| D31 | No small view sizes: the picture's place is compared at 10 and 9 through the view tables | The border and sizes below 10 in the display now |
| D32 | Mixer goldens for all 11 committed M6b and wire 29 sound streams, without melt rows | The four pause items only |
| D33 | `wire29_pause.py` also keeps the new items' frame, pause and sound streams | A separate tool |
| D34 | The v4 reader takes any nonzero byte 5 or 6 as set | Admitting only 0 and 1 (refuses genuine recordings, [Q-g_game-1559a](../quirks/g_game.c.md)) |
| D35 | The encoder keeps a pending mobj through paused dumps | Projecting only unpaused dumps |
| D36 | `doom-play` uses the wire 29 configuration for every skill | Wire 28 for skills 0 to 3 without flags (two recorders in one app) |
| D37 | The hand-test check is a kind of `wire29_real.py` (`sessions`) comparing the simulation and the session's G columns and captures | The full gate with frames, sound and mixer on recordings |
| D38 | The session file name keeps its form; the flags are in the header bytes and the exit line | A name token for them |
| D39 | The recorder records only `0x81` (N5) | Recording the other special bytes |
| D40 | **Owner (a):** `P` is a second key for the original's pause under `--bindings modern` only | A `--pause-key` option; help text only; nothing |
| D41 | Mutation: each crate's mutants first judged by that crate's own tests (the wire 28 method), then the missed ones with `doom-game`'s tests added | The CI judge in one run (a caught mutant cost the whole 342-test `doom-game` suite) |
| D42 | Phase 2 in two tiers: the `doom-game` test binaries named `wire29*` first, then the full suite for what survived | The full suite for every missed mutant |
| D44 | **Owner (b):** the walk's wrapping `int` step sum (`p_maputl.c:873`) is followed as the strict build wraps it; WRAP is compared through its last capture; the refusal was removed | (a) refuse the tic at the first overflowing sum (built, then replaced); (c) admit only sums never read again |
| D49 | **Owner:** recorded for the future cheats milestone, nothing built: under `--bindings modern` the letters of the cheat strings are also bound (`P` pauses; `a`, `s`, `d`, `w` move; `e` uses) | (a) as the original, keys do both; (b) a cheat-typing mode; (c) a lockout while `id` is matching; (d) cheats only under vanilla bindings |
| D50 | **Not this PR, nothing built, no recommendation from the building agent:** a labelled non-vanilla option that plays on past a freed read. The options seen in the runs, (a) to (d), are in [§18](#18-decisions-d50-to-d53) | Today: (d), the session stops at the read |
| D51 | The later-level projection of a paused load tic's sound records: pending at the paused load capture and first in tic 0's last (the `DSIM` 42 text of STATE_FORMAT) | (b) leave `events.sounds` out of later-level comparisons; (c) record the load's records under the session tic they were made at only |
| D52 | `BARRELP` and `BARRELF` end at the M5b runner's declared `AttackerRemoved` witness (the status bar's presentation); the simulation test plays `BARRELF`'s read tic past the last capture, compared with nothing | (b) monster victims only, so the runner runs on (more authoring) |
| D53 | The planted fault `sweep` also zeroes the threshold of a mobj whose target it clears | (b) the target only (the port's `DSIM` 45 reader then refuses a barrel with a threshold and no target) |

Also owner-ruled in these steps, without a number: finding F1 ([§7](#7-finding-f1-a-fast-fireball-through-a-maps-outer-wall)) is
reproduced, not refused, unless a run shows dependence on memory outside defined state. No cheat lockout of any kind was added.

## 3. The 19 synthetic items against the genuine engine (CI)

The M6b runner's 19 items ([phase 1 §6.1](../M6B_REFERENCE_INVESTIGATION.md#61-the-genuine-side-built-in-this-phase)) run through the independent
`DSIM` 45 encoder, [`tools/reference/level_snapshot_wire29.py`](../../tools/reference/level_snapshot_wire29.py), a subclass of the read-only
DSIM43 chain. [`wire29_goldens.py`](../../tools/reference/wire29_goldens.py) checks each item's dump-set digest, tics, captures and header
bytes against `tests/reference/m6b_genuine.txt`, projects the capture of every tic and writes
[`wire29_state.txt`](../../tests/reference/wire29_state.txt). For skills 0 to 3 without `-respawn` each capture is also projected to
`DSIM` 44 and must equal wire 28's.

| Fact | Count (run 2026-11-26/27, `--check` exit 0) |
| --- | --- |
| Items, projected captures, variant (`V`) rows | 19, 9,318, 33 |
| `V` rows whose variant first differs over `DSIM` 45 at the capture its dumps first differ in `m6b_genuine.txt` | 32; the 33rd (`clamp`, skill 5) is refused by the encoder (skill 5 is not a `DSIM` 45 value) |
| Captures equal to the genuine engine in `nightmare_genuine_tests` | 9,318, every one also read by the `DSIM` 45 reader; every item ends complete (the 19 items are `AMMO4`, `BITS4`, `BITS3`, `CLAMP5`, `REACT4`, `REACT3`, `REACT3F`, `FAST4`, `FAST3`, `FAST3F`, `RESP4`, `RESP3`, `RESP3R`, `BLOCK4`, `GIB4`, `PAUSE`, `PAUSE0`, `PAUSEWI`, `PAUSEFIN`) |
| Planted-fault rows (the Rust port with the fault first differs at the variant's capture and equals the variant's digest there) | 31 at the pause step (12 for the ammunition, reaction time and fast table; 16 for the respawn; 3 for the pause); `Clamp` in the demo reader and `WrapZero` in their own tests |

How the intermediate steps were checked (each on the then-current head, all compared with the genuine engine, each ending where the next
fix was due): step 1 had 2,618 captures equal (each item ending at the then-pending refusal: the first fast missile, fast state or fast chase, the
first respawn, the first special byte); step 2 and 3 (ammunition, spawn rule, fast table, `A_Chase`) 4,610; step 4 (respawn) 9,007; step 6 (pause) 9,318. The
respawn items `RESP4` (4 kills of 2 monsters), `RESP3` and `RESP3R` run their whole level (1,317 captures), `BLOCK4` 1,645 and `GIB4`
1,068. `GIB4` was refused at load at every wire until D11: the respawn happens inside the closed door.

**`CLAMP5`** (a demo skill byte of 5) equals `BITS4`'s captures; with the reader's clamp planted off the port differs at capture 0.
`REACT4` and `FAST4` show the 0-tic reaction time and the halved table; `REACT3F` and `FAST3F` the same table at skill 3 with `-fast`.

## 4. Items beyond the M6b runner

Each is our own map, run in the same genuine build (strict, overflow, address and an observer build with identical dumps, sound and session
streams); the observer prints what the plain build cannot. The address builds are blind to the zone allocator (below); `ASAN_OPTIONS` has
`detect_leaks=0` in these runs: leak detection is disabled, which is not LeakSanitizer coverage.

| Item | What it shows | Result |
| --- | --- | --- |
| `STALE` | The player killed by an imp's fireball; the imp, killed by a barrel's blast, respawns later, so `attacker` names the freed corpse ([§6](#6-the-stale-pointer-after-a-respawn)) | 1,411 captures equal (0 to 1410, the read while the corpse is pending included); refused at session tic 1410 with `FreedRead`, state kept |
| `STALE2` | A sleeping imp whose `target` is a zombieman's freed corpse is woken by sourceless damage and `A_Chase` reads the target | 3,227 captures equal (0 to 3226, the sleep on a freed target included); refused at session tic 3226 with `FreedRead` |
| `BOSS2` | Two Barons telefragged, respawned (leveltimes 1344, 1920, 2432) and telefragged again; `A_BossDeath`'s tag-666 call at 146, 1494 and 2343 returning 1, 0, 1 | Equal at all 2,701 captures, no fix; mutation (skip a 0-unit floor) fails at capture 2344 |
| `FASTOUT` | A fast fireball leaves the map ([§7](#7-finding-f1-a-fast-fireball-through-a-maps-outer-wall)) | 141 captures equal; with the follow rule forced off, refused at session tic 55 |
| `WRAP` | The block-walk overshoot's wrapping step sum, p_maputl.c:873 (audit 1's item, `overshoot.wad`) | Equal at all 58 captures, no refusal (ruling D44 (b), [§15](#15-the-walks-step-sums-wrap-and-stepread)); 7 overflowing sums, all at 873, none read again; the overflow and address builds stop at the first (after capture 53), the strict build, which is the claim, goes on |
| `DEADSPEC` | `0x81` on a dead player's tics; `0x83` reborns | Genuine and port equal; paused 170 to 179, the unpausing `0x81` at 180 gives no reborn, `0x83` at 185 reborns at 186 |
| `TURBOP` | The turbo message set on a paused tic, shown by the status bar's ticker while paused | Equal; message on at session tic 256 (paused), not at 160 |
| `LOADP` | A paused load tic (`PAUSEWI`'s second level, tic 0 at 146) | Equal; found the fixes F2 and F3 below |
| `REBORNP` | `0x81` on a reborn's load tic | 260 tics, 4 paused frames, every frame, sound, music and B row equal; mutation `&&` to `||` at session.rs:472 fails at the paused reborn tic's frame; its mixer golden was missing until the pre-push check ([§16](#16-pause-around-melts-and-reborns-and-the-mixer-golden-gap)) |
| `STEPREAD` | An overflowed step sum (p_maputl.c:868) read again by the walk ([§15](#15-the-walks-step-sums-wrap-and-stepread)) | 17 captures equal, no refusal |
| `MELTP` | `0x81` around three screen melts ([§16](#16-pause-around-melts-and-reborns-and-the-mixer-golden-gap)) | 175 tics, 7 paused frames, 127 captures, 3 melts of 115 steps, all equal |
| `DEADEXIT` | A paused load tic after a dead player's exit (review finding R2, [§17](#17-the-independent-read-eight-findings)) | 188 tics, 4 paused frames, equal after the fix |
| `BARRELP`, `BARRELF`, `BARRELN` | A barrel whose first wounder respawned explodes: read while pending, read freed, nothing in range (R1) | Equal; `BARRELF` refused at 961 with `FreedRead` |
| `MISS0`, `MISSP`, `MISSF` | A fireball whose shooter respawned: never touches, touches while pending, touches after the free (R3) | Equal; `MISSF` refused at 804 with `FreedRead` |
| border (`wire29_border.py`) | The M_PAUSE picture at screen sizes 10, 9, 5 and 3 with our own border lumps | Place found once per size: `(126, 4)`, `(126, 16)`, `(126, 48)`, `(126, 64)`; 214 paused frames at each size |

The five "read only" items of phase 1 that this PR ran: a second boss death with the tag-666 call (`BOSS2`); a special byte on a dead
player's tic (`DEADSPEC`); the turbo message during a pause (`TURBOP`); the pause picture below screen size 10 (border); and, new here, a
paused reborn load tic (`REBORNP`). What stays unrun is in [§14](#14-limits-and-everything-read-not-run).

## 5. The session, frames, sound and mixer

The session is compared with the genuine session streams by `wire29_session.rs` (its list now has 24 items; the totals in this paragraph were counted when it had 22, the 19 plus `DEADSPEC`, `LOADP`, `TURBOP`, and are not recounted: read, not run;
12,334 session tics; every G column, C, I, J and F row equal; 9,974 first-level captures equal; paused tics `PAUSE` 214, `PAUSE0` 21,
`PAUSEWI` 9, `PAUSEFIN` 111, `DEADSPEC` 10, `LOADP` 13, `TURBOP` 214; the intermission's kill percentages 200, 150 and 100 for `RESP4`,
`RESP3R` and `RESP3`). The frames, the pause picture, the music calls and the mixer by `wire29_frames.rs`: 14 runs, 11,460 tics; level
frames 5,041 (whole digest, rebuilt F row, face-zeroed digest, draws, newly mapped lines, status), frames outside a level 3,708, paused
frames 926 (B rows), music calls 42, sound rows 15,442, mixer rows 1,298 (7,057 buffers), all equal. `REBORNP` and its 4 paused frames
are a further test. Melt step pictures are not compared (the M6b goldens used the counter melt clock; no melt goldens exist); the buffer
mixed after each melt is. The 13 M6b session streams that were not committed are regenerated by the strict runner into
`tests/reference/wire29_session/` and pinned by `m6b_genuine.txt`'s digests.

[`wire29_mixer.py`](../../tools/reference/wire29_mixer.py) runs the frozen M5c mixer harness on the 8 M6b and 6 wire 29 sound streams
(`--check` at the last head, exit 0): 29 files, 14 items, 316 starts, 9,631 tics, 5,934 buffers; strict, overflow, address and the model
identical; `detect_leaks=0`. Self-tests of the tool:
a flipped stream byte and a moved start are both reported.

**The two pictures** (README). [`wire29_readme_visual.py`](../../tools/media/wire29_readme_visual.py) draws `docs/media/wire29-pause.gif`, the
Rust frames of `PAUSE`, each equal to the genuine stream digest; its PAUSE picture is our own placeholder graphic, a black box.
[`wire29_resp4_visual.py`](../../tools/media/wire29_resp4_visual.py) draws `docs/media/wire29-resp4-intermission.gif`: the genuine engine
(the strict M6b runner, relinked with an observer that dumps each intermission picture) and Rust side by side with their difference, on
`RESP4`'s intermission (session tics 1,316 to 1,515, every 4th shown, 51 frames). Observed when it was made: 200 of 200 pictures equal
byte for byte (0 differing pixels) and each equal to its committed digest; the genuine kill counter reaches 200 percent; `--selftest`
(a flipped pixel) exits 1; `--check` reproduces the file. Local: it needs a C compiler and cargo and is not in CI.

**Planted faults of the session** (each with the variant's digest, or the stream line where the variant has none): `pause_mask` at `PAUSE`
capture 137; `pause_run` at `PAUSE` 73 and `PAUSE0` 1; `pause_st` at session line 154 (tic 72); `pause_keep` at `PAUSEWI` tic 142; `pause_wi`
at tic 127; `pause_hu` at `PAUSE` frame 145, hashing to the variant's F row digest; the picture one row lower at tic 72. A mutation that
removes the stripping of tic 0's load records fails `LOADP` at tic 146.

**Later levels.** `wire29_pause.py` also dumps each later load of its items and projects the later levels (`tests/reference/wire29_session/<item>_levels.txt`):
`DEADSPEC` 74 captures, `LOADP` 28, `REBORNP` 74, `MELTP` 36, `DEADEXIT` 40, 252 in all, one per session tic of the later level (paused tics
included); `later_levels_equal_the_genuine_dsim45_captures` compares each with the port (252 equal, each read by the `DSIM` 45 reader).
`PAUSEWI`'s later level is not projected (its M6b run is not in this tool: not done). See finding R5 in [§17](#17-the-independent-read-eight-findings).

**Fixes the new evidence found** (each: C evidence, fix, test):

- **Encoder, step 6.** `level_snapshot_wire29.py` read a capture's sounds at the dump's leveltime; after a pause every record came from the
  wrong session tic. Found at `PAUSE` capture 119; the 15 C rows of `PAUSE` and `PAUSE0` were regenerated (D23).
- **F2 (`head_owed`).** Restoring `DSES` 4 between `LOADP`'s paused load tic and its tic 0 restarted the carried chainsaw's sound at 146; the
  flag is now derived on restore (D30).
- **F3 (`viewz`).** A paused load tic of a carried player is drawn from `viewz` 1 (`P_SetupLevel`, p_setup.c:604, until tic 0's
  `P_CalcHeight`); `LOADP`'s frame 142 had 1 visplane where the genuine engine drew 5 (D29, Q-p_setup-604).
- **Encoder, step 8.** A mobj marked removed in the tic before a pause stays pending through the paused dumps (p_tick.c:135-136) and is
  freed at the first unpaused tic; found on a real-map replay with pauses, the Rust port already matched (D35).

## 6. The stale pointer after a respawn

`P_NightmareRespawn` removes the corpse (p_mobj.c:408) and nothing sweeps the pointers that name it; `P_RunThinkers` frees the block at
the corpse's next turn (p_tick.c:107-112). The paths that read such a pointer, in the Episode 1 monster set: `P_DeathThink`'s read of
`player->attacker->x` (run, `STALE`), `A_Chase`'s reads of `target` (run, `STALE2`), and a missile's `target` on contact (p_map.c:298-301; run since, `MISSF`, [§17](#17-the-independent-read-eight-findings)). What the genuine engine does (run, strict, overflow, address and observer builds identical): `STALE` has the
player dead from capture 924, the respawn at leveltime 1408, one read while the corpse is pending (block still in use), then 108 reads of
the freed block to the end (1,518 tics), 0 `Z_Malloc` blocks overlapping it; it computes the angle to the corpse's last coordinates, so the
dead player keeps facing where the corpse lay. `STALE2`: one read by `A_Chase` of the freed block (health and flags of what the corpse
left), the imp goes back to its spawn state with `target` kept.

**AddressSanitizer cannot see it.** The zone is one `malloc` at start-up and `Z_Free` writes only block headers, so the bytes stay and the
sanitizer sees no free. A later `Z_Malloc` over the block would make the pointer name whatever was put there (the dump would then show a
valid index); the rover allocates forward and the corpse's block is far behind it, so in these runs nothing reused it (observed: 0 blocks;
an authoring run with a 2,600-tic tail: 2,058 freed reads, 0 reuse).

**What wire 29 does (D13, D14).** The first read of the retired corpse is a refuse-the-tic witness, `SimError::FreedRead`, state kept
(`STALE`: session tic 1410; `STALE2`: 3226). The read while the corpse is pending is reproduced. A live monster's removed target is left to
`A_Chase` (D14); the chase guard that used to `unwrap()` the target now refuses. Two more readers, found by the independent read, are in
[§17](#17-the-independent-read-eight-findings): a barrel's explosion (p_inter.c:806-809) and a missile's contact (p_map.c:298-301). Whether the real-map skill 4 runs met a `FreedRead`, a `MapScale` or a stale-target refusal:
REAL-MAP-FIGURES-PENDING ([§8](#8-real-maps-and-the-session)). Quirk rows Q-p_mobj-408 and Q-p_inter-680.

## 7. Finding F1: a fast fireball through a map's outer wall

On the fast table a fireball (speed 20, radius 6) can cross a one-sided blocking line in one `P_TryMove`: `P_XYMovement` halves only when a
component exceeds `MAXMOVE/2` (p_mobj.c:152) and the destination box does not touch the line. It leaves the vertex rectangle and keeps
flying; on one real map the fireball flew flat outside the map until the level ended. Speed 10 never
exceeds twice the radius, so the slow table cannot. Found by the real-map skill 4 replays, which refused it as an escaped missile.

**Owner's ruling (2026-11-27): reproduce, not refuse, unless a run shows dependence on memory outside defined state.** The evidence of
defined state: every blockmap index is bounds-tested first (p_maputl.c:431-448, 481-487, 520-526, 379-382, read) and `FASTOUT`'s observer
build counts 22 line-iterator and 32 thing-iterator out-of-range cells, all returned before an index was formed, and 0 unlinked. The
address build is clean but blind to zone memory, so the claim rests on the bounds tests. Wire 29 follows a missile (imp or Baron fireball,
rocket; flying or exploding) outside the rectangle up to 32,767 minus margins (D17), through the position preflight, the monsters
preflight and the actor bound. Item `FASTOUT`: 141 captures equal; planted off, refused at session tic 55. Not run: a Baron's fireball
or a rocket outside (inferred from `info.c` radii and speeds). Quirk row Q-p_mobj-152.

## 8. Real maps and the session

Local only, on a scratch copy of the retail IWAD; counts, digests and pass/fail only. [`tools/local/wire29_real.py`](../../tools/local/wire29_real.py)
replays the 61 committed real-map recordings under wire 29 (kinds `skill4`, `respawn`, `fast`, `both`, `own` and, with pause commands
inserted, `pause`), each against the genuine M6b runner at the simulation level (every level projected by the `DSIM` 45 encoder, compared
capture by capture, the genuine load schedule being the only input, D15) and, with `--session`, through the session as `doom-play` plays it
(every session tic's G columns and every capture). Self-tests: a changed Rust command at tic 100 is caught at its tic; an extra genuine
`P_Random` draw is caught at the next capture; unpausing commands without their tic's movement fail the shifted comparison.

The pause kind inserts five pause pairs per run (a pair `0x81` ... `0x81`, `0x81` ... `0x85`, `0xfd` ... `0x81`, `0x85` ... `0xfd`, and a lone
`0x80`) on tics where the player's buttons are 0, and requires (1) genuine and Rust agree at every capture and session tic and (2) the
paused run's captures on its unpaused level tics equal the unpaused run's one for one (the two fields an inserted byte changes are left out;
runs with a forward above 50 also leave out the turbo message). `0x83` is not inserted: its use bit would reborn a dead player.

**Results:** REAL-MAP-FIGURES-PENDING (the 305 simulation-level replays: captures equal, refusals, genuine respawns; the pause and skill 4 runs
at the session level: tics, captures, paused tics, respawns, shifted-comparison captures). Earlier batches
were stopped for corrections of the tools (an encoder deficiency on pending mobjs, a shifted-comparison digest), never for speed.

**Replays that end at the freed-read refusal** (a respawning session can stop at a read of freed memory, [§17](#17-the-independent-read-eight-findings)):
of the 305 final replays, REAL-MAP-FIGURES-PENDING end at it; of the six hand recordings ([§9](#9-the-owners-hand-test-2026-11-27)),
REAL-MAP-FIGURES-PENDING. A replay that ends there ends complete up to that tic and is counted as a refusal, not as a failure.

**The two sums behind the README's evidence sentence** (counted as the owner ruled on 2026-11-27; both are filled in afterwards):

| Sum | Counts | Does not count | Figure |
| --- | --- | --- | --- |
| Replays equal to the genuine engine | every replay of an existing recording on another skill, with `--fast`, with `--respawn` or both (kinds `skill4`, `respawn`, `fast`, `both`; where the pause kind belongs is not in the ruling and is left to the final count) | the unchanged control replays (kind `own`) | REAL-MAP-FIGURES-PENDING |
| Distinct recordings | the committed real-map recordings replayed, and the six hand recordings of [§9](#9-the-owners-hand-test-2026-11-27) | a recording counted twice | REAL-MAP-FIGURES-PENDING |

The README sentence, with the figures to fill in: "N replays of M distinct recordings equal the original's engine tic for tic (a replay of an existing recording on another skill or option counts, an unchanged one does not)", N = REAL-MAP-FIGURES-PENDING, M = REAL-MAP-FIGURES-PENDING.

## 9. The owner's hand test, 2026-11-27

The owner played the Windows build of `f570dc36` (the CI artifact run #34) with `--bindings modern`. The check
(`wire29_real.py --kind sessions --recording ...`, jobs 5, exit 0, examples built from `f570dc36`) compared each recording at the simulation
level and the session level (G columns and every level capture, paused tics and paused load tics included); both self-tests failed as they
must. The directory held five recordings (the owner had said three); all five were checked. A sixth, made later with `--map 2 --skill hmp
--respawn --fast`, was checked the same way (exit 0, both self-tests pass).

| Recording (SHA-256, first 16 hex) | Map, skill, flags | Session tics | Level captures equal | Paused tics | Genuine respawns | Levels |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `955e16bae458bdc1` | E1M1, 0 | 1,030 | 765 | 33 | 0 | new, carried |
| `480bd9cc2e2e3a34` | E1M1, 0 | 1,387 | 1,070 | 325 | 0 | new, carried |
| `4a010ee8d646b554` | E1M1, 4 | 2,701 | 2,701 | 0 | 3 | new, reborn |
| `8ddcb476bbe70b3c` | E1M1, 4 | 2,105 | 2,105 | 439 | 0 | new |
| `63bcca8455427fca` | E1M1, 4 | 198 | 198 | 39 | 0 | new |
| `f03dde04583ad4a8` | E1M2, 2, `--respawn --fast` | 4,060 | 3,966 | 0 | 11 | new, carried |

Sums: 11,481 session tics, 10,805 level captures equal, 836 paused tics, 14 genuine respawns, 0 refusals, 0 failures. The session
tics outside level captures are the intermission, loads and melts. **Not compared by this check:** frames, sound rows and mixer buffers on
the recordings (compared on the synthetic items in CI), and the intermission and finale rows other than the G columns. **Not exercised
by the owner's recordings:** the finale (no recording reached a victory). The check's own self-test also made a recording headlessly through `doom-play`'s app
(skill 4, `--respawn --fast`, the Pause key at four tics): 1,500 of 1,500 captures equal at both levels, 61 paused tics.

## 10. Restore and continue

`wire29_restore.rs` (4 tests): a wire 29 session is saved, decoded, restored and re-saved at **every** tic of a window, each restored
session then stepped 20 to 25 tics beside the unbroken one on the same commands, compared at every tic on the report (kind, paused, melt,
sound incl. the mixed buffer), the frame pixels, the music calls, the level's whole `DSIM` 45 snapshot and every melt step; at the end the two
`DSES` 4 encodings are byte-equal. Windows: paused tics (`PAUSE` 68 to 118, 51 restores), the respawn gate and both fogs (`RESP4`, `RESP3R`,
35 restores each; the gate tic read from `m6b_genuine.txt`), loads that clear a pause (`PAUSEWI` 120 to 150, 31 restores; `LOADP` 138 to 150,
13 restores). The test can fail: with `head_owed` forced false the `LOADP` window failed ("restored at 143, tic 146"). Restore is the clone
`restore_v4` takes (there is no `Simulation` constructor from `DSIM` bytes), so the `DSIM` 45 side is compared on every tic rather than
separately. The synthetic frames and the session pass in release. Rust-only: no genuine engine ran a restored session.

## 11. Fuzzing and sanitizers

Five new targets: `wire29_dsim45`, `wire29_dses4`, `wire29_ddsp5`, `wire29_dsnd4`, `wire29_demo4`. The workspace forbids `unsafe`, so the
AddressSanitizer fuzz runs are the only sanitizer coverage of the new readers; nothing more is claimed. **Leak detection was on**
(`ASAN_OPTIONS` and `LSAN_OPTIONS` unset). Seeds (written outside the repository by the ignored test `write_fuzz_seeds`): 5 saved states each
of `DSES` 4, `DSIM` 45, `DDSP` 5 and `DSND` 4 and 44 demos.

| Fact | Observed |
| --- | --- |
| Build, `cargo +nightly fuzz build --sanitizer address` (all targets) | exit 0 |
| Seed replay (`-runs=0`) | exit 0 for all five (seeds 5, 5, 5, 5, 44) |
| Campaigns, 601 s each, `-seed=1 -timeout=20 -rss_limit_mb=2048`, corpus a copy of the seeds | no crash, no leak, no artifact: `wire29_dsim45` 1,345,675 runs; `wire29_dses4` 280,156; `wire29_ddsp5` 347,693; `wire29_dsnd4` 18,967,644; `wire29_demo4` 7,673,921 |
| Leak plant (a scratch copy of `wire29_dsim45` that leaks an accepted input) | seed replay exit 77, "LeakSanitizer: detected memory leaks", 10,889 bytes in 1 allocation; with `detect_leaks=0` exit 0; the unmodified target exit 0 |

**Not run:** a coverage-guided campaign without the sanitizer (wire 28 made both), campaigns longer than ten minutes, a measure of how
many mutated inputs the readers accept. The fuzz workspace's `cargo +nightly check --bins` passed at the display step (compiles only).

## 12. Mutation testing

**mutation: pending.** The `doom-sim` (401 mutants) and `doom-game` (207) runs were unfinished when this record was written. The numbers
below are the finished crates only; the survivors of the other two and their answers are filled in afterwards. Method: cargo-mutants 27.1.0
with cargo-nextest 0.9.151 on `git diff 682de22c HEAD -- crates/`, a worktree on the Linux disk, D41 and D42.

| Crate | Found | Phase 1 caught | Missed | Timeout | Unviable | Phase 2 caught of missed and timeout | Killed by new tests | Survivors |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: |
| `doom-sound` | 50 | 6 | 31 | 0 | 13 | 23 of 31 | 7 of 8 | 1 |
| `doom-render` | 135 | 30 | 67 | 10 | 28 | 62 of 77 | 12 of 15 | 3 |
| `doom-play` | 3 | 2 | 0 | 0 | 1 | - | - | 0 |
| `doom-sim` | 401 | pending | | | | | | |
| `doom-game` | 207 | pending | | | | | | |

**Survivors so far, each answered.** (1) `chain_pause.rs` `<` to `<=` in `ChainSoundStateV4::decode`: equivalent (both return
`Truncated` at 67, 75 and 76 bytes; scratch probe). (2) `d_display/session.rs:472` `&&` to `||`: killed afterwards by `REBORNP` (a paused
reborn load tic, see §4). (3) `pause.rs:68` delete `level_paused: 0` in `Pause::fresh`: unreachable (`fresh` runs only at tic 0, where
the count is 0). (4) `pause.rs:246` `-` to `+` in `check_parts`: equivalent in every state a session saves. New tests that kill mutants:
`dsnd4_reader.rs` (2), `chain_pause_tests.rs` (2), the sound-session test in `wire29_restore.rs`, `wire29_display.rs` (5); their expected
values are the genuine `paused` column, `m6b_genuine.txt`'s R rows and written module rules, never Rust output.

<!-- MUTATION-PENDING: doom-sim and doom-game results, survivors and kill tests are added here -->

## 13. The frozen wires, and the instruction counts

**Wires 1 to 28 gain and lose no refusal and change no result (run).** Of the files that hold the walk, only `intercept_vector.rs`
differs from master (35 insertions, 1 deletion: wire 27's `.ok()` became a match whose error goes to a cold wire 29 function that
returns `None` at once when the world has no parameters; parameters are set only under wire 29). `movement.rs` and `combat_trace.rs`
are master's text. The base (`682de22c`) and the head were built in release and compared: the 51 examples that run without arguments
exit 0 in both (`wire28_witness_timing` exits 1 in both: its usage message), 104 output files and 170 stdout lines identical,
`overshoot_walk`'s two tests pass in both, every `doom-sim` release test has the same status at both heads (1,461 passed at the base,
1,477 at the head: 16 head-only wire 29 tests). The one old wire whose walk step sum overflows in a test, wire 14's soak, gives identical
state digests at base, head and an instrumented tree (4 seeds), so it wrapped silently before and still does; the genuine engine did not
run it. An old-wire `WRAP` variant that reaches the overflow was searched for and not found.

**Instruction counts (Callgrind, deterministic, not timings; Rust 1.85.0 release examples, ext4, run alone).** The nine CI scenarios
against `tests/reference/m4p_ir_baseline.json`: `bench_advance.py ir --check` exit 0 ("threshold 3.0%: ok") at the last measured head,
all between +0.18 % and +2.12 % (the largest: `BVB1_wire24` +2.12 %, `TFRAG1_wire24` +1.42 %). A first measurement of an earlier head was over
the 3 % line (up to +4.2 %); two inlined checks were moved off the old wires' per-actor path (an escaped-missile test in a cold path and
the respawn thinker entered only when respawning holds) and the outcomes (admitted tics, final digests) are unchanged. The baseline and
threshold were not changed.

## 14. Limits and everything read, not run

- **Existing tests whose expectation changed (three, each only asserted that skill 4 was refused; dated 2026-11-27):**
  `crates/doom-play/src/main.rs` `tests::arguments` (`--skill 4` and `--skill nightmare` leave the refused list);
  `crates/doom-play/src/wire28_tests.rs` `skills_0_to_3_are_accepted_and_nightmare_is_refused` (the loop asserting "nightmare (4) is not built
  yet" removed; acceptance is asserted in `wire29_tests.rs`); `wire28_tests.rs` `the_help_lists_skills_0_to_3_and_the_escape_stop` (three help
  strings that said nightmare is refused removed from the wanted list). No test, fixture, golden or trace on master changed otherwise;
  `tests/reference/m6b_*` is untouched. This PR's own files moved their expectations as designed (`nightmare_genuine_tests.rs` ends and
  fault rows; `wire29_session.rs`'s `DSES` test, which asserted `PausedNotYet`, a refusal that no longer exists).
- **The original's pause is a fixed-rule stop, not a menu:** no pause during demo playback (the app has none: g_game.c:664-667 has no
  counterpart), the bit-6-alone byte and the save command stay refused, the pause's music calls are modelled without music.
- **Table histories (N4).** The table is a function of the options; the other histories (two `-fast` games in one process, a loaded save,
  the level-warp cheat) have genuine goldens and quirk rows and wait for menus, saves and cheats. `doom-play`'s restart is a new process.
- **Read, not run:** the MSRV workspace build and Windows and macOS CI at the final head (GitHub holds them); `S_StopMusic`'s extra
  resume when a pausing command lands on the completion tic (modelled, no item); a missing M_PAUSE (the refusal is built and tested on a
  synthetic WAD without it; no genuine item); the automap's `y = 4` picture place (no automap); a melt step picture with the pause picture
  in its end screen; Cacodemon and `MT_SPAWNCEILING` respawns (not in Episode 1); a monster awake in its see state at the moment its target
  is freed; a reused zone block; a rocket or Baron fireball outside the map; the original's music while paused; the genuine engine on
  wire 14's soak; older wires reaching a removed barrel source or missile owner (no corpse is removed there); a genuine `Z_Malloc` reuse of a freed corpse (none in any run; the scrub builds stand in); `STEPREAD` and `MELTP` under older wires; `PAUSEWI`'s later level; the sound or frames of a real-map pause (compared on synthetic items only); the Windows build of anything but the hand test.
- **Independent read:** done once, by reading only, at `c5c56685`: eight findings, answered in [§17](#17-the-independent-read-eight-findings). The reviewer ran nothing; the runs are the building agent's. A second read of the final diff is not recorded here.
- **Authoring exits.** Every nonzero exit seen while building is resolved; the ones that matter for method: the real-map batches stopped
  and restarted for tool corrections (not speed); one gate script of mine was killed when its head became obsolete (the D44 ruling);
  `cargo fmt --check` failed twice on my own new tests and was fixed in the next commit.

## 15. The walk's step sums: WRAP and STEPREAD

**WRAP under ruling D44 (b).** The first build refused the tic at the first overflowing step sum (decision D44 (a): `WRAP` compared at 54 captures,
refusal at session tic 53). The owner ruled (b) on 2026-11-27: wire 29 follows the wrapping `int` sum at p_maputl.c:873 as the strict build
(`-fwrapv`) wraps it, the way wire 27 follows `P_InterceptVector`'s sums, and the refusal was removed. Observed: the Rust walk equals
the genuine engine at **all 58 captures** of `WRAP` (each read by the `DSIM` 45 reader), no refusal; the golden counts 7 overflowing sums, all at line 873, at session tics 53, 53, 53,
54, 54, 55 and 56, every one dead (the next test is the end cell, so the wrapped value is never read again); the overflow and address builds stop at the first one
(captures 0 to 53 defined), and the strict build, which is the claim, goes on. The planted `WrapZero` fault first differs at capture 53. The test can fail: with
the sum refusing on overflow it fails (refusal at 53); with the sum saturating it still passes, because `WRAP`'s sums are all dead (see `STEPREAD`).

**The frozen-wire proof (run).** The base (`682de22c`) and the head were compared again after the change; the figures are in [§13](#13-the-frozen-wires-and-the-instruction-counts)
(104 output files and the `overshoot_walk` tests identical; wire 14's soak, which overflows the step sum twice, gives the same state digests at base and head).
`WRAP` itself, run under wires 26 to 28, is still refused at session tic 52 with `MapScale(Arithmetic)`, state kept, as before.

**`STEPREAD` (an overflowed sum read again).** The owner asked for an item where the overflowed sum is read again by the walk, equal to the genuine strict
build state for state, and a planted saturating fault that is caught. Built: our own room, the player's momentum large enough that `FixedDiv` saturates `ystep`
(session tic 7), so the sum at p_maputl.c:868 overflows and the next iteration tests it at line 866. Observed on the genuine engine: the strict build is
clean (17 captures); the overflow and address builds stop at line 868 after 8 dumps; the observer shows the overflow live (not the last trace) and the read
(`yintercept>>16` is -32,767 against `mapy` 1: false). The Rust walk equals the strict build at all 17 captures, no refusal. The genuine `saturate` variant
equals the strict build at all 17 `STEPREAD` and all 58 `WRAP` captures.

**Said plainly: a saturating fault cannot be caught here, by run or by code.** Run: replacing the sum by a saturating one in the Rust walk leaves both the
`STEPREAD` and the `WRAP` tests passing, and the genuine saturating build equals the strict one everywhere. Code (read, with the proof in the docstring of
`wire29_wrap.py`): a step is taken only when `(sum >> 16)` equals the current cell (p_maputl.c:866, 871), and the cells lie within
256 + 63 of the origin, so a sum is below 320 x 2^16 before the add; a `FixedDiv` step that did not saturate is below 2^30, so only MAXINT or MININT can
overflow the sum, and the wrapped value shifted by 16 lies in -32,768 to -32,450 or 32,449 to 32,767, as does the saturated one: never a cell the walk can be in.
Every later test is false either way and the sum is never stepped again, so wrapping and saturating give the same walk in every case. What the
tests can catch is a refusal (an `Arithmetic` refusal on overflow fails `STEPREAD` at session tic 7). Quirk rows Q-p_maputl-868a and 868b (868b, the older wires, stays not determined).

## 16. Pause around melts and reborns, and the mixer golden gap

**The mixer golden gap (found by the pre-push check).** `wire29_mixer.py --check` exited 1 on the check run before the push: item `REBORNP`
had no committed mixer starts file, golden or results row. Fixed by writing them (`REBORNP`: 5 starts, 260 tics, 160 buffers; its sound stream is byte-identical to `DEADSPEC`'s, so the two
goldens are identical). `--check` now exits 0 at the last head (the totals are in [§5](#5-the-session-frames-sound-and-mixer)). The `REBORNP` frames test now compares the mixer and fails with one golden digit
changed ("mixer row 18"); it does not itself assert that any mixer row exists (not changed).

**`MELTP` (the pause around screen melts).** Read, then run. The melt runs inside `D_Display`'s wipe loop (d_main.c:329-344): no `G_Ticker`, no input
read. A key pressed in it waits for `NetUpdate`'s event pass (d_net.c:402-403), and `G_BuildTiccmd` puts the pause in the next command (g_game.c:426-428), so
**the original has no command during a melt: the pause is in the first tic after it and that tic runs paused.** The pause picture is drawn before the wipe's end screen is copied (d_main.c:303-313, 327), so the
melt after a paused tic ends on the picture. A level load clears the pause (g_game.c:494). Item `MELTP` (`0x81` on tics 126, 128, 138, 140, 144; cut at 175):
genuine paused tics 126-127, 138 and 140-143, three melts of 115 steps, 127 captures. The Rust frames test (every frame, music call, sound row, mixer buffer and the 115 melt steps), the session test (every G, C, I, J row, 127
captures) and the `doom-play` test (Pause pressed and released in the start melt is held, no tic runs in the melt, the first command after it is `0x81` and that tic is paused) all pass. They can fail:
a melt-step digit, the pause picture skipped when a wipe starts, a paused bit of the session file and a planted app fault that drops the key each fail. The Rust port equals the
genuine engine: no fix was needed. Found, not fixed at that step: the session test's list lacked `REBORNP` (added at R5, [§17](#17-the-independent-read-eight-findings)).
The intermission's last tic is also a fire press in the tally (Q-wi_stuff-1480). Run under wire 29 only; older wires: not run.

**`REBORNP`** (`0x81` on a reborn's load tic): a paused load tic is reachable because `G_Ticker` runs the reborn, then `G_DoLoadLevel` (clears the pause),
and only then reads the command (g_game.c:612-614, 494, 698-708); `P_SetupLevel` sets `viewz` to 1 before the player is respawned and `G_PlayerReborn` clears it (p_setup.c:604, g_game.c:815),
so the paused frame is drawn from `viewz` 0. 187 captures, 4 paused tics, equal.

## 17. The independent read: eight findings

A fresh reviewer read the diff at `c5c56685` against the C and ran nothing. The owner ruled that no finding counts as confirmed or dismissed until a run shows it; the
order was R2, R1 with R3, R4 with R5, R7, and R6 a note unless a run shows an effect. **Five findings changed code or tests (R1, R2, R3, R4, R5); R6 shows no effect, R7 changed a
comment, R8 is a known placeholder.** The reviewer also checked correct: the corpse countdown and respawn order and random numbers, the Nightmare sites, the fast table (N4), the demo header and
commands, the pause order in `G_Ticker`, the pause picture's place, wires 1 to 28 untouched, the new readers, the Python encoders' independence and that the planted faults can fail.
The fold count of findings into the diff: not in the fact sheet, not stated here.

| Finding | What the read said | Confirmed or dismissed by | What was done |
| --- | --- | --- | --- |
| R2 (minor) | The paused load frame after a dead player's exit uses `viewz` 1 where the original, which reborns the player there, uses 0 (g_game.c:479-480, p_setup.c:604, g_game.c:815) | **Confirmed by a run:** item `DEADEXIT` (4 paused frames, 133 captures); with the old rule forced the test failed at session tic 148 with the frame of the altered engine `viewz1` | `viewz` 1 only when the new level's start is not a reborn (`world_done_viewz_one`, `begin_next_level_carried`); the planted fault reproduces the variant's digest at 148; quirk row Q-p_setup-604 |
| R1 (major, disclosure) | A barrel whose first wounder respawned is refused up front, though the original reads it only in `P_DamageMobj` of a victim in range (p_inter.c:806-809); COMPATIBILITY called this unreachable | **Confirmed by a run** (before the fix, `BARRELF` was refused at 961 and `BARRELN` at 961, where the genuine engine read freed memory at 961 / read nothing) | The up-front refusal stays on wires 21 to 28 only; wire 29 reproduces a pending read, plays on past a barrel with nothing in range and refuses the read of the freed block with `FreedRead`. Items `BARRELP`, `BARRELF`, `BARRELN` |
| R3 (minor) | A flying missile whose owner's corpse respawned is refused at the preflight, before any read (p_map.c:299-305, 324) | **Confirmed by a run** (before the fix: `MISS0` refused at 769 where the genuine engine never reads; `MISSF` refused at 769 where it reads at 804) | The owner is read lazily at contact; items `MISS0`, `MISSP`, `MISSF`. Wires 1 to 28 keep the preflight refusal |
| R4 (note) | The `DSIM` 45 reader accepts kill credit above the total whatever the skill | **Confirmed by reading and a test run** (every capture admitted it) | Credit above the total is accepted only with skill 4 or the `-respawn` option set; `dsim45_kills_pass_the_total_only_with_respawning` on real captures of an M6b map (accepts at skill 4, and with `-respawn` at skill 3 with and without `-fast`; refuses at skill 3 without it, and at skill 2 with `-fast`) |
| R5 (evidence gap) | The session test compared `DSIM` 45 digests only on the first level; paused load tics are on later levels | **Confirmed by reading** the test; the new comparison then **caught a gap**: `LOADP`'s paused load tic differed in `events.sounds` only (the projection skipped the S row of the load tic) | An encoder rule (D51) and later-level goldens, 252 captures equal ([§5](#5-the-session-frames-sound-and-mixer)); `REBORNP` and `DEADEXIT` joined the session list. `PAUSEWI`'s later level is not projected |
| R6 (note) | `head_owed` stays set after a restore at session tic 0 while paused | **Run, no effect:** `PAUSE0` restored after each paused tic 1 to 20 and at 21 and 22, 20 tics each beside the unbroken session: reports, frames, music calls, snapshots and the `DSES` 4 bytes equal | Nothing changed in code; a test `a_first_level_restored_paused_before_its_tic_0_continues_as_the_unbroken_one` |
| R7 (note) | The `escaped_missile` comment against the 16,384 cap | Read | Comment only: the bound subtracts the smaller of the sight margin and 16,384, and the `int` argument covers margins up to 16,384 |
| R8 (note) | Placeholders pending | Known | The `REAL-MAP-FIGURES-PENDING` and `MUTATION-PENDING` markers stay until the runs finish |

**What R1 and R3 changed in what the port promises.** The genuine engine reads whatever the freed block holds: `Z_Free` writes only the block's header, so the corpse's bytes stay until a later
`Z_Malloc` reuses the block (0 reuses in all eight freed-read runs). The outcome therefore depends on memory outside the defined state, which is why the port refuses. Scrub builds that fill the
corpse's bytes after its links when it is freed: filled with 0x00, `BARRELF` and `MISSF` dump the same as the strict build; filled with 0xff, both die of SIGSEGV (exit -11) at the read. The genuine facts of
the six items (strict, overflow, address and observer identical): `BARRELP`, the explosion at 960, after the removal, reads a pending source twice (the runner then ends at the M5b `AttackerRemoved` witness: D52), `BARRELF` two freed
reads, `BARRELN` none; `MISS0` none, `MISSP` one pending missile read and one source read, `MISSF` one freed read of each at 804. The planted `sweep` fault (every reference to the corpse cleared at its removal) first differs at 961 for the barrels and 769 for the
missiles; the port with the fault equals each variant's digest where it is not refused first. **Limits:** the first `sweep` made the port's reader refuse a barrel with a threshold and no target (D53, fixed); for `MISS0` and `MISSF` the port with the fault is refused at 769 (a flying missile with no owner), so it is not compared there; and the genuine engine with a real `Z_Malloc` reuse was never observed.

**What `doom-play` shows and saves** (run: test `wire29_tests::a_freed_read_ends_the_session_with_its_reason_and_the_demo_saved`, `MISSF` and `BARRELF` played through the app by vanilla keys): the session ends as refused at tic 804 or 961, the end screen's text is "simulation: FreedRead. The original would read freed memory here, through a pointer to a
monster's corpse removed when the monster respawned. What it reads depends on the memory allocator, so the session stops here instead of guessing.", the session summary contains it, and the demo saves, parses as version 4 and holds every command before the refused tic (804 and 961 commands). Without the new text the test fails ("simulation: FreedRead").

How many of the 305 final replays and the six hand recordings end at this refusal: REAL-MAP-FIGURES-PENDING ([§8](#8-real-maps-and-the-session)).

## 18. Decisions D50 to D53

**D50 (not this PR; nothing built).** A labelled non-vanilla option that plays on past a freed read. The building agent gave no recommendation; the options seen in the runs:
(a) clear every reference to the corpse when it is removed (the `sweep` fault): differs from the original from the respawn tic on, even where nothing ever reads the pointer (`BARRELN` and `MISS0` differ at 961 and 769 in
the target and threshold fields); (b) read a freed pointer as NULL at the read only (no source, no owner): differs only from the read on (no retarget, a kill credited to the first player for a counted victim, no species test);
(c) read the corpse's last record, what the genuine engine does while nothing reuses the block (the 0x00 scrub equals it, 0 reuses in all 8 freed-read runs): differs after a reuse, which the port cannot see without modelling the zone (D13 (b));
(d) refuse as now (the vanilla-only default). The owner decides, in a later milestone.
**D49** (cheat strings under modern bindings) is likewise for the future cheats milestone, nothing built. **D40 (a) and D44 (b) are owner-ruled** (rows in [§2](#2-decisions)); D51 to D53 are the building agent's, changeable before merge.

## 19. Nonzero exits of these steps

Each is resolved unless said. `wire29_mixer.py --check` exited 1 on `REBORNP` (§16, fixed). Authoring exits: `wire29_pause.py --only DEADEXIT` exit 1 (a declared address-build stop that did not occur: the build ran clean, the declaration was removed); `wire29_pause.py --only LOADP,REBORNP`
exit 1 ("the state build differs from strict": a missing directory, fixed); `cargo fmt --all --check` exit 1 three times on my own new tests (formatted); clippy exit 101 once (`filter_map_bool_then` in the `MELTP` session test, fixed);
`pkill -f` exit 144 twice, which killed my own shell and a background search (not repeated); the first documents-step GIF run (`no glyph for ;`, fixed); `wire28_witness_timing` exit 1 in base and head (its usage message). Expected failures, each reverted: the can-fail runs of the
`WRAP`, `STEPREAD`, `REBORNP`, `MELTP`, R1/R3, R2, R4 and `doom-play` tests, and the R2 and R1/R3 confirmations before their fixes. Last gates at `1861257f`: `cargo test --workspace` (debug) 180 result lines, 2,334 passed, 0 failed, 17 ignored; the release
tests of `doom-sim` and `doom-types` 1,487 passed (91 lines), of `doom-game`, `doom-render`, `doom-sound` and `doom-play` 814 passed (77 lines); `--check` of `wire29_goldens` (19 items, 9,318 captures, 33 variant rows), `wire29_stale` (38 files, 10 items, 14,104 captures),
`wire29_pause` (61 files, 13 pinned streams, 6 new items), `wire29_mixer`, `wire29_border` (5 files) and `wire29_wrap` (5 files) all exit 0; `bench.sh` exit 0 within 3 % (largest +2.13 %), run beside a mutation run, so only instruction counts. Not run: fuzz builds, MSRV and Windows and macOS CI, rustdoc at that head.

