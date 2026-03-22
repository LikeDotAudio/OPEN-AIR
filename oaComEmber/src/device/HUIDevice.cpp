#include "device/HUIDevice.hpp"
#include <memory>
#include <vector>
#include "GlowDevice.hpp"
#include "csv/CSV.hpp"
#include "device/HUIChannel.hpp"
#include "ember/glow/GlowNode.hpp"
#include "subscriptions/PathSubscription.hpp"

APKet::HUIDevice::HUIDevice(std::vector<u32> path) : 
    APKet::GlowDevice(path),
    number(path.at(path.size() - 1)),
    deviceName("Control Surface " + std::to_string(number)),
    csv(CSVCollection::getInstance().getCSV(number))
{

    for (int i = 1; i < NUM_CHANNELS + 1; i++) {
        auto new_path = std::vector<u32>(this->path);
        new_path.push_back(i);
        this->children.push_back(std::make_unique<HUIChannel>(std::vector<u32>(new_path), this->csv));
    }

}

APKet::HUIDevice::~HUIDevice() {}

libember::dom::Node* APKet::HUIDevice::getNode(std::vector<u32> path, u32 depth) {
    if (path.size() == 0) {
        auto* device_node = new libember::glow::GlowNode(this->number);
        device_node->setIdentifier(this->deviceName);
        device_node->setIsOnline(true);
        return device_node;
    }
    if (path.size() == depth) {
        auto id = libember::ber::ObjectIdentifier();
        for (auto dir : path) id.push_back(dir);
        auto* device_node = new libember::glow::GlowQualifiedNode(id);
        device_node->setIdentifier(this->deviceName);
        device_node->setIsOnline(true);
        return device_node;
    } else {
        auto& channel = this->children.at(path.at(depth) - 1);
        return channel->getNode(path, depth + 1);
    }
}