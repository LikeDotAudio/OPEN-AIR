/**
 * Header: cli.rs
 * Purpose: cli.rs implementation.
 * Description: Logic and implementation for cli.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

use clap::Parser;

#[derive(Parser, Debug)]
#[command(author, version, about = "Launch the OPEN-AIR stack (Rust core + frontend).", long_about = None)]
pub struct Args {
    #[arg(long, default_value_t = 8000, help = "Frontend server port (default 8000).")]
    pub port: u16,

    #[arg(long, default_value_t = 8001, help = "Rust orchestrator port (default 8001).")]
    pub core_port: u16,

    /// SECURITY: loopback by default.
    ///
    /// The HTTP server exposes `POST /api/save`, which writes files, and there is
    /// no authentication in front of it. Binding all interfaces therefore hands
    /// every host on the network a write primitive. Widening this is a deliberate
    /// act with a prerequisite: put authentication on the mutating routes first.
    /// Same opt-in discipline as `broker/mosquitto.conf`.
    #[arg(
        long,
        default_value = "127.0.0.1",
        help = "Address to bind the frontend server to (default 127.0.0.1, loopback only). \
                Use 0.0.0.0 to expose on the network — only with auth in front of /api/save."
    )]
    pub bind: std::net::IpAddr,

    /// SECURITY: loopback by default — see `--bind`.
    #[arg(
        long,
        default_value = "127.0.0.1",
        help = "Address the OSC agent listens on (default 127.0.0.1, loopback only)."
    )]
    pub osc_bind: std::net::IpAddr,

    /// Broker hostname. Was hard-coded to "127.0.0.1" in six places, which meant
    /// the orchestrator could only ever run on the same host as the broker —
    /// including inside a container, where `broker` is a different host.
    #[arg(
        long,
        env = "MQTT_HOST",
        default_value = "127.0.0.1",
        help = "MQTT broker hostname (env: MQTT_HOST)."
    )]
    pub mqtt_host: String,

    #[arg(long, env = "MQTT_PORT", default_value_t = 1883, help = "MQTT broker port (env: MQTT_PORT).")]
    pub mqtt_port: u16,

    #[arg(long, help = "Skip cargo builds.")]
    pub no_build: bool,

    #[arg(long, help = "Build Rust in release mode.")]
    pub release: bool,

    #[arg(long, help = "Do not launch the Rust orchestrator binary.")]
    pub no_orchestrator: bool,

    #[arg(long, help = "Skip all Rust (core import + orchestrator).")]
    pub no_rust: bool,

    #[arg(long, help = "Do not open the browser.")]
    pub no_browser: bool,

    #[arg(long, help = "Do not publish protocol config.ini files to MQTT on startup.")]
    pub no_mqtt: bool,

    /// Regenerate `FrontEnd/api/tree.json` and `FrontEnd/api/grabbag`, then exit.
    ///
    /// These are the static fallbacks `index.html` uses when the orchestrator is
    /// not answering. They are committed files (tree.json is ~2.5 MB), so they
    /// are refreshed on request rather than on every scan — regenerating them
    /// automatically would leave the working tree permanently dirty.
    #[arg(long, help = "Rewrite the static FrontEnd/api snapshots and exit.")]
    pub write_api_snapshot: bool,
}
