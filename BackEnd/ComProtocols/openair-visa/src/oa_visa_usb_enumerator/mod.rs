use std::fs;

pub fn discover_local_devices() -> Vec<String> {
    let mut resources = Vec::new();
    // List serial ports naively
    if let Ok(entries) = fs::read_dir("/dev") {
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().into_owned();
            if name.starts_with("ttyUSB") || name.starts_with("ttyACM") {
                resources.push(format!("ASRL/dev/{}::INSTR", name));
            }
        }
    }
    resources
}
