#pragma once

#include "ember/util/OctetStream.hpp"

namespace APKet {
    class StreamSender {
        public:

            virtual ~StreamSender() = default;

            virtual void send(const libember::util::OctetStream& stream) const = 0;

            virtual std::string getIPAddress() const = 0;
    };
}