use ini::Ini;
use std::error::Error;

pub struct Config {
    pub enabled: bool,
    pub topic: String,
    #[allow(dead_code)]
    pub topic_listen: String,
    pub topic_publish: String,
    pub topic_ignore: String,
    /// Send the short-form spelling of a command where the table carries one.
    /// The 6060B manual: *"The short form provides the fastest program
    /// execution."* Off by default — the long form is what the tables were
    /// swept as and what a log is readable in.
    pub prefer_short_scpi: bool,
}

pub fn load_config(path: &str) -> Result<Config, Box<dyn Error>> {
    let conf = Ini::load_from_file(path)?;
    let section = conf.section(Some("yak")).ok_or("Missing [yak] section in config.ini")?;
    
    let enabled = section.get("enabled").unwrap_or("false").parse::<bool>().unwrap_or(false);
    let topic = section.get("topic").unwrap_or("OpenAir/System/Protocols/yak").to_string();
    let topic_listen = section.get("topic_listen").unwrap_or("OpenAir/System/Protocols/yak/sub").to_string();
    let topic_publish = section.get("topic_publish").unwrap_or("OpenAir/System/Protocols/yak/pub").to_string();
    let topic_ignore = section.get("topic_ignore").unwrap_or("OpenAir/System/Protocols/yak/ignore").to_string();
    let prefer_short_scpi = section.get("prefer_short_scpi")
        .unwrap_or("false").parse::<bool>().unwrap_or(false);

    Ok(Config {
        enabled,
        topic,
        topic_listen,
        topic_publish,
        topic_ignore,
        prefer_short_scpi,
    })
}
