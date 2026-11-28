//! Wire 29 (`PlayerMonstersEpisode1V7`, DSIM45): Rust-only tests of the profile,
//! the admission of skill 4 and the parameters, and the DSIM45 writer and reader.
//! No genuine engine runs here; `nightmare_genuine_tests` compares with it. The maps
//! are the M6b synthetic slots (`tests/reference/m6b_wads/m6b.wad`).
use crate::identity::{OriginalActorType, OriginalState};
use crate::nightmare_genuine_tests::level;
use crate::*;

const V6: OriginalExecutionProfile = OriginalExecutionProfile::PlayerMonstersEpisode1V6;
const V7: OriginalExecutionProfile = OriginalExecutionProfile::PlayerMonstersEpisode1V7;
const NONE: GameParameters = GameParameters {
    respawn: false,
    fast: false,
};

fn m6b_map(map: u8) -> doom_map::Map {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../tests/reference/m6b_wads/m6b.wad");
    let bytes = std::fs::read(path).expect("wad");
    let wad = doom_wad::Wad::parse(&bytes, doom_wad::Limits::default()).expect("wad parse");
    doom_map::Map::from_wad(&wad, &format!("E1M{map}"), doom_map::MapLimits::default())
        .expect("map")
}

/// `level` at a load `gametic`.
fn level_at(map: u8, skill: Skill, parameters: GameParameters, gametic: u64) -> Simulation {
    Simulation::original_player_episode1_v7_level_at(
        m6b_map(map),
        map,
        skill,
        parameters,
        MapContextOptions::default(),
        LevelStart::NewGame,
        gametic,
    )
    .expect("the map loads")
}

fn idle(s: &mut Simulation, tics: usize) {
    for _ in 0..tics {
        s.advance([TicCommand::default(); 4]).expect("an idle tic");
    }
}

/// The DSIM framing of `fields` under `version`.
fn encode(version: u32, fields: &[(String, Vec<u8>)]) -> Vec<u8> {
    let mut out = b"DSIM".to_vec();
    out.extend(version.to_le_bytes());
    out.extend((fields.len() as u64).to_le_bytes());
    for (path, value) in fields {
        out.extend((path.len() as u32).to_le_bytes());
        out.extend(path.as_bytes());
        out.extend((value.len() as u64).to_le_bytes());
        out.extend(value);
    }
    out
}

fn fields(s: &Snapshot) -> Vec<(String, Vec<u8>)> {
    s.fields()
        .map(|f| (f.path().to_owned(), f.value().to_vec()))
        .collect()
}

/// `fields` with `path` set to `value` (`None` removes it).
fn with(fields: &[(String, Vec<u8>)], path: &str, value: Option<&[u8]>) -> Vec<(String, Vec<u8>)> {
    assert!(fields.iter().any(|(p, _)| p == path), "{path}");
    fields
        .iter()
        .filter_map(|(p, v)| match (p == path, value) {
            (false, _) => Some((p.clone(), v.clone())),
            (true, Some(value)) => Some((p.clone(), value.to_vec())),
            (true, None) => None,
        })
        .collect()
}

fn read45(fields: &[(String, Vec<u8>)]) -> Result<u32, DiagnosticError> {
    Diagnostic::decode_episode1_v7(&encode(45, fields), DiagnosticLimits::default())
        .map(|d| d.version())
}

/// DSIM45 is DSIM44 field for field under policy 29 and the wire-29 context, plus
/// `actors.parameters` right after `actors.options` and `level.gametic_lead` right
/// after `level.start.gametic`: a wire-28 and a wire-29 level of the same map,
/// skill and commands differ in exactly those four fields at every capture.
#[test]
fn dsim45_is_dsim44_plus_two_fields_under_policy_29() {
    let map = 3;
    let mut old = Simulation::original_player_episode1_v6_level_at(
        m6b_map(map),
        map,
        Skill::Hard,
        MapContextOptions::default(),
        LevelStart::NewGame,
        7,
    )
    .expect("wire 28 loads");
    let mut new = level_at(map, Skill::Hard, NONE, 7);
    for tic in 0..40 {
        let (a, b) = (old.snapshot(), new.snapshot());
        assert_eq!((a.version(), b.version()), (44, 45));
        let (a, b) = (fields(&a), fields(&b));
        let at = |p: &str| b.iter().position(|(q, _)| q == p).unwrap();
        assert_eq!(at("actors.parameters"), at("actors.options") + 1);
        assert_eq!(at("level.gametic_lead"), at("level.start.gametic") + 1);
        assert_eq!(b[at("actors.parameters")].1, [0, 0]);
        assert_eq!(b[at("level.gametic_lead")].1, 7_u64.to_le_bytes());
        let rest: Vec<_> = b
            .iter()
            .filter(|(p, _)| p != "actors.parameters" && p != "level.gametic_lead")
            .collect();
        assert_eq!(rest.len(), a.len());
        for ((pa, va), (pb, vb)) in a.iter().zip(rest) {
            assert_eq!(pa, pb);
            match pa.as_str() {
                "profile" => assert_eq!(
                    (&va[..], &vb[..]),
                    (&28_u32.to_le_bytes()[..], &29_u32.to_le_bytes()[..])
                ),
                "context.schema" => {
                    assert_eq!(
                        (&va[..], &vb[..]),
                        (
                            PLAYER_EPISODE1_V6_CONTEXT_SCHEMA,
                            PLAYER_EPISODE1_V7_CONTEXT_SCHEMA
                        )
                    )
                }
                _ => assert_eq!(va, vb, "{pa} at tic {tic}"),
            }
        }
        idle(&mut old, 1);
        idle(&mut new, 1);
    }
    assert_eq!((new.gametic_lead(), new.gametic()), (Some(7), 47));
}

/// The DSIM45 reader reads every capture of a wire-29 run back field for field;
/// every earlier reader refuses version 45, and it refuses version 44.
#[test]
fn dsim45_reader_round_trip_and_version_refusals() {
    let limits = DiagnosticLimits::default();
    let mut s = level_at(2, Skill::Nightmare, NONE, 0);
    for _ in 0..21 {
        let snap = s.snapshot();
        let bytes = snap.canonical_bytes();
        let d = Diagnostic::decode_episode1_v7(&bytes, limits).expect("DSIM45");
        assert_eq!(d.version(), 45);
        for f in snap.fields() {
            assert_eq!(d.field(f.path()), Some(f.value()), "{}", f.path());
        }
        for old in [
            Diagnostic::decode_episode1_v6,
            Diagnostic::decode_episode1_v5,
            Diagnostic::decode_episode1_v4,
        ] {
            assert_eq!(
                old(&bytes, limits).err(),
                Some(DiagnosticError::Version(45))
            );
        }
        idle(&mut s, 1);
    }
    let old = Simulation::original_player_episode1_v6_level(
        m6b_map(2),
        2,
        Skill::Hard,
        MapContextOptions::default(),
        LevelStart::NewGame,
    )
    .expect("wire 28 loads")
    .snapshot()
    .canonical_bytes();
    assert_eq!(
        Diagnostic::decode_episode1_v7(&old, limits).err(),
        Some(DiagnosticError::Version(44))
    );
}

/// Finding R4: a kill credit above the map total is reachable only when monsters
/// respawn, skill 4 or the respawn parameter (g_game.c:1416-1419; the total counts
/// placed monsters only, p_mobj.c:789-790), and the DSIM45 reader admits it only
/// then.
#[test]
fn dsim45_kills_pass_the_total_only_with_respawning() {
    let two = 2_i32.to_le_bytes();
    for (skill, respawn, fast, ok) in [
        (Skill::Nightmare, false, false, true),
        (Skill::Hard, true, false, true),
        (Skill::Hard, true, true, true),
        (Skill::Hard, false, false, false),
        (Skill::Hard, false, true, false),
        (Skill::Medium, false, true, false),
    ] {
        let f = fields(&level_at(2, skill, GameParameters { respawn, fast }, 0).snapshot());
        assert_eq!(read45(&f), Ok(45), "{skill:?} {respawn} {fast}, no credit");
        let got = read45(&with(&f, "level.single_player_kill_count", Some(&two)));
        assert_eq!(
            got.is_ok(),
            ok,
            "{skill:?} {respawn} {fast}, credit 2: {got:?}"
        );
    }
}

/// The DSIM45 rules beyond DSIM44's: the parameters' bytes, the gametic lead's
/// range, skill 4 (refused by DSIM44), kills past the total (refused by DSIM44)
/// and the durations of the thirteen fast-table states, halved iff skill 4 or
/// `fastparm`.
#[test]
fn dsim45_reader_rules() {
    let f = fields(&level_at(2, Skill::Nightmare, NONE, 100).snapshot());
    assert_eq!(read45(&f), Ok(45));
    for bad in [[2, 0], [0, 2]] {
        assert_eq!(
            read45(&with(&f, "actors.parameters", Some(&bad))),
            Err(DiagnosticError::Structure)
        );
    }
    assert_eq!(
        read45(&with(&f, "actors.parameters", Some(&[1]))),
        Err(DiagnosticError::Structure)
    );
    assert_eq!(
        read45(&with(&f, "actors.parameters", None)),
        Err(DiagnosticError::Structure)
    );
    assert_eq!(
        read45(&with(&f, "actors.parameters", Some(&[1, 1]))),
        Ok(45)
    );
    for (lead, ok) in [
        (99_u64, false),
        (100, true),
        (5000, true),
        (i32::MAX as u64, true),
        (1 << 31, false),
    ] {
        let got = read45(&with(&f, "level.gametic_lead", Some(&lead.to_le_bytes())));
        assert_eq!(got.is_ok(), ok, "lead {lead}: {got:?}");
    }
    assert_eq!(
        read45(&with(&f, "level.gametic_lead", None)),
        Err(DiagnosticError::Structure)
    );
    assert_eq!(
        read45(&with(&f, "actors.options", Some(&[5, 0, 0]))),
        Err(DiagnosticError::Identity)
    );
    // The same skill-4 capture as DSIM44 (version, profile, context, no new fields).
    let as44: Vec<_> = f
        .iter()
        .filter(|(p, _)| p != "actors.parameters" && p != "level.gametic_lead")
        .map(|(p, v)| match p.as_str() {
            "profile" => (p.clone(), 28_u32.to_le_bytes().to_vec()),
            "context.schema" => (p.clone(), PLAYER_EPISODE1_V6_CONTEXT_SCHEMA.to_vec()),
            _ => (p.clone(), v.clone()),
        })
        .collect();
    let read44 = |f: &[(String, Vec<u8>)]| {
        Diagnostic::decode_episode1_v6(&encode(44, f), DiagnosticLimits::default())
            .map(|d| d.version())
    };
    assert_eq!(read44(&as44), Err(DiagnosticError::Identity));
    assert_eq!(
        read44(&with(&as44, "actors.options", Some(&[3, 0, 0]))),
        Ok(44)
    );
    // One placed monster: a credit of 2 passes the total only in DSIM45.
    let two = 2_i32.to_le_bytes();
    assert_eq!(
        read45(&with(&f, "level.single_player_kill_count", Some(&two))),
        Ok(45)
    );
    let hard44 = with(&as44, "actors.options", Some(&[3, 0, 0]));
    assert_eq!(
        read44(&with(&hard44, "level.single_player_kill_count", Some(&two))),
        Err(DiagnosticError::Identity)
    );
    assert_eq!(
        read45(&with(
            &f,
            "level.single_player_kill_count",
            Some(&(-1_i32).to_le_bytes())
        )),
        Err(DiagnosticError::Identity)
    );

    // A Demon (E1M4, skill 3) set into S_SARG_RUN1 (2 tics) and S_SARG_ATK1 (8).
    let f = fields(&level_at(4, Skill::Hard, NONE, 0).snapshot());
    let demon = (0..)
        .map(|k| format!("actor.{k}"))
        .find(|p| {
            f.iter().any(|(q, v)| {
                *q == format!("{p}.type")
                    && v[..] == OriginalActorType::MT_SERGEANT.ordinal().to_le_bytes()
            })
        })
        .unwrap();
    for (state, slow) in [
        (OriginalState::S_SARG_RUN1, 2),
        (OriginalState::S_SARG_ATK1, 8),
    ] {
        let set = |tics: i32, parameters: [u8; 2], skill: u8| {
            let g = with(
                &f,
                &format!("{demon}.state"),
                Some(&state.ordinal().to_le_bytes()),
            );
            let g = with(&g, &format!("{demon}.tics"), Some(&tics.to_le_bytes()));
            let g = with(&g, "actors.parameters", Some(&parameters));
            read45(&with(&g, "actors.options", Some(&[skill, 0, 0])))
        };
        assert_eq!(set(slow, [0, 0], 3), Ok(45), "{state:?}");
        assert_eq!(
            set(slow + 1, [0, 0], 3),
            Err(DiagnosticError::Identity),
            "{state:?}"
        );
        assert_eq!(
            set(0, [0, 0], 3),
            Err(DiagnosticError::Identity),
            "{state:?}"
        );
        assert_eq!(set(slow, [1, 0], 3), Ok(45), "{state:?} respawn");
        for fast in [([0, 1], 3), ([0, 0], 4), ([1, 1], 4)] {
            assert_eq!(set(slow >> 1, fast.0, fast.1), Ok(45), "{state:?} {fast:?}");
            assert_eq!(
                set(slow, fast.0, fast.1),
                Err(DiagnosticError::Identity),
                "{state:?} {fast:?}"
            );
        }
    }
}

/// The spawn witnesses of items (E1M1) and decorations (E1M6) expect the reaction
/// time `P_SpawnMobj` gave (p_mobj.c:503-504): 0 under wire 29 at skill 4, the
/// type's (8) at skill 3. The other value refuses the next tic, state kept.
#[test]
fn spawn_witnesses_expect_the_skills_reaction_time() {
    for (map, item) in [(1, true), (6, false)] {
        for (skill, spawned, other) in [(Skill::Nightmare, 0, 8), (Skill::Hard, 8, 0)] {
            let mut s = level_at(map, skill, NONE, 0);
            let policy = s.player_policy();
            let id = s
                .actors
                .order()
                .find(|&id| {
                    s.actor(id).and_then(|a| a.life()).is_some_and(|l| {
                        if item {
                            world_pickups::kind_for(policy, l.actor_type).is_some()
                        } else {
                            e1m1_rules::is_decoration(policy, l.actor_type)
                        }
                    })
                })
                .expect("an item or a decoration");
            let reaction = |s: &Simulation| s.actor(id).unwrap().life().unwrap().reaction_time;
            assert_eq!(reaction(&s), spawned, "E1M{map} {skill:?}");
            let mut bad = s.clone();
            bad.actors
                .get_mut(id)
                .unwrap()
                .life
                .as_mut()
                .unwrap()
                .reaction_time = other;
            let kept = bad.snapshot().canonical_bytes();
            assert_eq!(
                bad.advance([TicCommand::default(); 4]),
                Err(PlayerBodyError::Invariant.into()),
                "E1M{map} {skill:?}"
            );
            assert_eq!(bad.snapshot().canonical_bytes(), kept);
            idle(&mut s, 1);
            assert_eq!(reaction(&s), spawned);
        }
    }
}

/// `fastparm` alone changes neither `P_GiveAmmo` (p_inter.c:95-101 names the
/// skills) nor the spawn reaction time (p_mobj.c:503-504): AMMO4's commands on
/// skill 3 with and without it (a map without a monster or a missile, where the
/// fast table has nothing to act on) give captures that differ only in
/// `actors.parameters`, at every tic of the corridor's pickups.
/// The pause's simulation part (rulings N5 (a), N6 (a)). Under wire 29 a level
/// tic admits every byte with `BT_SPECIAL` but the save command and keeps a live
/// player's zeroed (p_user.c:280-281); bit 6 alone stays refused; wire 28 refuses
/// every special byte and has no paused tic. A paused tic changes only the kept
/// command, the events, `level.gametic_lead` (one more) and, on a turbo tic
/// (`gametic` 128 with `forwardmove` 60, g_game.c:672-679), the message; each
/// refusal keeps the state.
#[test]
fn the_pause_commands_and_the_paused_tic() {
    let cmd = |buttons: u8, forward: i8| TicCommand {
        forward,
        buttons,
        ..TicCommand::default()
    };
    let one = |c| {
        [
            c,
            TicCommand::default(),
            TicCommand::default(),
            TicCommand::default(),
        ]
    };
    let mut s = level_at(2, Skill::Hard, NONE, 128);
    for b in [0x82, 0xc2, 0x40] {
        let before = s.snapshot().canonical_bytes();
        assert_eq!(s.advance(one(cmd(b, 0))), Err(SimError::UnsupportedButtons));
        if b & 0x80 != 0 {
            assert_eq!(
                s.paused_tic(one(cmd(b, 0))),
                Err(SimError::UnsupportedButtons)
            );
        }
        assert_eq!(s.snapshot().canonical_bytes(), before, "{b:#x}");
    }
    let before = fields(&s.snapshot());
    s.paused_tic(one(cmd(0x81, 60))).expect("a paused tic");
    let after = fields(&s.snapshot());
    let changed: Vec<&str> = before
        .iter()
        .zip(&after)
        .filter(|(a, b)| a != b)
        .map(|(a, _)| a.0.as_str())
        .filter(|p| !p.starts_with("events."))
        .collect();
    assert_eq!(
        changed,
        [
            "player.0.forward",
            "player.0.buttons",
            "original_player.0.pickups.message",
            "level.gametic_lead"
        ]
    );
    assert_eq!(
        (s.tic(), s.gametic_lead(), s.gametic()),
        (0, Some(129), 129)
    );
    for b in [0x81, 0x83, 0x85, 0xfd, 0x80] {
        s.advance(one(cmd(b, 25)))
            .expect("a special byte on a level tic");
        let kept = fields(&s.snapshot());
        let buttons = kept.iter().find(|f| f.0 == "player.0.buttons");
        assert_eq!(buttons.map(|f| f.1.clone()), Some(vec![0]), "{b:#x}");
    }
    let mut old = Simulation::original_player_episode1_v6_level_at(
        m6b_map(2),
        2,
        Skill::Hard,
        MapContextOptions::default(),
        LevelStart::NewGame,
        0,
    )
    .expect("wire 28");
    assert_eq!(
        old.advance(one(cmd(0x81, 0))),
        Err(SimError::UnsupportedButtons)
    );
    assert_eq!(
        old.paused_tic(one(cmd(0x81, 0))),
        Err(PlayerBodyError::Profile.into())
    );
}

/// Pins the bound of `escaped_missile` and the two admissions that use it (the doc of
/// `escaped_missile`: each coordinate within `32,767 - 128` units less the sight margin
/// capped at 16,384; the height within the sight margin alone; only a missile type, only
/// under wire 29). Below the public API: the admission is a `pub(crate)` preflight, and no
/// committed genuine item puts a missile at the bound, only far inside it (FASTOUT).
#[test]
fn an_escaped_missile_is_admitted_to_exactly_its_documented_bound() {
    let s = level_at(2, Skill::Hard, NONE, 0);
    let first = s.actor_order().next().expect("an actor");
    let base = *s.actor(first).expect("actor");
    let margin = s.sight_margin();
    let bound = 32_767 - 128 - margin.min(16_384);
    let at = |ty: OriginalActorType, x: u32, y: u32, z: u32| {
        let mut a = base;
        let units = |u: u32| Fixed::from_map_units(u as i16);
        a.spec.position = [units(x), units(y)];
        a.z = units(z);
        a.life.as_mut().expect("typed").actor_type = ActorTypeId(ty.ordinal());
        a
    };
    let shot = OriginalActorType::MT_TROOPSHOT;
    let imp = OriginalActorType::MT_TROOP;
    assert!(
        bound > margin,
        "the cases below lie outside the whole bound"
    );
    assert!(s.escaped_missile(&at(shot, bound, 0, 0)));
    assert!(s.escaped_missile(&at(shot, 0, bound, 0)));
    assert!(!s.escaped_missile(&at(shot, bound + 1, 0, 0)));
    assert!(!s.escaped_missile(&at(shot, 0, bound + 1, 0)));
    assert!(!s.escaped_missile(&at(imp, bound, 0, 0)));
    assert_eq!(s.actor_bounds_admitted(&at(shot, bound, 0, 0)), Ok(()));
    assert_eq!(s.actor_bounds_admitted(&at(shot, bound, 0, margin)), Ok(()));
    assert_eq!(
        s.actor_bounds_admitted(&at(shot, bound, 0, margin + 1)),
        Err(PerceptionError::Arithmetic.into())
    );
    assert!(s.actor_bounds_admitted(&at(shot, bound + 1, 0, 0)).is_err());
    assert!(s.actor_bounds_admitted(&at(imp, bound, 0, 0)).is_err());
    let old = Simulation::original_player_episode1_v6_level_at(
        m6b_map(2),
        2,
        Skill::Hard,
        MapContextOptions::default(),
        LevelStart::NewGame,
        0,
    )
    .expect("wire 28");
    assert!(!old.escaped_missile(&at(shot, bound, 0, 0)));
}

/// Pins `missile_speed` (g_game.c:1425-1427, the rule in its doc): under the fast table
/// (fastparm, or Nightmare) exactly `MT_BRUISERSHOT`, `MT_HEADSHOT` and `MT_TROOPSHOT`
/// move 20 units a tic and every other type keeps its speed; with no fast table none changes.
/// Below the public API: the function is `pub(crate)`, and no committed item flies a
/// fast fireball of every other missile type.
#[test]
fn only_the_three_fireballs_take_the_fast_speed() {
    let speed = 7 << 16;
    let fast = level_at(
        2,
        Skill::Hard,
        GameParameters {
            respawn: false,
            fast: true,
        },
        0,
    );
    let slow = level_at(2, Skill::Hard, NONE, 0);
    let nightmare = level_at(2, Skill::Nightmare, NONE, 0);
    for ty in [
        OriginalActorType::MT_BRUISERSHOT,
        OriginalActorType::MT_HEADSHOT,
        OriginalActorType::MT_TROOPSHOT,
        OriginalActorType::MT_ROCKET,
        OriginalActorType::MT_PLASMA,
        OriginalActorType::MT_TROOP,
    ] {
        let id = ActorTypeId(ty.ordinal());
        let three = !matches!(
            ty,
            OriginalActorType::MT_ROCKET
                | OriginalActorType::MT_PLASMA
                | OriginalActorType::MT_TROOP
        );
        let want = if three { 20 << 16 } else { speed };
        let of = |s: &Simulation| {
            crate::nightmare::missile_speed(&s.world, s.actor_options.skill, id, speed)
        };
        assert_eq!(of(&fast), want, "{ty:?} fast");
        assert_eq!(of(&nightmare), want, "{ty:?} nightmare");
        assert_eq!(of(&slow), speed, "{ty:?} slow");
    }
}

/// Pins the roster bound of `preflight_map_demons` under wire 29: the placed monsters
/// (the map's own `K`, `Episode1Bounds::monsters`; a respawned monster replaces its corpse,
/// so the bound is the count of placed ones) are admitted at `K` and refused with
/// `MapSpawnError::Ownership` above it. Below the public API: the bound is a map constant
/// that no loadable map exceeds, so the test lowers it in the world.
#[test]
fn the_roster_of_placed_monsters_is_bounded_by_the_maps_count() {
    let mut s = level_at(2, Skill::Hard, NONE, 0);
    let k = s.world.episode1.expect("bounds").monsters;
    assert!(k >= 1, "the map places monsters");
    assert_eq!(s.preflight_map_demons(), Ok(()));
    s.world.episode1.as_mut().expect("bounds").monsters = k - 1;
    assert_eq!(
        s.preflight_map_demons(),
        Err(SimError::MapSpawn(MapSpawnError::Ownership))
    );
}

/// A Nightmare level at tic 0 whose first `MF_COUNTKILL` actor is made a corpse (`tics`
/// -1, as after its death state) with `movecount` and the spawn angle `angle`, gameplay
/// RNG index `rng`; returns it after one tic, with the corpse's id.
fn corpse_tic(movecount: i32, angle: i16, rng: u8) -> (Simulation, ActorId) {
    let mut s = level_at(2, Skill::Nightmare, NONE, 0);
    let id = s
        .actor_order()
        .find(|i| {
            let l = s.actor(*i).and_then(|a| a.life);
            l.is_some_and(|l| l.flags & crate::world_pickups::MF_COUNTKILL != 0)
        })
        .expect("a monster");
    let life = s
        .actors
        .get_mut(id)
        .and_then(|a| a.life.as_mut())
        .expect("typed");
    life.tics = -1;
    life.movecount = movecount;
    life.spawnpoint.as_mut().expect("placed").angle = angle;
    s.rng = DoomRng::from_indices(rng, 0);
    idle(&mut s, 1);
    (s, id)
}

/// Pins the 12-second wait of `corpse_think` (p_mobj.c:459, the rule in its doc): a
/// corpse draws its gate on the tic its `movecount` reaches 12 * 35 = 420 and not before.
/// Seen from outside as the gameplay RNG: a tic with the draw and one without end at
/// different indexes. Below the public API: `corpse_think` is `pub(crate)` and a run to
/// the exact tic would take 420 tics of chase the genuine items do not stop at.
#[test]
fn a_corpse_draws_its_gate_from_the_tic_its_count_reaches_420() {
    let index = |movecount| corpse_tic(movecount, 0, 0).0.rng().indices()[0];
    assert_eq!(index(417), index(418), "counts 418 and 419 draw nothing");
    assert_ne!(index(419), index(418), "count 420 draws the gate");
}

/// Pins the angle of a respawned monster, `ANG45 * (mthing->angle / 45)` (p_mobj.c:400,
/// the comment in `respawn`): spawn angle 100 gives 2 * ANG45, whatever the gate's RNG
/// start, found by trying every index until a gate of 4 or less respawns the corpse (three spawns
/// join the order at once; the corpse leaves it with the removals after the tic).
#[test]
fn a_respawned_monster_faces_ang45_times_the_spawn_angle_over_45() {
    let before = level_at(2, Skill::Nightmare, NONE, 0).actor_order().count();
    for rng in 0..=255u8 {
        let (s, _) = corpse_tic(419, 100, rng);
        if s.actor_order().count() != before + 3 {
            continue;
        }
        let new = s.actor_order().last().expect("the respawned monster");
        assert_eq!(s.actor(new).expect("actor").spec.angle, 2 * 0x2000_0000);
        return;
    }
    panic!("no gate index respawned the corpse");
}

/// Pins `validate_decoration_at`'s per-field refusals (the doc of `validate_decoration`: a
/// decoration holds its spawn record forever): a wrong `tics` alone, or a wrong `health`
/// alone, is refused, though the other holds. Below the public API: the witness is
/// `pub(crate)` and a spawned decoration is never wrong in one field.
#[test]
fn a_decoration_with_one_wrong_field_is_refused() {
    let mut lumps = crate::player_movers_tests::room(0);
    lumps.add_thing([-32, 0, 0, 1, 7]);
    lumps.add_thing([200, 0, 0, 34, 7]);
    let options = MapContextOptions {
        initial_rng: DoomRng::from_indices(6, 0),
        respawn_monsters: false,
    };
    let mut s = Simulation::original_player_episode1_map(lumps.map(), options).expect("loads");
    s.spawn_map_things().expect("spawns");
    let decoration = s
        .actor_order()
        .filter_map(|i| s.actor(i))
        .find_map(|a| {
            let l = a.life()?;
            (l.actor_type.0 == OriginalActorType::MT_MISC49.ordinal()).then_some(*a)
        })
        .expect("the candle");
    let check = |a| crate::e1m1_rules::validate_decoration_at(None, a, false);
    assert_eq!(check(decoration), Ok(()));
    let mut tics = decoration;
    tics.life.as_mut().expect("typed").tics = 3;
    let mut health = decoration;
    health.life.as_mut().expect("typed").health += 1;
    for a in [tics, health] {
        assert_eq!(check(a), Err(PlayerBodyError::Invariant.into()));
    }
}

/// Pins the extent of the unfit-monster rule of `spawn_map_things` under wire 29
/// (p_mobj.c:515-521: `P_SpawnMobj` makes no fit test, the shootable case of the movers
/// policy's witness): only a `MF_COUNTKILL` thing is spawned in a sector (the room's second) whose
/// floor is at its ceiling; a candle there is refused by the spawn fit test as under every other
/// wire. Below the public API: the one-sector edit of a synthetic room is the whole setup.
#[test]
fn only_a_monster_may_spawn_in_a_closed_sector_under_wire_29() {
    let load = |kind: i16| {
        let mut lumps = crate::player_movers_tests::room(0);
        let sectors = &mut lumps
            .lumps
            .iter_mut()
            .find(|(n, _)| n == "SECTORS")
            .unwrap()
            .1;
        sectors[26..30].copy_from_slice(&[0, 0, 0, 0]);
        lumps.add_thing([-32, 0, 0, 1, 7]);
        lumps.add_thing([200, 0, 0, kind, 7]);
        Simulation::original_player_episode1_v7_level_at(
            lumps.map(),
            1,
            Skill::Medium,
            NONE,
            MapContextOptions::default(),
            LevelStart::NewGame,
            0,
        )
    };
    assert!(load(3001).is_ok(), "the imp spawns on the floor, unfit");
    let refused = load(34).err().expect("the candle is refused");
    assert!(format!("{refused:?}").contains("Fit"), "{refused:?}");
}

/// Pins the slide-only extent of `wire29_intercept` (ruling N9 (a), the doc of that function):
/// a `P_InterceptVector` whose `FixedDiv2` has an exact den and a wrong num, which wire 27
/// refuses for every caller, is taken (the genuine engine's value) for the slide trace alone
/// and under wire 29 alone. The vectors are found by a fixed search over the `int` operands
/// until wire 27 refuses that class for the slide trace. Below the public API: the function
/// is `pub(crate)`, reached by the walk's intercepts, and the one genuine item (WRAP) is a slide.
#[test]
fn the_wrapped_num_class_is_taken_for_the_slide_trace_alone() {
    use crate::intercept_vector::{
        InterceptCaller as C, Operand, Wire27Refusal, WrapClass, policy_intercept, wire27_intercept,
    };
    let want = Wire27Refusal::Unevidenced(WrapClass::Div2 {
        den: Operand::Exact,
        num: Operand::Wrong,
    });
    let mut x = 0x9e37_79b9_7f4a_7c15_u64;
    let mut next = || {
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        Fixed::from_bits((x >> 20) as i32)
    };
    let found = (0..4_000_000).find_map(|_| {
        let v = [
            next(),
            next(),
            next(),
            next(),
            next(),
            next(),
            next(),
            next(),
        ];
        let args = ([v[0], v[1]], [v[2], v[3]], [v[4], v[5]], [v[6], v[7]]);
        (wire27_intercept(C::Slide, args.0, args.1, args.2, args.3) == Err(want)).then_some(args)
    });
    let (a, b, c, d) = found.expect("a vector of the class");
    let wire29 = level_at(2, Skill::Hard, NONE, 0);
    let wire28 = Simulation::original_player_episode1_v6_level_at(
        m6b_map(2),
        2,
        Skill::Hard,
        MapContextOptions::default(),
        LevelStart::NewGame,
        0,
    )
    .expect("wire 28");
    for caller in [
        C::AimLine,
        C::AimThing,
        C::ShootLine,
        C::ShootThing,
        C::Slide,
        C::Use,
    ] {
        let refused = wire27_intercept(caller, a, b, c, d) == Err(want);
        let took = policy_intercept(&wire29.world, caller, a, b, c, d);
        assert_eq!(took.is_some(), !refused || caller == C::Slide, "{caller:?}");
        assert_eq!(
            policy_intercept(&wire28.world, caller, a, b, c, d).is_some(),
            !refused,
            "{caller:?} on wire 28"
        );
    }
    assert!(
        wire27_intercept(C::Use, a, b, c, d) == Err(want),
        "a refusing non-slide caller"
    );
}

/// Pins `freed_source`'s two arms through `DamagePlan::current_original_in` (the doc of
/// `freed_source`, p_inter.c:787-791 and 806-809): under wire 29 a damage source that no
/// longer resolves is refused with `FreedRead` for a victim that is alive (`health > 0`) and
/// shootable, and ignored for one that is not (health 0, or not shootable), where the C
/// returns before reading the source. Below the public API: the plan is `pub(crate)`, and
/// the genuine STALE items reach only the live victim.
#[test]
fn a_freed_damage_source_is_refused_only_for_a_live_shootable_victim() {
    let source = ActorId::from_parts(900, 7);
    let plan = |health: i32, shootable: bool| {
        let mut s = level_at(2, Skill::Hard, NONE, 0);
        let victim = s
            .actor_order()
            .find(|i| {
                let l = s.actor(*i).and_then(|a| a.life);
                l.is_some_and(|l| l.flags & crate::world_pickups::MF_COUNTKILL != 0)
            })
            .expect("a monster");
        let life = s
            .actors
            .get_mut(victim)
            .and_then(|a| a.life.as_mut())
            .expect("typed");
        life.health = health;
        let bit = crate::original_player::MF_SHOOTABLE;
        life.flags = (life.flags & !bit) | if shootable { bit } else { 0 };
        let request = DamageRequest {
            target: victim,
            inflictor: None,
            source: Some(source),
            amount: 1,
        };
        s.checked_demon_operation(|h| {
            crate::combat::DamagePlan::current_original(h, request).map(|_| ())
        })
        .and_then(|r| r)
    };
    assert_eq!(plan(5, true), Err(SimError::FreedRead));
    assert_eq!(plan(0, true), Ok(()));
    assert_eq!(plan(5, false), Ok(()));
}

/// Pins `toggles_pause` and `save_command` over all 256 button bytes, by the written rule
/// of their docs (g_game.c:698-716, d_event.h:78-92): `BT_SPECIAL` (0x80) set, and the low
/// two bits 1 (pause) or 2 (save game). Below the public API: the two predicates are
/// `pub` in `nightmare`, and the session tests pass only a few bytes through them.
#[test]
fn the_pause_and_save_predicates_over_every_button_byte() {
    for b in 0..=255u8 {
        let special = b >= 0x80;
        assert_eq!(
            crate::nightmare::toggles_pause(b),
            special && b % 4 == 1,
            "{b:#x}"
        );
        assert_eq!(
            crate::nightmare::save_command(b),
            special && b % 4 == 2,
            "{b:#x}"
        );
    }
}

#[test]
fn fastparm_alone_changes_no_ammunition_or_reaction_time() {
    let (map, commands) = crate::nightmare_genuine_tests::demo("AMMO4");
    let fast = GameParameters {
        respawn: false,
        fast: true,
    };
    let mut a = level_at(map, Skill::Hard, NONE, 0);
    let mut b = level_at(map, Skill::Hard, fast, 0);
    let none = TicCommand::default();
    for c in &commands {
        let (fa, fb) = (fields(&a.snapshot()), fields(&b.snapshot()));
        assert_eq!(
            with(&fb, "actors.parameters", Some(&[0, 0])),
            fa,
            "tic {}",
            a.tic()
        );
        let (ra, rb) = (
            a.advance([*c, none, none, none]),
            b.advance([*c, none, none, none]),
        );
        assert_eq!(ra, rb);
        if ra.is_err() {
            break;
        }
    }
    assert!(a.tic() > 300, "the corridor's pickups were played");
}

/// Skill 4 is admitted under wire 29 alone; wire 28 refuses it at the load as
/// before. Wire 29 takes the parameters at any skill and keeps them in the
/// capture; `with_original_registry` refuses wire 29 as it refuses wires 26 to
/// 28, and `MapContextOptions::respawn_monsters` stays refused under wire 29 (the
/// respawn parameter is `GameParameters::respawn`).
#[test]
fn skill_4_and_the_parameters_are_admitted_under_wire_29_alone() {
    assert!(level("BITS4", 2, Skill::Nightmare, NONE).is_ok());
    let wire28 = Simulation::original_player_episode1_v6_level(
        m6b_map(2),
        2,
        Skill::Nightmare,
        MapContextOptions::default(),
        LevelStart::NewGame,
    );
    assert_eq!(
        wire28.map(|_| ()),
        Err(LevelStartError::Registry(OriginalRegistryError::Runtime(
            PlayerBodyError::Unsupported.into()
        )))
    );
    for (skill, respawn, fast) in [
        (Skill::Baby, true, false),
        (Skill::Medium, false, true),
        (Skill::Nightmare, true, true),
    ] {
        let p = GameParameters { respawn, fast };
        let s = level_at(2, skill, p, 0);
        let snap = s.snapshot();
        let get = |path: &str| {
            snap.fields()
                .find(|f| f.path() == path)
                .unwrap()
                .value()
                .to_vec()
        };
        assert_eq!(get("actors.options"), [skill as u8, 0, 0]);
        assert_eq!(
            get("actors.parameters"),
            [u8::from(respawn), u8::from(fast)]
        );
    }
    let registry = OriginalExecutionRegistry::new(V7).expect("registry");
    assert_eq!(
        Simulation::with_original_registry(
            m6b_map(2),
            player_map_scale::actor_slots(V7),
            registry,
            ActorOptions::default(),
            MapContextOptions::default(),
        )
        .map(|_| ()),
        Err(PlayerBodyError::Unsupported.into())
    );
    let respawning = Simulation::original_player_episode1_v7_level_at(
        m6b_map(2),
        2,
        Skill::Medium,
        NONE,
        MapContextOptions {
            respawn_monsters: true,
            ..MapContextOptions::default()
        },
        LevelStart::NewGame,
        0,
    );
    assert_eq!(
        respawning.map(|_| ()),
        Err(LevelStartError::Registry(OriginalRegistryError::Runtime(
            MapSpawnError::Respawn.into()
        )))
    );
    assert!(!V6.has_nightmare() && V7.has_nightmare() && V7.has_easy_skills());
    assert_eq!(
        (V7.wire_id(), V7.context_schema()),
        (29, PLAYER_EPISODE1_V7_CONTEXT_SCHEMA)
    );
}
