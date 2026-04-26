# oaComProtocols.oaComNmos/Core/IS12/Interface/schemas.py
# Author: Gemini (Collaborator)
# Version: 20260405.1547.2

"""
Pydantic models for IS-12 NMOS Control Protocol schemas.
"""

from typing import Any

from pydantic import BaseModel, Field, StrictInt, StrictStr


# Base message schema
class IS12BaseMessage(BaseModel):
    message_id: StrictStr = Field(..., description="Unique identifier for the message.")
    timestamp: StrictStr = Field(..., description="Timestamp in ISO 8601 format.")
    version: StrictStr = Field(..., description="Protocol version string.")
    # Other common fields might be added based on actual specs if available

# Command message schema
class IS12CommandMessage(IS12BaseMessage):
    operation: StrictStr = Field(..., description="The operation to perform (e.g., 'Set', 'Get', 'Invoke').")
    resource_id: StrictStr | None = Field(None, description="Identifier of the resource to operate on.")
    parameters: dict[StrictStr, Any] | None = Field(None, description="Parameters for the command.")
    # Additional fields as per protocol specification

# Command Response message schema
class IS12CommandResponseMessage(IS12BaseMessage):
    command_result: StrictStr = Field(..., description="Result of the command ('Success', 'Failure').")
    data: dict[StrictStr, Any] | None = Field(None, description="Data returned by the command.")
    error: dict[str, Any] | None = Field(None, description="Error details if command_result is 'Failure'.")
    # Additional fields as per protocol specification

# Subscription message schema
class IS12SubscriptionMessage(IS12BaseMessage):
    subscription_id: StrictStr = Field(..., description="Unique identifier for the subscription.")
    resource_ids: list[StrictStr] = Field(..., description="List of resource IDs to subscribe to.")
    event_types: list[StrictStr] = Field(..., description="List of event types to subscribe to (e.g., 'property_changed', 'state_changed').")
    filter: dict[str, Any] | None = Field(None, description="Optional filter for events.")

# Subscription Response message schema
class IS12SubscriptionResponseMessage(IS12BaseMessage):
    subscription_id: StrictStr = Field(..., description="Identifier of the subscription being responded to.")
    status: StrictStr = Field(..., description="Status of the subscription ('Subscribed', 'Failed').")
    message: StrictStr | None = Field(None, description="Message providing details on the subscription status.")

# Notification message schema
class IS12NotificationMessage(IS12BaseMessage):
    notification_id: StrictStr = Field(..., description="Unique identifier for the notification.")
    resource_id: StrictStr = Field(..., description="Identifier of the resource the notification pertains to.")
    event_type: StrictStr = Field(..., description="Type of event (e.g., 'property_changed').")
    event_data: dict[str, Any] = Field(..., description="Data associated with the event.")

# Event Data schema (used within NotificationMessage)
class IS12EventData(BaseModel):
    # This can be a generic dict or specific models if event types are well-defined
    # For now, using a generic dictionary.
    pass

# Error Message schema
class IS12ErrorMessage(IS12BaseMessage):
    error_code: StrictInt = Field(..., description="Numeric error code.")
    error_message: StrictStr = Field(..., description="Human-readable error message.")
    details: dict[str, Any] | None = Field(None, description="Additional error details.")

# Example usage (for development and testing)
if __name__ == "__main__":
    try:
        # Example of creating a command message
        command_message = IS12CommandMessage(
            message_id="cmd-123",
            timestamp="2026-04-05T15:47:00Z",
            version="1.0.1",
            operation="Set",
            resource_id="device-abc",
            parameters={"setting": "volume", "value": 50}
        )
        print("Created Command Message:")
        print(command_message.model_dump_json(indent=2))

        # Example of creating a command response message (success)
        response_success = IS12CommandResponseMessage(
            message_id="resp-123",
            timestamp="2026-04-05T15:47:01Z",
            version="1.0.1",
            command_result="Success",
            data={"current_volume": 50}
        )
        print("Created Success Response Message:")
        print(response_success.model_dump_json(indent=2))

        # Example of creating a command response message (failure)
        response_failure = IS12CommandResponseMessage(
            message_id="resp-124",
            timestamp="2026-04-05T15:47:02Z",
            version="1.0.1",
            command_result="Failure",
            error={"error_code": 400, "error_message": "Invalid parameter value."}
        )
        print("Created Failure Response Message:")
        print(response_failure.model_dump_json(indent=2))

        # Example of creating a subscription message
        subscription_message = IS12SubscriptionMessage(
            message_id="sub-abc",
            timestamp="2026-04-05T15:47:03Z",
            version="1.0.1",
            subscription_id="sub-001",
            resource_ids=["device-xyz"],
            event_types=["property_changed"],
            filter={"parameter": "volume"}
        )
        print("Created Subscription Message:")
        print(subscription_message.model_dump_json(indent=2))

    except Exception as e:
        print(f"An error occurred during schema example generation: {e}")

