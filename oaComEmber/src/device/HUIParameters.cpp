#include "device/HUIParameters.hpp"

APKet::HUIParameter::HUIParameter(std::vector<u32> path, CSV& csv, std::string hui, u32 channel_num) :
    GlowDevice(path),
    channel_num(channel_num),
    hui(hui),
    csv(csv)
{
    this->csv.addSubscriber(std::make_unique<CSVHUIValueSubscriber>(this));
}

void APKet::HUIParameter::CSVHUIValueSubscriber::onUpdate() {
    if (this->hui_parameter->updateValue()) {
        for (auto& subscriber : this->hui_parameter->subscribers) {
            subscriber->onUpdate(this->hui_parameter->path);
        }
    }
}

bool APKet::HUIParameter::updateValue() {
    auto new_value = this->csv.getTableRow(this->hui).at(this->channel_num - 1);
    if (new_value != this->value) {
        this->value = new_value;
        return true;
    }
    return false;
}

libember::dom::Node* APKet::HUIIntValue::getNode(std::vector<u32> path, u32 depth) {
    if (path.size() == 0) {
        auto* param_node = new libember::glow::GlowParameter(this->path.at(this->path.size() - 1));
        param_node->setIdentifier(hui);
        try {
            param_node->setValue(std::stoi(this->value));
        } catch (std::invalid_argument e) {
            APKet::Logger::getInstance().logError("Invalid integer \"" + this->value + "\" read from " + this->hui + " in csv", e);
        }
        return param_node;
    }
    if (path.size() == depth) {
        libember::ber::ObjectIdentifier id = libember::ber::ObjectIdentifier();
        for (auto dir : this->path) id.push_back(dir);
        auto* param_node = new libember::glow::GlowQualifiedParameter(id);
        param_node->setIdentifier(hui);
        try {
            param_node->setValue(std::stoi(this->value));
        } catch (std::invalid_argument e) {
            APKet::Logger::getInstance().logError("Invalid integer \"" + this->value + "\" read from " + this->hui + " in csv", e);
        }
        return param_node;
    }
    throw std::runtime_error("No node at path.");
};

libember::dom::Node* APKet::HUIButtonActive::getNode(std::vector<u32> path, u32 depth) {
    if (path.size() == 0) {
        auto* param_node = new libember::glow::GlowParameter(this->path.at(this->path.size() - 1));
        param_node->setIdentifier(hui);
        param_node->setValue(this->value.compare("0") != 0);
        return param_node;
    }
    if (path.size() == depth) {
        libember::ber::ObjectIdentifier id = libember::ber::ObjectIdentifier();
        for (auto dir : this->path) id.push_back(dir);
        auto* param_node = new libember::glow::GlowQualifiedParameter(id);
        param_node->setIdentifier(hui);
        param_node->setValue(this->value.compare("0") != 0);
        return param_node;
    }
    throw std::runtime_error("No node at path.");
};