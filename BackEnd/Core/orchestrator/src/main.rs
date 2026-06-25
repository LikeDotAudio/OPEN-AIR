use axum::{
    extract::ws::{Message, WebSocket, WebSocketUpgrade},
    extract::State,
    response::IntoResponse,
    routing::get,
    Router,
};
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::broadcast;
use serde::{Deserialize, Serialize};
use serde_json::Value;

// This struct represents the unified data format that the Frontend React app expects.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SystemState {
    pub topic: String,
    pub value: Value,
}

// Shared state for the Axum router
struct AppState {
    tx: broadcast::Sender<SystemState>,
}

#[tokio::main]
async fn main() {
    println!("🚀 [RUST ORCHESTRATOR] Booting OPEN-AIR Native Core...");

    // 1. Create the high-speed lock-free channel for the internal message bus
    // This replaces the old Python ProtocolRouter. All protocol agents will clone the sender.
    let (tx, _rx) = broadcast::channel::<SystemState>(1024);
    let app_state = Arc::new(AppState { tx: tx.clone() });

    // 2. Launch the Native Device Protocol Agents
    // In the future, this reads `config.ini` and dynamically spawns these based on settings.
    let tx_clone_osc = tx.clone();
    tokio::spawn(async move {
        println!("🚀 [AGENT] Launching Native OSC Agent on 0.0.0.0:8000...");
        let osc_agent = openair_osc::OscAgent::new("0.0.0.0".to_string(), 8000);
        let (osc_tx, mut osc_rx) = tokio::sync::mpsc::channel(100);
        
        tokio::spawn(async move {
            let _ = osc_agent.start(osc_tx).await;
        });

        while let Some(osc_event) = osc_rx.recv().await {
            let system_event = SystemState {
                topic: format!("OpenAir/Protocol/GuiOsc/{}", osc_event.address),
                value: osc_event.value,
            };
            let _ = tx_clone_osc.send(system_event);
        }
    });

    let tx_clone_midi = tx.clone();
    tokio::spawn(async move {
        println!("🚀 [AGENT] Launching Native MIDI Agent...");
        // Auto-select the first available port
        let midi_agent = openair_midi::MidiAgent::new(None); 
        let (midi_tx, mut midi_rx) = tokio::sync::mpsc::channel(100);

        tokio::spawn(async move {
            if let Err(e) = midi_agent.start(midi_tx).await {
                eprintln!("🎹❌ [MIDI AGENT] Failed to start: {:?}", e);
            }
        });

        // Forward MIDI Events to the Global Broadcast Channel
        while let Some(midi_event) = midi_rx.recv().await {
            let system_event = SystemState {
                topic: format!("OpenAir/Protocol/MidiIn/{}", midi_event.address),
                value: midi_event.value,
            };
            let _ = tx_clone_midi.send(system_event);
        }
    });

    let tx_clone_aes70 = tx.clone();
    tokio::spawn(async move {
        println!("🚀 [AGENT] Launching Native AES70 Agent (OCP.1 TCP)...");
        // For demonstration, connects to a hypothetical AES70 device on localhost:50014
        let aes70_agent = openair_aes70::Aes70Agent::new("127.0.0.1".to_string(), 50014); 
        let (aes70_tx, mut aes70_rx) = tokio::sync::mpsc::channel(100);

        tokio::spawn(async move {
            if let Err(e) = aes70_agent.start(aes70_tx).await {
                eprintln!("🔊❌ [AES70 AGENT] Failed to start: {:?}", e);
            }
        });

        // Forward AES70 Events to the Global Broadcast Channel
        while let Some(aes70_event) = aes70_rx.recv().await {
            let system_event = SystemState {
                topic: format!("OpenAir/Protocol/AES70/{}", aes70_event.address),
                value: aes70_event.value,
            };
            let _ = tx_clone_aes70.send(system_event);
        }
    });

    // 3. Frontend WebSocket API (The axum Server)
    // This replaces `oaComWebsocket`. The React Frontend will connect here.
    let app = Router::new()
        .route("/api/health", get(|| async { "Rust Core is Healthy" }))
        .route("/ws", get(ws_handler))
        .with_state(app_state);

    // Port is overridable via OPENAIR_CORE_PORT so the launcher (openair.py) can
    // keep this Rust core off the frontend static server's port. Defaults to 8000.
    let port: u16 = std::env::var("OPENAIR_CORE_PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8000);
    let addr = SocketAddr::from(([127, 0, 0, 1], port));

    // 4. Start the Async Runtime Server — bind gracefully (no panic) so a stale
    // instance still holding the port produces a clear message, not a backtrace.
    let listener = match tokio::net::TcpListener::bind(addr).await {
        Ok(l) => l,
        Err(e) => {
            eprintln!("❌ [API] Could not bind {addr}: {e}");
            eprintln!("        Another orchestrator is likely still running on port {port}. \
                       Stop it, or set OPENAIR_CORE_PORT to a free port.");
            return;
        }
    };
    println!("🌐 [API] Frontend API Server listening on http://{}", addr);
    if let Err(e) = axum::serve(listener, app).await {
        eprintln!("❌ [API] server error: {e}");
    }
}

// The WebSocket handler upgrades the HTTP request
async fn ws_handler(
    ws: WebSocketUpgrade,
    State(state): State<Arc<AppState>>,
) -> impl IntoResponse {
    println!("🔌 [WEBSOCKET] Client requested connection...");
    ws.on_upgrade(|socket| handle_socket(socket, state))
}

// The core loop for a connected WebSocket client
async fn handle_socket(mut socket: WebSocket, state: Arc<AppState>) {
    println!("🟢 [WEBSOCKET] Client connected!");
    
    // Subscribe to the global message bus
    let mut rx = state.tx.subscribe();

    // Loop to read from the broadcast channel and push to the WebSocket
    loop {
        tokio::select! {
            // Receive from the core message bus
            Ok(msg) = rx.recv() => {
                // Serialize the SystemState to JSON
                if let Ok(json_str) = serde_json::to_string(&msg) {
                    // Send to the React frontend
                    if socket.send(Message::Text(json_str)).await.is_err() {
                        println!("🔴 [WEBSOCKET] Client disconnected.");
                        break;
                    }
                }
            }
            // Optionally: Handle incoming messages from the frontend (e.g., UI clicks)
            Some(result) = socket.recv() => {
                match result {
                    Ok(Message::Text(text)) => {
                        println!("📥 [WEBSOCKET] Received from UI: {}", text);
                        // Here you would parse the UI intent and route it back to the gear
                        // via the `tx` channel or a dedicated command channel.
                    }
                    Ok(Message::Close(_)) => {
                        println!("🔴 [WEBSOCKET] Client closed connection.");
                        break;
                    }
                    Err(_) => {
                        println!("⚠️ [WEBSOCKET] Error receiving from client.");
                        break;
                    }
                    _ => {}
                }
            }
        }
    }
}
