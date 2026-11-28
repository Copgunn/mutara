//! Mutation-survivor tests for `app/mod.rs` under the wire 29 configuration (`GameData::load_wire29_session`),
//! through the public API. Expected values are the wire 29 record's (docs/validation/WIRE29.md): the
//! Pause key sends the original's pause command (g_game.c:561-565, built at g_game.c:426-430), recorded
//! as command byte 0x81 (`BT_SPECIAL | BTS_PAUSE`) of a v4 demo whose header holds `respawnparm` and
//! `fastparm` (g_game.c:1556, 1560-1561: version 110, skill, episode, map, the parameters). doom-play
//! has the same checks at its level; these pin doom-game's own `GameData`/`App` code.
//!
//! Not pinned: `GameData::recorder`'s `&&` (581:42) is equivalent. `||` differs only for a session
//! whose configuration is not wire 28, where it picks `new_v3` over `new`; the two writers differ
//! only for skills 0 and 1, which every non-wire-28 session refuses at load.

use doom_game::app::Timestamp;
use doom_game::app::{App, GameData, GameParameters, Host, Mode, PAUSE_COMMAND, SessionConfig};
use doom_game::input::Preset;
use doom_game::input::keys::{KEY_ESCAPE, KEY_PAUSE, KEY_UPARROW};
use doom_game::session::ModeSetting;
use doom_game::session::demo::SessionDemo;
use std::path::Path;

const BOTH: GameParameters = GameParameters {
    respawn: true,
    fast: true,
};

#[derive(Default)]
struct FileHost {
    saved: Vec<(String, Vec<u8>)>,
}

impl Host for FileHost {
    fn timestamp(&mut self) -> Timestamp {
        Timestamp::default()
    }
    fn exists(&mut self, _: &str) -> bool {
        false
    }
    fn save(&mut self, name: &str, bytes: &[u8]) -> Result<(), String> {
        self.saved.push((name.to_owned(), bytes.to_vec()));
        Ok(())
    }
}

/// The synthetic episode with M6b's `M_PAUSE`, skill 4, both parameters.
fn data() -> GameData {
    let dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../tests/reference");
    let files: Vec<Vec<u8>> = [
        "m6a_wads/episode.wad",
        "m5b_gfx.wad",
        "m5c_sfx.wad",
        "m6a_wads/m6a_gfx.wad",
        "m6a_wads/m6a_music.wad",
        "m6b_wads/m6b_gfx.wad",
    ]
    .iter()
    .map(|w| std::fs::read(dir.join(w)).expect("WAD"))
    .collect();
    let refs: Vec<&[u8]> = files.iter().map(Vec::as_slice).collect();
    GameData::load_wire29_session(&refs, ModeSetting::Probe, 1, 4, BOTH).expect("skill 4")
}

/// Runs slots (35 a second) until the session has run `tics` tics.
fn run_to(app: &mut App, host: &mut FileHost, k: &mut u64, tics: u64) {
    while app.tic() < tics && app.mode() == &Mode::Playing {
        *k += 1;
        assert!(*k < 10_000, "{tics} tics not reached");
        app.update((*k * 1_000_000).div_ceil(35), host);
    }
}

/// Pins `GameData::parameters` (595:9), `GameData::original_pause` (590:9) through the demo
/// header (581:22: a v4 writer, not the earlier ones), and `App::preset` (1280:9).
#[test]
fn the_wire_29_data_and_app_report_their_parameters_preset_and_demo_header() {
    let data = data();
    assert_eq!(data.parameters(), BOTH);
    let cfg = SessionConfig {
        preset: Preset::Modern,
        ..SessionConfig::default()
    };
    let mut host = FileHost::default();
    let mut app = App::new(data, cfg, &mut host);
    assert_eq!(app.preset(), Preset::Modern);
    let mut k = 0;
    run_to(&mut app, &mut host, &mut k, 3);
    app.quit(&mut host);
    let (_, bytes) = host.saved.last().expect("a demo file").clone();
    assert_eq!(
        bytes[..7],
        [110, 4, 1, 1, 0, 1, 1],
        "version, skill, episode, map, parameters"
    );
    let (demo, parameters) = SessionDemo::parse_v4(&bytes).expect("the wire 29 reader");
    assert_eq!((demo.skill, parameters), (4, BOTH));
}

/// Pins `App::key` (1412:29, 1415:30) and `App::run_tic` (1536:22, 1537:17): the Pause key's
/// key-down sets `sendpause` and the next command has its buttons replaced by 0x81 with its
/// movement kept (g_game.c:426-430); Esc is not the original's pause (it stops the app, outside
/// the demo) and a key-up of Pause sends nothing.
#[test]
fn the_pause_key_records_command_0x81_with_its_movement_and_esc_does_not() {
    assert_eq!(PAUSE_COMMAND, 0x81);
    let mut host = FileHost::default();
    let mut app = App::new(data(), SessionConfig::default(), &mut host);
    let mut k = 0;
    app.key(KEY_UPARROW, true, &mut host);
    run_to(&mut app, &mut host, &mut k, 10);
    // Esc: the app's own pause, nothing recorded as a pause command
    app.key(KEY_ESCAPE, true, &mut host);
    assert_eq!(app.mode(), &Mode::Paused);
    app.key(KEY_ESCAPE, true, &mut host);
    assert_eq!(app.mode(), &Mode::Playing);
    run_to(&mut app, &mut host, &mut k, 15);
    assert!(
        app.recorder()
            .commands()
            .iter()
            .all(|c| c.buttons != PAUSE_COMMAND)
    );
    assert!(!app.session().expect("session").paused());
    // Pause: key-up alone sends nothing; key-down does, for exactly one tic
    app.key(KEY_PAUSE, false, &mut host);
    run_to(&mut app, &mut host, &mut k, 17);
    assert!(!app.session().expect("session").paused());
    app.key(KEY_UPARROW, true, &mut host); // a stop releases the held keys
    let t0 = app.tic();
    app.key(KEY_PAUSE, true, &mut host);
    assert_eq!(
        app.mode(),
        &Mode::Playing,
        "the original's pause is not the app's"
    );
    run_to(&mut app, &mut host, &mut k, t0 + 1);
    let c = app.recorder().commands()[t0 as usize];
    assert_eq!(
        (c.buttons, c.forward),
        (0x81, 25),
        "buttons replaced, movement kept"
    );
    run_to(&mut app, &mut host, &mut k, t0 + 5);
    let pauses = (app.recorder().commands().iter()).filter(|c| c.buttons == PAUSE_COMMAND);
    assert_eq!(pauses.count(), 1);
    assert!(app.session().expect("session").paused());
}
