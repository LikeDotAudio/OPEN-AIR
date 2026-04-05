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
}