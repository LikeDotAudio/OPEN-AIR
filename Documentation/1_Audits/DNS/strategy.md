# Public Internet Exposure & HTTPS / WSS MQTT Connectivity Strategy

## Executive Summary
This document outlines the architectural strategies to safely expose the local machine running **OPEN-AIR** services to the public internet under `https://openair.like.audio/`, enabling secure HTTPS web interface access and WebSockets over TLS (`wss://`) for MQTT client connections.

---

## 1. Technical Context & Requirements
- **Web Interface**: Static or dynamic frontend served at `https://openair.like.audio/`.
- **MQTT Service**:
  - Local TCP MQTT broker running on port `1883`.
  - Local WebSocket MQTT broker running on port `9001` (required for web browsers accessing the HTTPS frontend, as modern browsers block mixed insecure content like unencrypted `ws://` on an `https://` site).
- **Target Protocol**: HTTPS (`https://openair.like.audio/`) and Secure WebSockets (`wss://openair.like.audio/mqtt` or `wss://openair.like.audio:9001`).

---

## 2. Deployment Architecture Options

We present **3 Primary Architecture Options** based on your network environment and operational constraints.

```
                   +-------------------------------------------------+
                   |           Public Internet Client                |
                   |      (Browser / Remote MQTT Client)             |
                   +-------------------------------------------------+
                                           |
                                   https:// openair.like.audio
                                           |
    +--------------------------------------+--------------------------------------+
    |                                      |                                      |
    v                                      v                                      v
[Option A: Tunneling]               [Option B: Reverse Proxy]              [Option C: Direct IP / Dynamic DNS]
Cloudflare Tunnel / Tailscale       Cloud Server + Reverse Proxy           Router Port Forward + DDNS
(No Router Port Forwarding)         (VPS with Public Static IP)           (Public IPv4 + ACME Certbot)
    |                                      |                                      |
    +--------------------------------------+--------------------------------------+
                                           |
                                           v
                   +-------------------------------------------------+
                   |           Local Machine (OPEN-AIR Host)         |
                   |                                                 |
                   |  - Web Frontend / Static Server                 |
                   |  - MQTT Broker (TCP: 1883, WS: 9001)           |
                   |  - Orchestrator / ComProtocols (Rust/Node)      |
                   +-------------------------------------------------+
```

---

### Option A: Tunneling via Cloudflare Tunnel (Cloudflared) — **[RECOMMENDED]**
*Best for: Zero-configuration router setups, CGNAT networks, maximum security without exposing public IPv4 addresses.*

#### How It Works:
1. `cloudflared` daemon runs locally on the host machine.
2. An outbound encrypted tunnel connects to Cloudflare's edge servers.
3. Domain `openair.like.audio` routes traffic through Cloudflare directly to local ports (`8000` / `9001`).
4. SSL/TLS standard certificates (`https://` and `wss://`) are managed automatically by Cloudflare.

#### Architecture Setup:
- **Web Frontend**: `https://openair.like.audio/` -> `http://localhost:8000`
- **MQTT WebSockets**: `wss://openair.like.audio/mqtt` -> `http://localhost:9001`

#### Implementation Steps:
1. Install `cloudflared` on the local machine:
   ```bash
   sudo apt-get install cloudflared
   ```
2. Authenticate and create a named tunnel:
   ```bash
   cloudflared tunnel login
   cloudflared tunnel create openair-local
   ```
3. Configure `~/.cloudflared/config.yml`:
   ```yaml
   tunnel: <TUNNEL-UUID>
   credentials-file: /home/anthony/.cloudflared/<TUNNEL-UUID>.json

   ingress:
     - hostname: openair.like.audio
       path: /mqtt
       service: ws://localhost:9001
     - hostname: openair.like.audio
       service: http://localhost:8000
     - service: http_status:404
   ```
4. Map the CNAME record for `openair.like.audio` to `<TUNNEL-UUID>.cfargotunnel.com` via Cloudflare DNS.
5. Run the service:
   ```bash
   cloudflared tunnel run openair-local
   ```

---

### Option B: VPS Reverse Proxy / VPN Bridge (Tailscale / WireGuard)
*Best for: Static IP host environments with custom web server control.*

#### How It Works:
1. A small public VPS (e.g., DigitalOcean, Hetzner, AWS) holds the public IP for `openair.like.audio`.
2. NGINX or Caddy on the VPS acts as the public TLS termination point.
3. Tailscale / WireGuard creates a private mesh connection between the VPS and this local machine.
4. Traffic to `openair.like.audio` is proxied over the VPN tunnel to the local machine.

#### NGINX Reverse Proxy Configuration (on VPS):
```nginx
server {
    server_name openair.like.audio;

    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/openair.like.audio/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/openair.like.audio/privkey.pem;

    # Frontend UI
    location / {
        proxy_pass http://100.x.y.z:8000; # Tailscale IPv4 of local host
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # MQTT WebSockets Protocol
    location /mqtt {
        proxy_pass http://100.x.y.z:9001; # Local MQTT WS port
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

---

### Option C: Port Forwarding + Dynamic DNS + Let's Encrypt (Certbot)
*Best for: Direct internet connectivity with control over network gateway.*

#### How It Works:
1. Public DNS record for `openair.like.audio` (A Record) points to your router's public WAN IP address.
2. Router forwards incoming traffic on ports `80`, `443`, and `8883` / `9001` to this machine's local IP address.
3. Certbot or Caddy running locally retrieves a TLS certificate from Let's Encrypt.

#### Requirements:
- Router administrative access.
- Non-CGNAT public IPv4 address from your ISP.
- Port forwarding rules:
  - WAN `80/443` -> Local IP `80/443` (for Web & TLS)
  - WAN `8883` -> Local IP `9001` or broker MQTTS port.

---

## 3. MQTT Client Integration Requirements

Browsers connecting to `https://openair.like.audio/` **must** use WebSockets over TLS (`wss://`) to avoid mixed content security violations.

### Frontend MQTT Client Connection Snippet (JavaScript):
```javascript
const client = mqtt.connect('wss://openair.like.audio/mqtt', {
  clientId: 'openair_web_' + Math.random().toString(16).substring(2, 8),
  clean: true,
  connectTimeout: 4000,
  reconnectPeriod: 1000,
});

client.on('connect', () => {
  console.log('Connected to OPEN-AIR MQTT Broker over WSS');
  client.subscribe('OpenAir/System/Protocols/mqtt');
});
```

---

## 4. Security & Hardening Recommendations

1. **Broker Authentication**: Ensure `allow_anonymous false` is configured on the public-facing broker, requiring valid credentials or token-based authentication.
2. **Rate Limiting**: Apply connection rate limits at the reverse proxy level to defend against DoS attacks.
3. **Firewall (UFW)**: Block direct external access to raw unencrypted ports (`1883`, `9001`) from outside the local network. Only permit ingress via the tunnel or proxy service.

---

## 5. Summary Recommendation

For fastest setup, security, and minimal network configuration hassle, **Option A (Cloudflare Tunnel)** is recommended. It handles HTTPS/WSS certificates automatically, works behind home routers without port forwarding or static IPs, and provides TLS termination out of the box.
