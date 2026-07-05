/**
 * Header: pcm_visualizer.rs
 * Purpose: pcm_visualizer.rs implementation.
 * Description: Logic and implementation for pcm_visualizer.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaAudioMixer/Core/oaAudioMixer_rs/src/bin/pcm_visualizer.rs
use std::process::{Command, Stdio};
use std::io::Read;
use std::thread;
use std::time::Duration;
use std::env;

// Inline comment: Logic for main
fn main() {
    let args: Vec<String> = env::args().collect();
    let target = if args.len() > 1 { &args[1] } else { "@DEFAULT_AUDIO_SINK@" };

    let mut child = Command::new("pw-record")
        .args(&["--target", target, "--format", "s16", "--rate", "44100", "--channels", "2", "-"])
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .expect("Failed to start pw-record");

    let mut stdout = child.stdout.take().expect("Failed to get stdout pipe");
    let mut buffer = [0u8; 16]; // Read exactly 16 bytes for a fixed-size display

    loop {
        if stdout.read_exact(&mut buffer).is_ok() {
            let mut out = String::new();
            for byte in buffer.iter() {
                out.push_str(&format!("{:08b}\n", byte));
            }
            // Print the 16 bytes vertically as a single "frame"
            // We use a separator to help the TUI identify frames
            println!("---FRAME---\n{}", out);
            
            thread::sleep(Duration::from_millis(50));
        } else {
            break;
        }
    }
}
