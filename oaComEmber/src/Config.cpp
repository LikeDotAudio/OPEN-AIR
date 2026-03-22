#include "Config.hpp"
#include <iostream>
#include "Logger.hpp"

// APKet::Config APKet::Config::instance;

APKet::Config::Config() {

    this->portnum = 9000;

    std::ifstream file = std::ifstream(APKet::CONFIG_PATH);
    if (!file.is_open()) {
        // throw std::runtime_error("Failed to open config file");
        APKet::Logger::getInstance().logError("Could not find config file.");
        std::exit(1);
    }
    std::string line;

    APKet::Logger::getInstance().logDebug("Parsing Config File");

    while (std::getline(file, line)) {
        size_t pos = line.find(';');
        if (pos != std::string::npos) {
            line.erase(pos);
        }

        line.erase(0, line.find_first_not_of(" \t\r\n"));
        line.erase(line.find_last_not_of(" \t\r\n") + 1);

        if (!line.empty() && line[0] != '[') {
            std::string key = line.substr(0, line.find('='));
            key.erase(0, key.find_first_not_of(" \t\r\n"));
            key.erase(key.find_last_not_of(" \t\r\n") + 1);

            std::string value = line.substr(line.find('=') + 1);
            value.erase(0, value.find_first_not_of(" \t\r\n"));
            value.erase(value.find_last_not_of(" \t\r\n") + 1);

            if (key.compare("CSV_PATHS") == 0) {
                size_t sub1 = 0;
                size_t sub2;
                std::string substr;
                while ((sub2 = value.find("|", sub1)) != std::string::npos) {
                    this->csv_paths.push_back(value.substr(sub1, sub2 - sub1));
                    sub1 = sub2 + 1; // Skip the |
                }
                this->csv_paths.push_back(value.substr(sub1));
            }

            if (key.compare("PORTNUM") == 0) {
                try {
                    this->portnum = stoi(value);
                } catch (std::invalid_argument e) {
                    APKet::Logger::getInstance().logError("Could not read portnum in config. Using default 9000", e);
                }
            }
        }
    }
}

APKet::Config::~Config() {}

APKet::Config& APKet::Config::getInstance() {
    
    APKet::Logger::getInstance().logDebug("Getting Config Instance");
    static Config instance;
    return instance;
}

std::vector<std::string> APKet::Config::getPaths() {
    return this->csv_paths;
}

u16 APKet::Config::getPort() {
    return this->portnum;
}