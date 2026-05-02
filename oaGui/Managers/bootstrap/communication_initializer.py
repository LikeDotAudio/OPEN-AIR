# oaGui/Managers/bootstrap/communication_initializer.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for initializing MQTT communication and state cache subscriptions.

def initialize_communications(splash, mqtt_conn, sub_router, state_cache):
    """Connects to the MQTT broker and establishes initial state subscriptions."""
    splash.set_status(message="Connecting to Broker...")
    
    mqtt_conn.connect_to_broker(
        on_message_callback=state_cache.handle_incoming_mqtt,
        subscriber_router=sub_router
    )
    
    state_cache.subscribe_to_all_topics()
