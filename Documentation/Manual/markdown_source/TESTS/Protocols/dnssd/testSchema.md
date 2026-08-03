# DNS-SD (DNS Service Discovery) - Test Schema

## Framework
This schema defines the integration test boundary between the standalone testing tools and the OPEN-AIR core.

Test Schema: 
1. Broadcast a mock service.
2. Verify the receiver discovers it within the TTL.
3. Verify TXT record parsing.
4. Handle service withdrawal (TTL=0).
