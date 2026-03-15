# _broker_link

Executes the "Link" operation: forwarding data from a destination back to a source.

## Role
Facilitates bidirectional communication by syncing changes from the destination back to the source.

### Logic
- Mirror image of `_broker_splice`, but targets the source topic.
- Essential for keeping UI controls and hardware in sync.
