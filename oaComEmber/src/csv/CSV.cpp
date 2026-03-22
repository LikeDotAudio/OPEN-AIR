#include "csv/CSV.hpp"
#include <algorithm>
#include <array>
#include <stdexcept>
#include <string>
#include "Logger.hpp"
#include "csv-parser/csv.h"
#include "subscriptions/PathSubscription.hpp"

APKet::CSV::CSV(std::string path) : filepath(path), table() {

    // this->filepath = path;
    // this->table = std::vector<std::vector<std::string>>();

    io::CSVReader<CSV_COL_COUNT> reader(this->filepath);

    reader.read_header(io::ignore_missing_column, "one", "two", "three", "four", "five", "six", "seven", "eight", "id", "hui");

    std::string hui = "";
    std::string id = "";
    std::string data[10];
    while (reader.read_row(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], id, hui)) {
        std::array<std::string, CSV_COL_COUNT> row = { data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], id, hui };
        if (hui.compare("") != 0) this->table.insert({ hui, row });
    }
}

void APKet::CSV::addSubscriber(std::shared_ptr<APKet::Subscriber> subscription) {
    subscriptions.push_back(std::move(subscription));
}

void APKet::CSV::removeSubscriber(const APKet::Subscriber& subscription_to_remove) {
    
    auto subscription = this->subscriptions.begin();
    while (subscription < subscriptions.end()) {

        if (**subscription == subscription_to_remove) {
            subscription = this->subscriptions.erase(subscription);
        }
        else {
            subscription++;
        }

    }
}

std::array<std::string, CSV_COL_COUNT> APKet::CSV::getTableRow(std::string hui) const {
    return this->table.at(hui);
}

std::string APKet::CSV::getPath() const {
    return this->filepath;
}

// if (path.size() <= (**subscription).getPath().size()) {



//     bool equals = true;
//     for (i32 i = 0; i < (i32)path.size(); i++) {
//         if (path.at(i) != (**subscription).getPath().at(i)) {
//             equals = false;
//             subscription++;
//             break;
//         }
//     }
//     if (equals) this->subscriptions.erase(subscription);
// } else {
//     subscription++;
// }

// void APKet::CSV::startPolling() {
//     this->polling_thread = std::thread([this] { this->pollUntilStop(); });
// }

// void APKet::CSV::stopPolling() {
//     this->poll_stop_flag = true;
//     this->polling_thread.join();
// }

// void APKet::CSV::pollUntilStop() {
//     while (!this->poll_stop_flag) {
//         updateTable();
//         notifySubscribers();
//         std::chrono::microseconds duration(500 * 1000);
//         std::this_thread::sleep_for(duration);
//     }
// }

void APKet::CSV::updateTable() {

    try {

        io::CSVReader<CSV_COL_COUNT> reader(this->filepath);

        reader.read_header(io::ignore_missing_column, "one", "two", "three", "four", "five", "six", "seven", "eight", "id", "hui");

        std::string hui = "";
        std::string id;
        std::string data[10];
        while (reader.read_row(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], id, hui)) {
            std::array<std::string, CSV_COL_COUNT> row = { data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], id, hui };
            if (hui.compare("") != 0) this->table.insert_or_assign(hui, row);
        }

    }
    catch (io::error::base& e) {
        APKet::Logger::getInstance().logWarning("Could not read csv to update table: ", e);
    }
}

void APKet::CSV::notifySubscribers() {
    for (auto subscriber : subscriptions) {
        subscriber->onUpdate();
        // auto devicesub = std::dynamic_pointer_cast<HUIDevice::MidiDeviceSubscription>(subscriber);
        // subscriber->onUpdate();
    }
}

APKet::CSVCollection& APKet::CSVCollection::getInstance() {
    static CSVCollection instance;
    return instance;
}

std::vector<APKet::CSV>& APKet::CSVCollection::getCSVList() {
    return this->csvs;
}

APKet::CSV& APKet::CSVCollection::getCSV(u32 number) {
    return this->csvs.at(number - 1);
}

u32 APKet::CSVCollection::getCSVCount() {
    return this->csvs.size();
}

APKet::CSVCollection::CSVCollection() {

    this->csvs = std::vector<APKet::CSV>();

    APKet::Config& config = APKet::Config::getInstance();

    std::vector<std::string> csv_paths = config.getPaths();

    for (auto path : csv_paths) {
        try {
            this->csvs.emplace_back(path);
        }
        catch (std::exception& e) {
            APKet::Logger::getInstance().logWarning("Could not create CSV object for path " + path + ": ", e);
        }
    }

}

// void APKet::CSVCollection::startPolling() {
//     for (auto& csv : this->csvs) csv.startPolling();
// }

// void APKet::CSVCollection::stopPolling() {
//     for (auto& csv : this->csvs) csv.stopPolling();
// }

