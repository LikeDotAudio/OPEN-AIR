#include "main.hpp"
#include <iostream>
#include <fstream>

int main() {

    APKet::Config& config = APKet::Config::getInstance();

    std::shared_ptr<APKet::GlowDevice> midi_collection = std::dynamic_pointer_cast<APKet::GlowDevice>(std::make_shared<APKet::HUIDeviceCollection>(config.getPaths().size()));

    APKet::EmbServer server = APKet::EmbServer(midi_collection);

    auto stop_predicate = []() { // Will return true if ready to stop the service
        return false;
    };
    try {
        server.listen(config.getPort(), stop_predicate);
    } catch (std::runtime_error e) {
        APKet::Logger::getInstance().logError("Error while opening socket", e);
    }
}