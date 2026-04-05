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
4
],
"type": "integer"
},
"subscriptions": {
"description": "Array of OIDs which have successfully been added to the subscription list.",
"items": {
"type": "integer"
},
"type": "array"
}
},
"required": [
"subscriptions",
"messageType"
],
"type": "object"
}
],
"description": "Subscription response protocol message structure",
"title": "Subscription response protocol message",
"type": "object"
}