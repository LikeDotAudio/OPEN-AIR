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
"messageType": {
"description": "Protocol message type",
"enum": [
1
],
"type": "integer"
},
"responses": {
"description": "Responses being transmited in this transaction",
"items": {
"properties": {
"handle": {
"description": "Integer value used for pairing with the command",
"maximum": 65535,
"minimum": 1,
"type": "integer"
},
"result": {
"description": "Response result",
"properties": {
"errorMessage": {
"description": "Error message associated with the failure of the command (optional)",
"type": "string"
},
"status": {
"description": "Status of the command response. Must include the numeric values for NcMethodStatus or other types which inherit from it. 200 must be returned if the command was successful",
"maximum": 65535,
"minimum": 0,
"type": "integer"
},
"value": {
"description": "Method return value as described in the MS-05-02 Type definition or in a private Type definition",
"type": [
"string",
"number",
"object",
"array",
"boolean",
"null"
]
}
},
"required": [
"status"
],
"type": "object"
}
},
"required": [
"handle",
"result"
],
"type": "object"
},
"type": "array"
}
},
"required": [
"responses",
"messageType"
],
"type": "object"
}
],
"description": "Command response protocol message structure",
"title": "Command response protocol message",
"type": "object"
}