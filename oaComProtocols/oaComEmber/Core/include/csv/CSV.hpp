#pragma once

#include <array>
#include <cstddef>
#include <map>
#include <memory>
#include <thread>
#include <vector>
#include <chrono>
#include <iostream>

#include "ember/util/OctetStream.hpp"

#include "communication/connection/EmberClient.hpp"
#include "communication/connection/Sender.hpp"
#include "communication/EmberHeader.hpp"
#include "communication/connection/Sender.hpp"
#include "subscriptions/Subscription.hpp"
#include "csv-parser/csv.h"
#include "csv/CSV.hpp"
#include "Config.hpp"
#include "types.hpp"

#define CSV_COL_COUNT 10

namespace APKet {

    class CSV {
        
        public:

            CSV(std::string path);

            CSV(const CSV&) = default;

            CSV& operator=(CSV&& other) noexcept = default;

            void addSubscriber(std::shared_ptr<Subscriber> subscription);

            void removeSubscriber(const Subscriber& subscription_to_remove);

            void notifySubscribers();

            void updateTable();

            std::array<std::string, CSV_COL_COUNT> getTableRow(std::string hui) const;

            std::string getPath() const;

        private:

            std::string filepath;

            std::vector<std::shared_ptr<Subscriber>> subscriptions;

            std::map<std::string, std::array<std::string, CSV_COL_COUNT>> table;

    };

    class CSVCollection {

        public:

            static CSVCollection& getInstance();

            std::vector<CSV>& getCSVList();

            CSV& getCSV(u32 number);

            u32 getCSVCount();

        private:

            std::vector<CSV> csvs;

            CSVCollection();

    };

}
