#pragma once

#include <memory>
#include <string>
#include <vector>

#include "GlowDevice.hpp"
#include "subscriptions/PathSubscription.hpp"
#include "device/HUIChannel.hpp"
#include "ember/glow/GlowQualifiedNode.hpp"
#include "csv-parser/csv.h"
#include "csv/CSV.hpp"
#include "Config.hpp"
#include "subscriptions/Subscription.hpp"
#include "types.hpp"

#define NUM_CHANNELS 8

namespace APKet {

    class HUIDevice : public GlowDevice {
        public:

            HUIDevice(std::vector<u32> path);

            ~HUIDevice();

            HUIDevice(const HUIDevice&) = delete;

            virtual libember::dom::Node* getNode(std::vector<u32> path, u32 depth) override;
        
        private:

            u32 number;

            std::string deviceName;

            CSV& csv;
            
    };

}