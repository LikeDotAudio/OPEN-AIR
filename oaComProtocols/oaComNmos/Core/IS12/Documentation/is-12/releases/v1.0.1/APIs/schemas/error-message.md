{
"$schema": "http://json-schema.org/draft-04/schema#",
"allOf": [
{
"$schema": "http://json-schema.org/draft-04/schema#",
"description": "Base protocol message structure",
"properties": {
"messageType": {
"description": "Protocol message type",
"enum": [
0,
1,
2,
3,
4,
5
],
"type": "integer"
}
},
"required": [
"messageType"
],
"title": "Base protocol message",
"type": "object"
},
{
"properties": {
"errorMessage": {
"description": "Error details associated with the failure",
"type": "string"
},
"messageType": {
"description": "Protocol message type",
"enum": [
5
],
"type": "integer"
},
"status": {
"description": "Status of the message response. Must include the numeric values for NcMethodStatus or other types which inherit from it.",
"maximum": 65535,
"minimum": 0,
"type": "integer"
}
},
"required": [
"status",
"errorMessage",
"messageType"
],
"type": "object"
}
],
"description": "Error protocol message structure - used by devices to return general error messages for example when incoming messages do not have messageType, handles or contain invalid JSON",
"title": "Error protocol message",
"type": "object"
}