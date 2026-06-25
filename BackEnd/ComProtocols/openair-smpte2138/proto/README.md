# ST2138 protobuf sources

`build.rs` compiles these with `prost-build` (only under the `python` feature)
into `OUT_DIR/st2138.rs`, which `src/oa_st2138_codec_rs/mod.rs` includes via
`include!(concat!(env!("OUT_DIR"), "/st2138.rs"))`.

Drop the ST2138 `.proto` files here (they declare `package st2138;`):

- menu.proto
- device.proto
- service.proto
- language.proto
- externalobject.proto
- param.proto
- constraint.proto

These were previously referenced from a now-removed
`../oaComProtocols/oaComSMPTE2138/st2138-a-main/interface/proto/` path. Once
restored here, `cargo check -p openair-smpte2138 --features python` and a full
`oaRustCore` build will succeed.
