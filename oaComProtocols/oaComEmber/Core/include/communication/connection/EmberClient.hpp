#pragma once

#include <memory>
#include <vector>

#include "ember/glow/GlowRootElementCollection.hpp"
#include "ember/util/OctetStream.hpp"

#include "communication/connection/socket.hpp"
#include "communication/connection/Sender.hpp"
#include "communication/EmberHeader.hpp"
#include "communication/S101Packager.hpp"
#include "s101/StreamDecoder.hpp"
#include "types.hpp"

namespace APKet {

    /*
     * A Class representing a client that communicates using the ember protocol.
     */

    class EmberClient : public StreamSender {

        public:

            EmberClient(i32 fd, struct sockaddr_in addr);

            EmberClient(APKet::ClientConnection connection);

            i32 getFD() { return this->connection.getFD(); }

            std::string getIPAddress() const override { return this->connection.getIPAddress(); }

            void send(const libember::util::OctetStream& stream) const override;

            // void send(const APKet::EmberHeader& header) const;

            // void send(const APKet::EmberHeader& header, const libember::glow::GlowRootElementCollection* collection) const;

            /*
             * Reads a single ember packet
             */
            libember::util::OctetStream read();

            bool bufferIsEmpty();
        
        protected:

            ClientConnection connection;

            libs101::StreamDecoder<unsigned char> decoder;

            static bool appendMessage(libember::ber::Octets::const_iterator first, libember::ber::Octets::const_iterator last, std::vector<libember::util::OctetStream*>* messages);
        
        private:

            std::vector<libember::util::OctetStream> read_buffer;
            
            libember::util::OctetStream pop_buffer() {
                libember::util::OctetStream message = this->read_buffer[0];
                this->read_buffer.erase(this->read_buffer.begin());
                return message;
            };

    };

}