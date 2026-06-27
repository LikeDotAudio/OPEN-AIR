use rumqttc::{Client, MqttOptions, QoS};
use std::time::Duration;

pub fn publish_devices_mqtt(broker_ip: &str, port: u16, base_topic: &str, inputs: Vec<String>, outputs: Vec<String>) -> Result<(), String> {
    let mut mqttoptions = MqttOptions::new("open-air-midi-scanner", broker_ip, port);
    mqttoptions.set_keep_alive(Duration::from_secs(30));
    
    let (mut client, mut connection) = Client::new(mqttoptions, 10);
    
    std::thread::spawn(move || {
        for _ in connection.iter() {}
    });

    let mut count = 0;
    
    // Publish Inputs
    for (i, name) in inputs.iter().enumerate() {
        println!("     ✅ Identified & Published Input: {}", name);
        let topic_prefix = format!("{}/Input/Dev{}", base_topic.trim_end_matches('/'), i);
        let _ = client.publish(format!("{}/name", topic_prefix), QoS::AtLeastOnce, true, name.as_bytes());
        let _ = client.publish(format!("{}/type", topic_prefix), QoS::AtLeastOnce, true, "input".as_bytes());
        let _ = client.publish(format!("{}/Read", topic_prefix), QoS::AtLeastOnce, true, "");
        count += 3;
    }

    // Publish Outputs
    for (i, name) in outputs.iter().enumerate() {
        println!("     ✅ Identified & Published Output: {}", name);
        let topic_prefix = format!("{}/Output/Dev{}", base_topic.trim_end_matches('/'), i);
        let _ = client.publish(format!("{}/name", topic_prefix), QoS::AtLeastOnce, true, name.as_bytes());
        let _ = client.publish(format!("{}/type", topic_prefix), QoS::AtLeastOnce, true, "output".as_bytes());
        let _ = client.publish(format!("{}/Write", topic_prefix), QoS::AtLeastOnce, true, "");
        count += 3;
    }

    println!("   📡 [MIDI AGENT] Published {} attributes to {}", count, base_topic);
    
    // allow a brief moment for flush before dropping client
    std::thread::sleep(Duration::from_millis(500));
    Ok(())
}
