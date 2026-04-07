{
"$schema": "http://json-schema.org/draft-04/schema#",
"description": "Event data structure",
"oneOf": [
{
"$schema": "http://json-schema.org/draft-04/schema#",
"description": "Property changed event data structure",
"properties": {
"changeType": {
"description": "Event change type numeric value. Must include the numeric values for NcPropertyChangeType",
"maximum": 65535,
"minimum": 0,
"type": "integer"
},
"propertyId": {
"description": "Property ID structure",
"properties": {
"index": {
"description": "Index component of the property ID",
"minimum": 1,
"type": "integer"
},
"level": {
"description": "Level component of the property ID",
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
"sequenceItemIndex": {
"description": "Index of sequence item if the property is a sequence",
"type": [
"number",
"null"
]
},
"value": {
"description": "Property value as described in the MS-05-02 Class definition or in a private Class definition",
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
"propertyId",
"changeType",
"value",
"sequenceItemIndex"
],
"title": "Property changed event data",
"type": "object"
}
],
"title": "Event data",
"type": "object"
}