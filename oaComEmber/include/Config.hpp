#pragma once

#include <map>
#include <string>
#include <vector>
#include <cstddef>
#include <fstream>

#include <types.hpp>


namespace APKet {
    static const char CONFIG_PATH[] = "config.ini";

    class Config {
        public:

            static Config& getInstance();

            std::vector<std::string> getPaths();

            u16 getPort();

        private:
            
            Config();

            ~Config();

            // static Config instance;

            std::vector<std::string> csv_paths;

            u16 portnum;

    };
}
