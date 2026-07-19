# OPEN-AIR — orchestrator image.
#
# Build stage compiles the Rust orchestrator; the runtime stage carries only what
# is needed to run it, plus the Python the VISA probe path shells out to.
#
#   python3 docker/launch.py
#   docker compose -f docker/docker-compose.yml up
#
# NOTE: the build context is the REPO ROOT (set in docker-compose.yml), not this
# directory — the Rust workspaces and FrontEnd/ live up there. All COPY paths
# below are therefore repo-root-relative.
#
# The compose file is the documented startup path. It exists because the previous
# answer to "how do I run this" was seven commands that omitted the frontend
# toolchain entirely, which made every evaluation cost the author's time.

# ---------- build ----------
FROM rust:1.94-bookworm AS build

# midir (MIDI) needs ALSA headers; pkg-config finds them.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libasound2-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Copy the two Cargo workspaces plus the contracts crate they depend on by path.
COPY rust-toolchain.toml ./
COPY contracts/rust        ./contracts/rust
COPY BackEnd/Core          ./BackEnd/Core
COPY BackEnd/ComProtocols  ./BackEnd/ComProtocols

RUN cargo build --release \
      --manifest-path BackEnd/Core/Cargo.toml \
      -p open-air-orchestrator

# ---------- runtime ----------
FROM debian:bookworm-slim AS runtime

# pyvisa/pyvisa-py are required: the orchestrator shells out to python3 to probe
# instruments (*IDN?) and to run SCPI writes. Without them every probe fails and
# the Discovered tab comes up empty.
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip libasound2 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY Deployment/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

WORKDIR /app

COPY --from=build /src/BackEnd/Core/target/release/open-air-orchestrator /usr/local/bin/

# AVDECC (AVB/Milan) is a Layer 2 protocol: it needs raw packet capture, which
# means CAP_NET_RAW. The container runs as the host user (see `user:` in
# docker-compose.yml) so it is NOT root and cannot inherit the capability from
# the container's bounding set alone — FILE capabilities are what carry it to a
# non-root process. `+eip` puts it in the effective, inheritable and permitted
# sets so the binary has it the moment it starts.
#
# compose must still grant NET_RAW/NET_ADMIN via `cap_add`, or the bounding set
# clamps this away. Both halves are required; either alone silently fails and
# the AVB agent reports "raw packet capture denied".
# cap_net_bind_service is for PTP, not AVDECC: PTPv1/v2 arrive on UDP ports 319
# and 320, which are below 1024 and therefore privileged. Without it the PTP
# agent reports "partial" — it still hears gPTP over raw Ethernet, but every
# UDP-carried clock is invisible, which looks exactly like a network with no
# PTPv1/v2 on it.
RUN apt-get update && apt-get install -y --no-install-recommends libcap2-bin \
    && setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip /usr/local/bin/open-air-orchestrator \
    && apt-get purge -y libcap2-bin && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# The served UI and the authored panel tree. Gui_Frames is bind-mounted in
# compose so edits from the WYSIWYG editor land on the host, not in the layer.
COPY FrontEnd   ./FrontEnd
COPY Deployment ./Deployment

EXPOSE 8000

# SECURITY: bind 0.0.0.0 *inside the container only*. Compose publishes the port
# to 127.0.0.1 on the host, so the service is not exposed to the network. The
# container boundary is what makes this safe — do not copy this flag to a
# bare-metal run. See cli.rs and broker/mosquitto.conf.
ENV OPENAIR_BIND=0.0.0.0

CMD ["sh", "-c", "open-air-orchestrator --bind ${OPENAIR_BIND} --port 8000 --no-build --no-browser"]
