#include "communication/connection/EmberClient.hpp"

APKet::EmberClient::EmberClient(i32 fd, struct sockaddr_in addr) : connection(fd, addr) {}

APKet::EmberClient::EmberClient(APKet::ClientConnection connection) : connection(connection) {}

void APKet::EmberClient::send(const libember::util::OctetStream& stream) const {
    libember::util::OctetStream send_stream = libember::util::OctetStream(stream);
    packageMessageWithS101(send_stream);
    std::string send_str = std::string(send_stream.begin(), send_stream.end());
    this->connection.send(send_str);
}

libember::util::OctetStream APKet::EmberClient::read() {

    if (this->read_buffer.size() > 0) {
        return pop_buffer();
    }

    std::vector<libember::util::OctetStream*> messages = std::vector<libember::util::OctetStream*>();

    std::string read_buffer = this->connection.read();

    this->decoder.read(read_buffer.begin(), read_buffer.end(), [this](libember::ber::Octets::const_iterator first, libember::ber::Octets::const_iterator last) -> bool {
        libember::util::OctetStream stream = libember::util::OctetStream();
        stream.append(first, last);
        this->read_buffer.push_back(stream);
        return true;
        });

    libember::util::OctetStream message = this->read_buffer[0];
    this->read_buffer.erase(this->read_buffer.begin());
    return message;

    return this->read();

}

bool APKet::EmberClient::bufferIsEmpty() {
    return this->read_buffer.size() == 0;
}