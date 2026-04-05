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
"commands": {
"description": "Commands being transmited in this transaction",
"items": {
"properties": {
"arguments": {
"description": "Method arguments",
"type": "object"
},
"handle": {
"description": "Integer value used for pairing with the response",
"maximum": 65535,
"minimum": 1,
"type": "integer"
},
"methodId": {
"description": "ID structure for the target method",
"properties": {
"index": {
"description": "Index component of the method ID",
"minimum": 1,
"type": "integer"
},
"level": {
"description": "Level component of the method ID",
"minimum": 1,
"type": "integer"
}
},
"required": [
"level",
"index"
],
"type": "object"
},
"oid": {
"description": "Object id containing the method",
"minimum": 1,
"type": "integer"
}
},
"required": [
"handle",
"oid",
"methodId"
],
"type": "object"
},
"type": "array"
},
"messageType": {
"description": "Protocol message type",
"enum": [
0
],
"type": "integer"
}
},
"required": [
"commands",
"messageType"
],
"type": "object"
}
],
"description": "Command protocol message structure",
"title": "Command protocol message",
"type": "object"
}