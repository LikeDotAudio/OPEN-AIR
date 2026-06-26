use rumqttc::{Client, MqttOptions, QoS};
use std::time::Duration;

pub struct MqttPublisher {
    client: Client,
}

impl MqttPublisher {
    pub fn new(broker_ip: &str, port: u16) -> Self {
        let mut mqttoptions = MqttOptions::new("openair-visa-publisher", broker_ip, port);
        mqttoptions.set_keep_alive(Duration::from_secs(5));
        
        let (client, mut connection) = Client::new(mqttoptions, 10);
        
        std::thread::spawn(move || {
            for _ in connection.iter() {}
        });
        
        Self { client }
    }
    
    pub fn publish_device(&self, base_topic: &str, category: &str, model: &str, count: usize, payload_json: &str) {
        // Safe topic string mapping
        let safe_cat = category.replace(" ", "_");
        let safe_model = model.replace(" ", "_");
        let topic = format!("{}/{}/{}/Dev{}", base_topic.trim_end_matches('/'), safe_cat, safe_model, count);
        
        let _ = self.client.publish(topic, QoS::AtLeastOnce, true, payload_json.as_bytes());
    }
    
    pub fn publish_device_attribute(&self, base_topic: &str, category: &str, model: &str, count: usize, attribute: &str, payload: &str) {
        let safe_cat = category.replace(" ", "_");
        let safe_model = model.replace(" ", "_");
        let topic = format!("{}/{}/{}/Dev{}/{}", base_topic.trim_end_matches('/'), safe_cat, safe_model, count, attribute);
        
        let _ = self.client.publish(topic, QoS::AtLeastOnce, true, payload.as_bytes());
    }
    
    pub fn publish_raw(&self, topic: &str, payload: &str) {
        let _ = self.client.publish(topic, QoS::AtLeastOnce, true, payload.as_bytes());
    }
    
    pub fn flush(&self, _count: usize) {
        // Allow background thread time to send messages before dropping
        std::thread::sleep(Duration::from_millis(1500));
    }
}
