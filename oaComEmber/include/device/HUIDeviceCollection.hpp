#pragma once

#include <iostream>
#include <cstring>
#include <string>
#include <tuple>
#include <vector>
#include <algorithm>
#include <memory>

#include "ember/dom/Sequence.hpp"
#include "ember/glow/GlowRootElementCollection.hpp"
#include "ember/glow/GlowNode.hpp"
#include "ember/glow/GlowParameter.hpp"
#include "ember/glow/GlowQualifiedNode.hpp"
#include "ember/glow/GlowQualifiedParameter.hpp"
#include "ember/glow/GlowRootElementCollection.hpp"
#include "ember/dom/Node.hpp"

#include "device/HUIDevice.hpp"
#include "device/HUIChannel.hpp"
#include "subscriptions/PathSubscription.hpp"
#include "subscriptions/Subscription.hpp"
#include "csv-parser/csv.h"
#include "Config.hpp"
#include "types.hpp"
#include "GlowDevice.hpp"
#include "csv-parser/csv.h"


namespace APKet {
    
    /*
     * Implementation of GlowDevice for HUIDevices
     */
    class HUIDeviceCollection : public GlowDevice {

        public:

            HUIDeviceCollection(u32 device_count);

            ~HUIDeviceCollection() = default;

            libember::dom::Node* getNode(std::vector<u32> path, u32 depth) override;

    };
    
}
