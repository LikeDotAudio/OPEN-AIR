#pragma once

#include <iostream>
#include <sstream>
#include <time.h>
#include <fstream>
#include <filesystem>

#ifdef _WIN32
#include <windows.h>
#endif

#define LOG_DEBUG 1

namespace APKet {
    
    class Logger {
        
        public:

            static Logger& getInstance() {
                static Logger instance;
                return instance;
            }

            Logger(Logger const&) = delete;
            void operator=(Logger const&) = delete;

            void logDebug(const std::string message) {
                #ifdef LOG_DEBUG
                    this->log("[DEBUG]", message);
                #endif
            }

            void logInfo(const std::string message) {
                this->log("[INFO]", message);
            }

            void logWarning(const std::string message) {
                this->log("[WARNING]", message);
            }

            void logWarning(const std::string message, const std::exception& e) {
                this->log("[WARNING]", message);
                this->log("[WARNING]", e.what());
            }

            void logError(const std::string message) {
                this->log("[ERROR]", message);
            }

            void logError(const std::string message, const std::exception& e) {
                this->log("[ERROR]", message);
                this->log("[ERROR]", e.what());
            }

        private:

            std::string logfile_path;

            Logger() {

                time_t now = time(0);
                char* dt = ctime(&now);
                tm *ltm = localtime(&now);

                std::stringstream dateStream;
                dateStream << 1900 + ltm->tm_year; // Year
                dateStream << '-';
                dateStream << 1 + ltm->tm_mon;    // Month
                dateStream << '-';
                dateStream << ltm->tm_mday;        // Day
                std::string currentDate = dateStream.str();
                
                std::filesystem::create_directory("ember-csv-logs");
                logfile_path = "ember-csv-logs\\log_" + currentDate + ".log";
            }

            void log(std::string prefix, std::string message) {

                std::string log_message = prefix + " " + message; 
                std::cout << log_message << std::endl;

                std::ofstream file(logfile_path, std::ofstream::app);

                if(!file.is_open()) {
                    std::cout << "Could not log file.\n";
                }

                file << log_message;
                file << "\n";

                file.close();

            }
    };
}