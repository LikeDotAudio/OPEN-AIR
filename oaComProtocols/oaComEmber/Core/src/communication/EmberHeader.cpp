#include "communication/EmberHeader.hpp"

APKet::EmberHeader::EmberHeader() {}

APKet::EmberHeader::EmberHeader(libember::util::OctetStream& stream) {

    this->header.insert(this->header.end(), stream.begin(), std::next(stream.begin(), BASE_HEADER_SIZE));

}

void APKet::EmberHeader::wrapStream(libember::util::OctetStream& stream) const {
    libember::util::OctetStream stream_copy = libember::util::OctetStream(stream);
    stream.clear();
    stream.append(this->header.begin(), this->header.end());
    stream.append(stream_copy.begin(), stream_copy.end());
}

void APKet::EmberHeader::unwrapStream(libember::util::OctetStream& stream) const {
    stream.consume(this->header.size());
}

bool APKet::EmberHeader::isValid() const {

    if (this->getMessageType() != APKet::message_type::EMBER) {
        std::cout << "Invalid message type " << this->getMessageType() << std::endl;
        return false;
    }

    if (this->getVersion() != 1) {
        std::cout << "Invalid version" << std::endl;
        return false;
    }

    return true;
}


unsigned char APKet::EmberHeader::getDeviceSlot() const {
    return this->header[APKet::header_indices::DEVICE_SLOT];
}

enum APKet::message_type APKet::EmberHeader::getMessageType() const {
    return (enum APKet::message_type)this->header[APKet::header_indices::MESSAGE_TYPE];
}

enum APKet::command_type APKet::EmberHeader::getCommandType() const {
    return (enum APKet::command_type)this->header[APKet::header_indices::COMMAND_TYPE];
}

unsigned char APKet::EmberHeader::getVersion() const {
    return this->header[APKet::header_indices::VERSION];
}


// ===== EmberKeepAliveHeader =====

APKet::EmberKeepAliveHeader::EmberKeepAliveHeader() : EmberHeader() {
    this->header.push_back(0); // index 0
    this->header.push_back(APKet::message_type::EMBER); // index 1
    this->header.push_back(APKet::command_type::KEEP_ALIVE_RESP); // index 2
    this->header.push_back(1); // index 3
}

APKet::EmberKeepAliveHeader::EmberKeepAliveHeader(libember::util::OctetStream& stream) : EmberHeader(stream) {}

// ===== EmberPacketHeader =====

APKet::EmberPacketHeader::EmberPacketHeader() : EmberHeader() {
    this->header.push_back(0); // index 0
    this->header.push_back(APKet::message_type::EMBER); // index 1
    this->header.push_back(APKet::command_type::EMBER_PACKET); // index 2
    this->header.push_back(1); // index 3
    this->header.push_back(APKet::flags::SINGLE_PACKET); // index 4
    this->header.push_back(APKet::design_type_document::GLOW); // index 5
    this->header.push_back(2); // index 6
    this->header.push_back(LIBEMBER_GLOWDTD_VERSION_MINOR); // index 7
    this->header.push_back(LIBEMBER_GLOWDTD_VERSION_MAJOR); // index 8
}

APKet::EmberPacketHeader::EmberPacketHeader(libember::util::OctetStream& stream) : EmberHeader(stream) {
    this->header.insert(this->header.end(), std::next(stream.begin(), BASE_HEADER_SIZE), std::next(stream.begin(), EMBER_HEADER_SIZE));
    this->header.insert(this->header.end(), std::next(stream.begin(), EMBER_HEADER_SIZE), std::next(stream.begin(), EMBER_HEADER_SIZE + this->getAppBytes()));
}

bool APKet::EmberPacketHeader::hasFlagSet(APKet::flags flag) {
    if (flag == APKet::flags::WITHIN_MULTI_PACKET) {
        return !this->getFlags();
    }
    return (this->getFlags() & flag);
}

enum APKet::flags APKet::EmberPacketHeader::getFlags() const {
    return (enum APKet::flags)this->header[APKet::header_indices::FLAGS];
}

enum APKet::design_type_document APKet::EmberPacketHeader::getDTD() const {
    return (enum APKet::design_type_document)this->header[APKet::header_indices::DESIGN_TYPE_DOCUMENT];
}

unsigned char APKet::EmberPacketHeader::getAppBytes() const {
    return this->header[APKet::header_indices::APP_BYTES];
}

unsigned char APKet::EmberPacketHeader::getMinorGlowVersion() const {
    return this->header[APKet::header_indices::MINOR_GLOW_VERSION];
}

// ===== EmberHeaderFactory =====

APKet::EmberHeaderFactory::EmberHeaderFactory() {}

std::unique_ptr<APKet::EmberHeader> APKet::EmberHeaderFactory::createHeader(libember::util::OctetStream& stream) {

    APKet::command_type command_type = (APKet::command_type)*std::next(stream.begin(), (APKet::header_indices::COMMAND_TYPE));

    if (command_type == APKet::command_type::EMBER_PACKET) return std::unique_ptr<APKet::EmberHeader>(new APKet::EmberPacketHeader(stream));

    if (command_type == APKet::command_type::KEEP_ALIVE_REQ || command_type == APKet::command_type::KEEP_ALIVE_RESP) return std::unique_ptr<APKet::EmberHeader>(new APKet::EmberKeepAliveHeader(stream));

    throw std::runtime_error("Stream header has unknown command type.");

}
