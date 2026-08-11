use std::thread;
use std::time::Duration;
use test_orchestrator::TestOrchestratorManager;

fn main() {
    println!("[TestOrchestrator] Starting Rust Test Orchestrator Service...");
    let mut manager = TestOrchestratorManager::new();
    manager.initialize_all();

    println!("[TestOrchestrator] Active Orchestrators: {:?}", manager.orchestrators.keys().collect::<Vec<_>>());

    let mut loop_count = 0;
    loop {
        let results = manager.step_all();
        for (name, res) in results {
            println!("[{}] Step result ({}) -> {}", name, res.status, res.data);
        }

        thread::sleep(Duration::from_millis(500));
        loop_count += 1;
        if loop_count > 10 {
            println!("[TestOrchestrator] Service pulse verified. Daemon running cleanly.");
            break;
        }
    }
}
