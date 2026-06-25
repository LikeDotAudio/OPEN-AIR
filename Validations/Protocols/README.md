# Protocol testers

One standalone **real-protocol** tester per protocol — each tests the protocol on
the wire (not the MQTT bus). Runnable directly:

    python3 Validations/Protocols/<proto>/<proto>_tester.py [action] [options]

Each reads its connection params from `BackEnd/ComProtocols/openair-<proto>/config.ini`
(overridable with flags). Shared helpers (config reader, TCP probe, hexdump) live
in `_proto_util.py`.

| Protocol | File | What it does | Library |
|----------|------|--------------|---------|
| osc | `osc/osc_tester.py` | UDP OSC: `listen` / `send` | python-osc |
| osc | `osc/osc_monitor.py` | GUI OSC tree monitor (live) | python-osc + tkinter |
| midi | `midi/midi_tester.py` | `ports` / `listen` / `send` | mido |
| snmp | `snmp/snmp_tester.py` | `snmpwalk` against the agent | net-snmp CLI |
| ptp | `ptp/ptp_tester.py` | sniff UDP 319/320 (needs **sudo**) | scapy |
| rest | `rest/rest_tester.py` | HTTP request to the endpoint | requests |
| nmos | `nmos/nmos_tester.py` | query the IS-04 registry API | requests |
| dnssd | `dnssd/dnssd_tester.py` | browse for the service type | zeroconf |
| mdns | `mdns/mdns_tester.py` | browse for the service type | zeroconf |
| sap | `sap/sap_tester.py` | join SAP multicast, print SDP | stdlib socket |
| websocket | `websocket/websocket_tester.py` | connect, send, print frames | websocket-client |
| visa | `visa/visa_tester.py` | `list` resources / `idn` query | pyvisa |
| mqtt | `mqtt/mqtt_tester.py` | subscribe to the broker (bus monitor) | paho-mqtt |
| aes70 | `aes70/aes70_tester.py` | TCP connect + sniff (OCP.1) | stdlib socket |
| ember | `ember/ember_tester.py` | TCP connect + sniff (S101) | stdlib socket |
| smpte2138 | `smpte2138/smpte2138_tester.py` | TCP connect + sniff (protobuf) | stdlib socket |
| yak | `yak/yak_tester.py` | SCPI `*IDN?` over TCP | stdlib socket |

Run any with `-h` for its options. Most accept `--timeout`; network ones accept
`--host`/`--port` (defaulted from the config.ini). Each exits 0 on success,
2 when it connected/ran but saw no data, 1 on a hard failure.

aes70/ember/smpte2138/yak are binary/instrument protocols — the tester verifies
connectivity and hexdumps the wire traffic (full decode is out of scope).

## Requirements

`pip install python-osc mido python-rtmidi scapy zeroconf pyvisa pyvisa-py
requests websocket-client paho-mqtt`, plus `net-snmp` (`snmpwalk`). All were
present in the dev environment when these were written.
