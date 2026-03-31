#include "communication/connection/ClientConnection.hpp"

APKet::ClientConnection::ClientConnection(i32 fd, struct sockaddr_in addr) : fd(fd), addr(addr) {}

// APKet::ClientConnection::~ClientConnection() {}

#include <iomanip> // Add this line

void APKet::ClientConnection::send(const std::string& buffer) const {
    const char* data = buffer.c_str();
    size_t size = buffer.size();

    while (size > 0) {

        std::stringstream bytes_str;
        for (unsigned char byte : buffer) {
            bytes_str << std::uppercase << std::setw(2) << std::setfill('0') << std::hex << (int)byte << " ";
        }
        APKet::Logger::getInstance().logDebug("Sending: " + bytes_str.str());

        size_t num_bytes = ::send(this->fd, data, size, 0);

        if (num_bytes == (size_t)-1) {
            throw std::runtime_error("Failed to send data");
            break;
        }

        data += num_bytes;
        size -= num_bytes;
    }
}

void APKet::ClientConnection::close() {
#ifdef _WIN32
    closesocket(this->fd);
    WSACleanup();
#else
    ::close(this->fd);
#endif
}

i32 APKet::ClientConnection::getFD() const {
    return this->fd;
}

std::string APKet::ClientConnection::getIPAddress() const {
    char ip[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &(this->addr.sin_addr), ip, INET_ADDRSTRLEN);
    return std::string(ip);
}


std::string APKet::ClientConnection::read() {
    char buffer[1290];

#ifdef _WIN32
    i32 num_read = ::recv(this->fd, buffer, 1290, 0);
#else
    i32 num_read = ::recv(this->fd, &buffer, 1290, 0);
#endif

    if (num_read == 0) {
        throw std::runtime_error("Connection Closed.");
    }
    else if (num_read == -1) {
        throw std::runtime_error("Error while reading");
    }

    
    std::stringstream bytes_str;
    for (i32 i = 0; i < num_read; i++) {
        bytes_str << std::uppercase << std::setw(2) << std::setfill('0') << std::hex << (int)(u8)buffer[i] << " ";
    }
    APKet::Logger::getInstance().logDebug("Received: " + bytes_str.str());

    return std::string((char*)buffer, num_read);
}
