fn main() {
    let mut config = prost_build::Config::new();
    config.compile_protos(
        &[
            "../oaComProtocols/oaComSMPTE2138/st2138-a-main/interface/proto/menu.proto",
            "../oaComProtocols/oaComSMPTE2138/st2138-a-main/interface/proto/device.proto",
            "../oaComProtocols/oaComSMPTE2138/st2138-a-main/interface/proto/service.proto",
            "../oaComProtocols/oaComSMPTE2138/st2138-a-main/interface/proto/language.proto",
            "../oaComProtocols/oaComSMPTE2138/st2138-a-main/interface/proto/externalobject.proto",
            "../oaComProtocols/oaComSMPTE2138/st2138-a-main/interface/proto/param.proto",
            "../oaComProtocols/oaComSMPTE2138/st2138-a-main/interface/proto/constraint.proto",
        ],
        &["../oaComProtocols/oaComSMPTE2138/st2138-a-main/interface/proto/"],
    ).expect("Failed to compile ST2138 protobuf files");
}
