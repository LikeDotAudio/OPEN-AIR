# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260405.1315.12

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union

# --- Core Data Structures for IS-07 Events and Messages ---

@dataclass
class Identity:
    """Represents the identity of an event source or message sender."""
    source_id: str
    flow_id: Optional[str] = None

@dataclass
class Timing:
    """Represents timing information for an event or message."""
    creation_timestamp: str # e.g., "1531680501:280709600"
    origin_timestamp: Optional[str] = None
    action_timestamp: Optional[str] = None

# --- Type Definitions ---
# These classes represent the structure for defining event types.

@dataclass
class NumberValue:
    """Represents a numerical value, potentially with a scale for rational numbers."""
    value: Union[int, float]
    scale: Optional[int] = None

@dataclass
class NumberTypeDefinition:
    """Defines a number event type with constraints and optional scale/unit."""
    type: str = "number"
    scale: Optional[int] = None
    min: Optional[NumberValue] = None
    max: Optional[NumberValue] = None
    step: Optional[NumberValue] = None
    unit: Optional[str] = None

@dataclass
class StringTypeDefinition:
    """Defines a string event type with length and pattern constraints."""
    type: str = "string"
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None

@dataclass
class BooleanTypeDefinition:
    """Defines a boolean event type."""
    type: str = "boolean"

@dataclass
class EnumValue:
    """Represents a single value within an enumerated type."""
    value: Union[bool, int, float, str]
    label: str
    description: str

@dataclass
class BooleanEnumTypeDefinition:
    """Defines a boolean enumerated type."""
    type: str = "boolean"
    values: List[EnumValue]

@dataclass
class NumberEnumTypeDefinition:
    """Defines a number enumerated type."""
    type: str = "number"
    values: List[EnumValue]

@dataclass
class StringEnumTypeDefinition:
    """Defines a string enumerated type."""
    type: str = "string"
    values: List[EnumValue]

# Union for type definitions to allow any of them
TypeDefinition = Union[
    BooleanTypeDefinition,
    StringTypeDefinition,
    NumberTypeDefinition,
    BooleanEnumTypeDefinition,
    NumberEnumTypeDefinition,
    StringTypeDefinition, # Assuming string enum will be string type def with values
]

# --- Event Payloads ---
# These represent the actual data being sent for different event types.

@dataclass
class BooleanPayload:
    """Payload for boolean events."""
    value: bool

@dataclass
class StringPayload:
    """Payload for string events."""
    value: str

@dataclass
class NumberPayload:
    """Payload for number events."""
    value: Union[int, float]
    scale: Optional[int] = None

@dataclass
class ObjectPayload(Dict[str, Any]):
    """Payload for object events. Using Dict as a base for flexibility."""
    pass

# --- Base Event Structure ---

@dataclass
class EventCore:
    """Core structure for all IS-07 state change events."""
    identity: Identity
    timing: Timing
    event_type: str # e.g., "boolean", "number/temperature/C", "boolean/enum/OnOff"
    payload: Union[BooleanPayload, StringPayload, NumberPayload, ObjectPayload]
    message_type: str = "state" # Default to state message type

# Specific Event Types (composed of EventCore + specific payload type)
# Note: These are conceptual representations; the actual event_type string determines the payload structure.
# The EventCore payload type is Union[...], so the structure is determined by event_type.

# --- Message Structures ---

@dataclass
class MessageConnectionStatus:
    """Represents an MQTT connection status message."""
    active: bool
    message_type: str = "connection_status"

@dataclass
class MessageShutdownReboot:
    """Represents a shutdown or reboot message."""
    identity: Identity
    timing: Timing
    message_type: str # "reboot" or "shutdown"

@dataclass
class MessageHealth:
    """Represents a health/heartbeat message."""
    timing: Timing
    message_type: str = "health"

# Union for all possible message types
Message = Union[
    EventCore, # State change messages are also messages
    MessageConnectionStatus,
    MessageShutdownReboot,
    MessageHealth,
]

# --- Helper for type definitions that might be fetched via API ---
# This is a simplified representation; a real implementation might need to
# handle deserialization from JSON and dynamic type creation.

# Placeholder for potentially complex type definitions fetched via API
# A more robust system would involve a factory or registry to create
# the correct TypeDefinition object based on 'type' and 'values' fields.
# For now, we define a general structure.
@dataclass
class GenericTypeDefinition:
    """A general representation for type definitions that might include various fields."""
    type: str
    values: Optional[List[Dict[str, Any]]] = None # For enums
    min: Optional[Dict[str, Any]] = None # For number type
    max: Optional[Dict[str, Any]] = None
    step: Optional[Dict[str, Any]] = None
    unit: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None

