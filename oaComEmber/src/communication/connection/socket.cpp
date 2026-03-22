#include "communication/connection/socket.hpp"


Socket::Socket(const u16& port) {
    if ((this->fd = ::socket(AF_INET, SOCK_STREAM, 0)) < 0) {
#ifdef _WIN32
        WSACleanup();
#endif
        throw std::runtime_error("Failed to create socket");
    }

    this->serv_addr.sin_family = AF_INET;
    this->serv_addr.sin_port = ::htons(port);
    this->serv_addr.sin_addr.s_addr = ::htonl(INADDR_ANY);

    if (::bind(this->fd, (SA*)&this->serv_addr, sizeof(this->serv_addr)) < 0) {
#ifdef _WIN32
        closesocket(this->fd);
        WSACleanup();
#else
        ::close(this->fd);
#endif
        throw std::runtime_error("Failed to bind to socket using port " + std::to_string(port));
    }

    if (::listen(this->fd, 5) < 0) {
#ifdef _WIN32
        closesocket(this->fd);
        WSACleanup();
#else
        ::close(this->fd);
#endif
        throw std::runtime_error("Failed to listen to socket");
    }

    APKet::Logger::getInstance().logInfo("Server listening on port " + std::to_string(port));
}

// Returns pair with file descriptor and socket info of client
auto Socket::accept() -> APKet::ClientConnection const {
    i32 client_fd;
    struct sockaddr_in client;
    const auto addrlen = sizeof(client);

    if ((client_fd = ::accept(this->fd, (SA*)&client, (socklen_t*)&addrlen)) < 0) {
#ifdef _WIN32
        closesocket(client_fd);
#else
        close(client_fd);
#endif
        throw std::runtime_error("Failed to accept connection");
    }

    return APKet::ClientConnection(client_fd, client);
}

i32 Socket::getFd() {
    return this->fd;
}
