#pragma once

#include <iostream>
#include <memory>
#include <vector>
#include <stdexcept>

#include "ember/util/OctetStream.hpp"
#include "ember/glow/GlowDtd.hpp"
#include "ember/util/OctetStream.hpp"
#include "ember/util/detail/StreamBufferIterator.hpp"
#include "types.hpp"

#define BASE_HEADER_SIZE 4
#define EMBER_HEADER_SIZE 7

namespace APKet {

    enum message_type {
        EMBER = 0x0E,
    };

    enum command_type {
        EMBER_PACKET = 0x00,
        KEEP_ALIVE_REQ = 0x01,
        KEEP_ALIVE_RESP = 0x02,
    };

    enum flags {
        SINGLE_PACKET = 0xC0,
        FIRST_PACKET = 0x80,
        LAST_PACKET = 0x40,
        EMPTY_PACKET = 0x20,
        WITHIN_MULTI_PACKET = 0x00,
    };

    enum design_type_document {
        GLOW = 0x01,
    };

    enum header_indices {
        DEVICE_SLOT = 0,
        MESSAGE_TYPE = 1,
        COMMAND_TYPE = 2,
        VERSION = 3,
        FLAGS = 4,
        DESIGN_TYPE_DOCUMENT = 5,
        APP_BYTES = 6,
        MINOR_GLOW_VERSION = 7,
        MAJOR_GLOW_VERSION = 8,
    };


    class EmberHeader {

    public:

        virtual ~EmberHeader() = default;

        /* Adds the header to the stream */
        void wrapStream(libember::util::OctetStream &stream) const;

        void unwrapStream(libember::util::OctetStream &stream) const;

        /* Returns true if the header is valid */
        bool isValid() const;

        unsigned char getDeviceSlot() const;

        enum message_type getMessageType() const;

        enum command_type getCommandType() const;

        unsigned char getVersion() const;

    protected:

        /* Constructor */
        EmberHeader();

        /* Constructor */
        EmberHeader(libember::util::OctetStream &stream);

        std::vector<u8> header;

    };

    class EmberKeepAliveHeader : virtual public EmberHeader {
        
        public:

            EmberKeepAliveHeader();

            EmberKeepAliveHeader(libember::util::OctetStream &stream);

            // bool isValid() const override;
    
    };

    class EmberPacketHeader : virtual public EmberHeader {

        public:

            EmberPacketHeader();

            EmberPacketHeader(libember::util::OctetStream &stream);

            // bool isValid() const override;

            /* Returns true if the specified flag in the header is set */
            bool hasFlagSet(flags flag);

            enum flags getFlags() const;

            enum design_type_document getDTD() const;

            unsigned char getAppBytes() const;

            unsigned char getMinorGlowVersion() const;

            unsigned char getMajorGlowVersion() const;

    };


    class EmberHeaderFactory {

        public:

            EmberHeaderFactory();

            // bool isValid() const override;

            std::unique_ptr<EmberHeader> createHeader(libember::util::OctetStream &stream);

    };

}
