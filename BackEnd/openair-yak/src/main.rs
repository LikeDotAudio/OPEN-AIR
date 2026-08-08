mod config;
mod mqtt;
mod verbs;
mod models;
mod converters;
mod repository;
mod readings;
mod tools;

use clap::{Parser, Subcommand};
use log::{info, error};
use std::sync::Arc;

/// The YAK agent, plus the build-time tooling over its command tables.
///
/// With no subcommand this starts the agent, which is what
/// `Deployment/openair.py` launches — so the tools could be added without
/// changing how anything runs it.
#[derive(Parser)]
#[command(name = "openair-yak", about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Option<Command>,
}

#[derive(Subcommand)]
enum Command {
    /// Check the command tables against their own invariants.
    CheckTables {
        /// Exit 1 on any finding.
        #[arg(long)]
        strict: bool,
        /// Write {model: command count} and exit.
        #[arg(long, value_name = "FILE")]
        snapshot: Option<String>,
        /// Fail if any model lost commands since that snapshot.
        #[arg(long, value_name = "FILE")]
        against: Option<String>,
    },
    /// Point each known device at its command table.
    BuildLinks {
        /// Report drift without writing; exit 1 if stale.
        #[arg(long)]
        check: bool,
    },
    /// Rewrite every commands_tree.md from its table.
    BuildTrees {
        /// Report drift without writing; exit 1 if stale.
        #[arg(long)]
        check: bool,
    },
    /// Rewrite Instruments/_yak/CommandList.csv and .xlsx from the tables.
    BuildList {
        /// Report drift without writing; exit 1 if stale.
        #[arg(long)]
        check: bool,
    },
    /// Cross-reference panel controls against the command vocabulary.
    Crossref {
        /// Instrument type (default: all).
        type_name: Option<String>,
        /// Full per-control tables.
        #[arg(long, short)]
        verbose: bool,
        /// Print yak_handler stubs.
        #[arg(long)]
        emit: bool,
    },
}

#[tokio::main]
async fn main() {
    // Initialize logging for anything we didn't manually port to println
    env_logger::init();

    // Tooling runs and exits; only the no-subcommand path starts the agent.
    if let Some(command) = Cli::parse().command {
        let code = match command {
            Command::CheckTables { strict, snapshot, against } => {
                tools::validate::run(strict, snapshot, against)
            }
            Command::BuildLinks { check } => tools::links::run(check),
            Command::BuildTrees { check } => tools::trees::run(check),
            Command::BuildList { check } => tools::list::run(check),
            Command::Crossref { type_name, verbose, emit } => {
                tools::crossref::run(type_name, verbose, emit)
            }
        };
        std::process::exit(code);
    }

    eprintln!("🚀 [AGENT] Launching Native YAK Agent...");

    // Load YAK configuration
    let app_config = match config::load_config("config.ini") {
        Ok(c) => c,
        Err(e) => {
            error!("Failed to load config: {}", e);
            return;
        }
    };

    if !app_config.enabled {
        info!("Yak protocol is disabled in config. Exiting.");
        return;
    }

    // Load the YAK Repository. Phase 0 item 1: never a hard-coded path —
    // YAK_REPO_PATH wins, else walk up from cwd until the tree is found, so
    // the agent works from openair-yak/, BackEnd/, or the repo root.
    let repo_path = std::env::var("YAK_REPO_PATH").unwrap_or_else(|_| {
        find_yak_tree().unwrap_or_else(|| {
            error!("YAK tree not found from cwd; set YAK_REPO_PATH. Loading zero definitions.");
            String::from("Instruments")
        })
    });
    info!("YAK repository path: {}", repo_path);
    let repo = Arc::new(repository::YakRepository::new(&repo_path));

    // Start the MQTT client loop which acts as the hub
    if let Err(e) = mqtt::start_mqtt_client(app_config, repo).await {
        error!("MQTT client encountered a fatal error: {:?}", e);
    }
}

/// Walk up from the current directory looking for the YAK definition tree.
fn find_yak_tree() -> Option<String> {
    let rel = std::path::Path::new("Instruments");
    let mut dir = std::env::current_dir().ok()?;
    loop {
        let candidate = dir.join(rel);
        if candidate.is_dir() {
            return Some(candidate.to_string_lossy().into_owned());
        }
        if !dir.pop() {
            return None;
        }
    }
}
