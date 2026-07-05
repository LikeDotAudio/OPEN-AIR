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
}
