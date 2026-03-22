#include "device/HUIChannel.hpp"
#include <memory>
#include <stdexcept>
#include <vector>
#include "Logger.hpp"
#include "csv/CSV.hpp"
#include "ember/glow/GlowNode.hpp"
#include "ember/glow/GlowQualifiedParameter.hpp"
#include "device/HUIParameters.hpp"
#include "subscriptions/Subscription.hpp"
#include "types.hpp"

APKet::HUIChannel::HUIChannel(std::vector<u32> path, CSV& csv) : 
    APKet::GlowDevice(path),
    channel_num(path.at(path.size() - 1))
{
    // this->csv.addSubscriber(std::shared_ptr<MidiChannelSubscription>(new MidiChannelSubscription(this)));
    path.push_back(1);
    this->children.push_back(std::make_unique<HUIIntValue>(path, csv, "Fader", channel_num));
    path.at(path.size() - 1) = 2;
    this->children.push_back(std::make_unique<HUIButtonActive>(path, csv, "Record Active", channel_num));
    path.at(path.size() - 1) = 3;
    this->children.push_back(std::make_unique<HUIButtonActive>(path, csv, "Solo Active", channel_num));
    path.at(path.size() - 1) = 4;
    this->children.push_back(std::make_unique<HUIButtonActive>(path, csv, "Mute Active", channel_num));
    path.at(path.size() - 1) = 5;
    this->children.push_back(std::make_unique<HUIButtonActive>(path, csv, "Select Active", channel_num));
    path.at(path.size() - 1) = 6;
    this->children.push_back(std::make_unique<HUIIntValue>(path, csv, "Knob State", channel_num));
}

libember::dom::Node* APKet::HUIChannel::getNode(std::vector<u32> path, u32 depth) {
    if (path.size() == 0) {
        auto* channel_node = new libember::glow::GlowNode(this->channel_num);
        channel_node->setIdentifier("Channel " + std::to_string(channel_num));
        channel_node->setIsOnline(true);

        return channel_node;
    }
    if (path.size() == depth) {
        libember::ber::ObjectIdentifier id = libember::ber::ObjectIdentifier();
        for (auto dir : this->path) id.push_back(dir);
        auto* channel_node = new libember::glow::GlowQualifiedNode(id);
        channel_node->setIdentifier("Channel " + std::to_string(channel_num));
        channel_node->setIsOnline(true);

        return channel_node;
    } else {
        auto& channel = this->children.at(path.at(depth) - 1);
        return channel->getNode(path, depth + 1);
    }
}
