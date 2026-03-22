#pragma once

#include <array>
#include <memory>
#include <tuple>
#include <vector>
#include <string>

#include "csv/CSV.hpp"
#include "ember/glow/GlowNode.hpp"
#include "ember/glow/GlowQualifiedNode.hpp"
#include "ember/glow/GlowParameter.hpp"
#include "GlowDevice.hpp"
#include "subscriptions/Subscription.hpp"
#include "types.hpp"
#include "subscriptions/PathSubscription.hpp"

namespace APKet {

    class HUIChannel : public GlowDevice {

        public:

            HUIChannel(std::vector<u32> path, CSV& csv);

            HUIChannel(const HUIChannel&) = delete;

            libember::dom::Node* getNode(std::vector<u32> path, u32 depth) override;

        private:

            u32 channel_num;

    };

}
        //     std::vector<libember::dom::Node*> getChildren(std::vector<u32> path) override;

        //     void addSubscription(std::shared_ptr<PathSubscriber> subscriber, std::vector<u32> path, bool add_to_children) override;

        //     void removeSubscription(std::shared_ptr<PathSubscriber>& subscriber_to_remove, std::vector<u32> path, bool recursive) override;

        //     class MidiChannelSubscription : public Subscriber {

        //         public:

        //             MidiChannelSubscription(HUIChannel* midi_channel) : midi_channel(midi_channel) {};

        //             ~MidiChannelSubscription() = default;
                    
        //             void onUpdate() override;

        //             virtual bool operator==(const Subscriber& other) const override { return &other == this; }

        //         private:

        //             template <class TypeValue>
        //             void conditionallyUpdate(TypeValue& value, TypeValue new_value, std::vector<std::shared_ptr<PathSubscriber>> subscribers_list, u32 num);

        //             HUIChannel* midi_channel;
                
        //     };

        // private:

        //     u32 channel_num;
        //     std::string channel_name;

        //     u8 knob_pos;
        //     bool record;
        //     bool solo;
        //     bool mute;
        //     bool select;
        //     i16 fader_level;

        //     std::array<std::vector<std::shared_ptr<PathSubscriber>>, 6> param_subscribers;

        //     CSV& csv;