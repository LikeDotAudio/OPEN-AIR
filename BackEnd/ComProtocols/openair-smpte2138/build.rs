fn main() {
    // oa_st2138_codec_rs (the pyo3 ST2138 codec) is only compiled under the
    // `python` feature, and only it needs the generated protobuf bindings, so
    // only then do we run prost-build. Without the feature this crate builds as
    // a plain stub (keeps the ComProtocols workspace building).
    if std::env::var("CARGO_FEATURE_PYTHON").is_err() {
        return;
    }
    // Place the ST2138 .proto files under openair-smpte2138/proto/.
    let proto_root = "proto";
    let protos = [
        "proto/menu.proto",
        "proto/device.proto",
        "proto/service.proto",
        "proto/language.proto",
        "proto/externalobject.proto",
        "proto/param.proto",
        "proto/constraint.proto",
    ];
    prost_build::Config::new()
        .compile_protos(&protos, &[proto_root])
        .expect("Failed to compile ST2138 protobufs (place .proto files in openair-smpte2138/proto/)");
}
