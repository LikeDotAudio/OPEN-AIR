# docker/ — the one-command startup path

Everything needed to run OPEN-AIR without installing a Rust toolchain, a Python
environment, or a broker on the host.

```bash
python3 docker/launch.py
```

Then open **http://localhost:8000**.

Works from any directory — paths resolve against this folder, not your shell.

## Contents

| File | What it is |
|---|---|
| `launch.py` | Launcher. Preflights Docker, starts the stack, waits for health, opens a browser. Stdlib only. |
| `docker-compose.yml` | Two services: `broker` (mosquitto) and `orchestrator`. Build context is the **repo root**. |
| `Dockerfile` | Multi-stage: builds the Rust orchestrator, then a slim runtime with Python + pyvisa for the VISA probe path. |
| `mosquitto.conf` | Broker config for the **container**. Differs from `../broker/mosquitto.conf` — see below. |

## ⚠️ Networking: use `--host-net` for a real bench

**Containers do NOT get an address from your DHCP.** They sit on a Docker bridge
(`172.20.0.x`), NAT'd behind the host. That breaks discovery in two ways that are
*silent* — both look like "no devices found":

| | Bridge (default) | `--host-net` |
|---|---|---|
| VISA/SCPI outbound TCP | ✅ works (NAT) | ✅ works |
| **mDNS / DNS-SD** | ❌ multicast does not cross the bridge — every address resolves to `172.20.0.1`, the gateway | ✅ real LAN addresses |
| **VISA subnet scan** | ❌ derives the subnet from its own IP → scans `172.20.0.1-254`, where no instrument lives | ✅ scans your real subnet |

```bash
python3 docker/launch.py --host-net              # LAN discovery works
python3 docker/launch.py --host-net --hardware   # …plus USB + MIDI
```

Host mode still does not give the container its own DHCP address — it has no
separate address at all, it *is* the host. A genuine per-container LAN IP needs a
**macvlan** network, which also needs a shim interface for host↔container
traffic. For a single-box lab tool, host mode is the better trade.

**Security:** host mode removes the port mapping that confined the bridge setup.
Confinement then comes from what each process binds — the orchestrator binds
`127.0.0.1` (`--bind`) and the broker uses `../broker/mosquitto.conf`, which also
binds loopback. Both must stay that way unless broker auth + ACL and HTTP auth
are in place.

## 🔌 USB instruments and MIDI: use `--hardware`

A container sees no host hardware by default — no `/dev/snd`, no `/dev/bus/usb`.
The MIDI agent enumerates zero devices and USB (USBTMC) instruments are
invisible, however firmly they are plugged in. Neither failure is loud.

`--hardware` bind-mounts `/dev/snd` and `/dev/bus/usb` and adds cgroup rules for
majors 116 (ALSA), 189 (usbfs) and 180 (usbtmc), plus the `audio` group.

It bind-mounts the **bus** rather than listing `devices:` deliberately: a
`devices:` entry is resolved once at container start, so hot-plugged instruments
never appear and a device absent at boot stops the container from starting at
all. Bind-mounting supports hot-plug, which is how a bench is actually used.

This is a real privilege increase, which is why it is opt-in — but it is far
narrower than `privileged: true`. Do not substitute that.

## Commands

```bash
python3 docker/launch.py            # start (default)
python3 docker/launch.py up --logs  # start and tail
python3 docker/launch.py status     # containers + endpoint health
python3 docker/launch.py logs       # tail
python3 docker/launch.py down       # stop
python3 docker/launch.py rebuild    # rebuild images from scratch, then start
python3 docker/launch.py reset      # stop AND delete the broker volume
```

Plain compose works too, if you prefer:

```bash
docker compose -f docker/docker-compose.yml up
```

The launcher adds one thing over raw compose: a **preflight** that checks Docker
is installed, the daemon is reachable, and the files compose references exist —
then fails with an instruction instead of a stack trace. A startup path that dies
confusingly on a stranger's machine is the problem this folder exists to solve.

## Why `mosquitto.conf` here differs from `../broker/mosquitto.conf`

The bare-metal config binds `127.0.0.1`, because on a host there is nothing else
between the broker and the network.

Inside a container, `127.0.0.1` means *the container's own loopback*, which the
orchestrator container cannot reach. So this config binds `0.0.0.0` and the
**compose port mapping** provides the confinement instead: every published port
is `127.0.0.1:<port>:<port>`, so nothing is reachable from off-host.

**The confinement lives in `docker-compose.yml`, not in the broker config.** If
you remove a host-IP prefix from a port mapping, you have exposed an anonymous
broker that can drive lab hardware.

## Before exposing anything on a network

The bus is not a passive transport. Publishing to the VISA `Write` topics makes
the orchestrator execute SCPI on real instruments, and the HTTP API can write
panel files. Both are unauthenticated today.

To expose on a LAN you need **all** of:

1. Broker auth — `password_file`, `allow_anonymous false`
2. An ACL so an authenticated UI client still cannot publish to `…/Write` —
   a ready-made policy ships as [`../broker/acl.example`](../broker/acl.example)
3. Authentication in front of the HTTP API's mutating routes
4. Only then widen the port mappings

Do not do step 4 on its own.

## State

Retained MQTT topics are the system's state store, so the broker's data lives in
a named volume (`broker-data`) and survives `down`. `reset` deletes it — that is
real data loss, not a cache clear, which is why it is a separate command.

`../FrontEnd/Gui_Frames/` is bind-mounted, so panels you edit in the WYSIWYG
editor land on your disk and show up in `git diff`.

## Running without Docker

See the collapsed *"Running without Docker"* section in the
[root README](../README.md#-quick-start). It needs Rust 1.94, Python 3, and a
mosquitto broker on the host.
