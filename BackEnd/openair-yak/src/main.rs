mod config;
mod mqtt;
mod verbs;
mod models;
mod converters;
mod repository;

use log::{info, error};
use std::sync::Arc;

#[tokio::main]
async fn main() {
    // Initialize logging for anything we didn't manually port to println
    env_logger::init();
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
            String::from("BackEnd/openair-yak/10_Yak")
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
    let rel = std::path::Path::new("BackEnd/openair-yak/10_Yak");
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
