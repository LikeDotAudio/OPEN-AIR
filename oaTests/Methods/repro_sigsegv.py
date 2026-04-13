import time
from oaComBroker.Core.protocol_router.manager import ProtocolRouter
from oaStateCache.Core.state_cache import StateRegistry
from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager

def reproduce_crash():
    print("🚀 Starting reproduction test...")
    mqtt = MqttConnectionManager()
    state = StateRegistry(mqtt)
    
    print("📂 Simulating large cache ingestion...")
    # Create a lot of fake data
    fake_data = {}
    for i in range(5000):
        topic = f"OPEN-AIR/System/Status/Test/Topic_{i}"
        fake_data[topic] = {"value": i, "timestamp": time.time(), "source": "DISK", "boot": True}
    
    # Inject it into the state registry's cache manually to trigger initialize_state-like behavior
    state.rust_cache.update(fake_data)
    
    print("⏳ Running initialize_state sequence...")
    state.initialize_state()
    
    print("✅ Finished reproduction test without crash.")

if __name__ == "__main__":
    reproduce_crash()
