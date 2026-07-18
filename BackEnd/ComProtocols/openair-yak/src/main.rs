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

    // Load the YAK Repository
    let repo_path = std::env::var("YAK_REPO_PATH").unwrap_or_else(|_| String::from("../../FrontEnd/Gui_Frames/5_Protocols/10_Yak"));
    let repo = Arc::new(repository::YakRepository::new(&repo_path));

    // Start the MQTT client loop which acts as the hub
    if let Err(e) = mqtt::start_mqtt_client(app_config, repo).await {
        error!("MQTT client encountered a fatal error: {:?}", e);
    }
}
