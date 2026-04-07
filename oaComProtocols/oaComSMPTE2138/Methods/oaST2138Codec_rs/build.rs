fn main() {
    let mut config = prost_build::Config::new();
    config.compile_protos(
        &[
            "../../st2138-a-main/interface/proto/constraint.proto",
            "../../st2138-a-main/interface/proto/device.proto",
            "../../st2138-a-main/interface/proto/externalobject.proto",
            "../../st2138-a-main/interface/proto/language.proto",
            "../../st2138-a-main/interface/proto/menu.proto",
            "../../st2138-a-main/interface/proto/param.proto",
            "../../st2138-a-main/interface/proto/service.proto",
        ],
        &["../../st2138-a-main/interface/proto/"],
    ).unwrap();
}
