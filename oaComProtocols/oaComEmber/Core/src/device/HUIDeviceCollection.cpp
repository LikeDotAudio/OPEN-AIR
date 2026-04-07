#include "device/HUIDeviceCollection.hpp"
#include <initializer_list>
#include <memory>
#include "device/HUIDevice.hpp"
#include "ember/glow/GlowParameter.hpp"
#include "subscriptions/PathSubscription.hpp"

APKet::HUIDeviceCollection::HUIDeviceCollection(u32 device_count) : APKet::GlowDevice({}) {
    for(u32 i = 1; i <= device_count; i++) {
        this->children.push_back(std::make_unique<HUIDevice>(std::vector<u32>({i})));
    }
}

libember::dom::Node* APKet::HUIDeviceCollection::getNode(std::vector<u32> path, u32 depth) {

    if (path.size() == depth) {
        return new libember::glow::GlowRootElementCollection();
    } else {
        auto& device = this->children.at(path.at(0) - 1);
        return device->getNode(path, depth + 1);
    }

}