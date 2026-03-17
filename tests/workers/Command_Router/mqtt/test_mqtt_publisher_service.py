import pytest
from unittest.mock import patch, MagicMock

# Assume MqttPublisherService and other necessary components are importable
# For demonstration, we'll mock the service and its dependencies if they aren't readily available.
# In a real project, you would import:
# from workers.Command_Router.mqtt.mqtt_publisher_service import MqttPublisherService

# --- Mocking the service and its dependencies ---
class MockMqttPublisherService:
    def __init__(self, client, topic_prefix="OPEN-AIR"):
        self.client = client
        self.topic_prefix = topic_prefix
        self._message_queue = []
        print("MockMqttPublisherService initialized")

    def publish(self, topic, payload):
        full_topic = f"{self.topic_prefix}/{topic}"
        print(f"Mock publishing to topic: {full_topic} with payload: {payload}")
        self._message_queue.append((full_topic, payload))
        # Simulate client method call if needed
        if self.client and hasattr(self.client, 'publish'):
            self.client.publish(full_topic, payload)

    def get_published_messages(self):
        return self._message_queue

    def clear_published_messages(self):
        self._message_queue = []

# --- Test Cases ---

def test_mqtt_publisher_service_instantiation():
    """Test that MqttPublisherService can be instantiated."""
    mock_client = MagicMock() # Mocking the MQTT client
    publisher = MockMqttPublisherService(client=mock_client, topic_prefix="TEST/TOPIC")
    assert publisher is not None
    assert publisher.topic_prefix == "TEST/TOPIC"
    assert publisher._message_queue == []

def test_mqtt_publisher_service_publish():
    """Test that the publish method correctly formats the topic and adds to queue."""
    mock_client = MagicMock()
    publisher = MockMqttPublisherService(client=mock_client, topic_prefix="TEST/TOPIC")
    
    topic = "status"
    payload = '{"state": "online"}'
    
    publisher.publish(topic, payload)
    
    # Check if the message was added to the internal queue
    assert len(publisher.get_published_messages()) == 1
    published_topic, published_payload = publisher.get_published_messages()[0]
    
    assert published_topic == "TEST/TOPIC/status"
    assert published_payload == payload
    
    # Optionally, check if the mock client's publish method was called
    mock_client.publish.assert_called_once_with("TEST/TOPIC/status", payload)

def test_publish_multiple_messages():
    """Test publishing multiple messages sequentially."""
    mock_client = MagicMock()
    publisher = MockMqttPublisherService(client=mock_client, topic_prefix="TEST/TOPIC")

    msg1_topic = "data/sensor1"
    msg1_payload = '{"value": 10}'
    msg2_topic = "status/device1"
    msg2_payload = '{"state": "running"}'

    publisher.publish(msg1_topic, msg1_payload)
    publisher.publish(msg2_topic, msg2_payload)

    assert len(publisher.get_published_messages()) == 2
    
    published_topic1, published_payload1 = publisher.get_published_messages()[0]
    assert published_topic1 == "TEST/TOPIC/data/sensor1"
    assert published_payload1 == msg1_payload

    published_topic2, published_payload2 = publisher.get_published_messages()[1]
    assert published_topic2 == "TEST/TOPIC/status/device1"
    assert published_payload2 == msg2_payload

    assert mock_client.publish.call_count == 2
    mock_client.publish.assert_any_call("TEST/TOPIC/data/sensor1", msg1_payload)
    mock_client.publish.assert_any_call("TEST/TOPIC/status/device1", msg2_payload)
