use regex::Regex;

fn main() {
    let text = std::fs::read_to_string("../../FrontEnd/libControl/faders/Fader/Readme.md").unwrap();
    let re = Regex::new(r"(?s)```json\s*\n(.*?)\n```").unwrap();
    if let Some(caps) = re.captures(&text) {
        let json_str = caps.get(1).unwrap().as_str();
        println!("Captured: {} bytes", json_str.len());
        match serde_json::from_str::<serde_json::Value>(json_str) {
            Ok(_) => println!("JSON OK"),
            Err(e) => println!("JSON Error: {}", e),
        }
    } else {
        println!("No match!");
    }
}
