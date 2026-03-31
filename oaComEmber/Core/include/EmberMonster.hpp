#pragma once

#include <memory>
#include <vector>

#include "ember/glow/GlowRootElementCollection.hpp"
#include "ember/glow/CommandType.hpp"
#include "ember/glow/GlowContainer.hpp"
#include "ember/util/OctetStream.hpp"
#include "ember/glow/GlowParameter.hpp"
#include "ember/glow/GlowParameterBase.hpp"
#include "ember/glow/GlowType.hpp"

#include "communication/connection/Sender.hpp"
#include "communication/EmberHeader.hpp"
#include "csv/CSV.hpp"
#include "subscriptions/PathSubscription.hpp"
#include "GlowParser.hpp"
#include "GlowDevice.hpp"
#include "subscriptions/Subscription.hpp"




namespace APKet {

    class S101PacketHandler {

        public:

            S101PacketHandler() = delete;

            ~S101PacketHandler();

            S101PacketHandler(std::shared_ptr<StreamSender> sender, std::shared_ptr<GlowDevice> glow_device);

            /*
             * This function takes in a complete packet (see ember doc page 82 under Flags as of 2023-12-21)
             */
            void feed_packet(libember::util::OctetStream complete_packet);

            /*
             * Removes all owned subscribers on glow_device
             */
            void cleanUp();

        protected:

            std::shared_ptr<StreamSender> sender;

            std::shared_ptr<GlowDevice> glow_device;

            void handleEmberPacket(APKet::EmberPacketHeader& header, libember::util::OctetStream ember_stream);

            void sendKeepAliveResp();

            libember::util::OctetStream ember_buffer;


            class DeviceSubscriber : public PathSubscriber {

                public: 

                    DeviceSubscriber(S101PacketHandler * interpreter);

                    void onUpdate(std::vector<u32> path) override;
                    
                private:

                    S101PacketHandler * interpreter;

            };

        private:

            std::shared_ptr<PathSubscriber> subscriber;

            void handleGlow(std::unique_ptr<libember::glow::GlowRootElementCollection>& collection);

            void handleSubscribe(libember::glow::GlowContainer* container);

    };
}