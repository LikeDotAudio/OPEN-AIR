#include "EmbServer.hpp"

APKet::EmbServer::EmbServer(std::shared_ptr<APKet::GlowDevice> root_device) : root_device(root_device) {
}

void APKet::EmbServer::listen(u16 port, std::function<bool()> stop_predicate) {


#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        Logger::getInstance().logError("Failed to initialize winsocket.");
        std::exit(EXIT_FAILURE);
    }
#endif

    Socket socket(port);

    // this->clients.push_back(std::make_shared<APKet::EmberClient>(socket.accept()));
    // this->handlers.push_back(std::shared_ptr<APKet::EmberMonster>(new APKet::EmberMonster(clients.back(), this->root_device)));

    fd_set readfds;
    i32 max_fd = 0;
    timeval timeout;

    Logger::getInstance().logDebug("Starting Multiplexing Loop");


    do {

        reset_select_params(readfds, timeout, max_fd, socket, clients);

        i32 ready_count = select(max_fd + 1, &readfds, NULL, NULL, &timeout); // Waits for any socket to be ready

        if (ready_count == 0) { // If the time limit is reached (no sockets are ready)
            for (auto& csv : APKet::CSVCollection::getInstance().getCSVList()) {
                csv.updateTable();
                csv.notifySubscribers();
            }
            continue;
        }
        else if (ready_count == -1) {
            APKet::Logger::getInstance().logWarning("Select failed.");
        }


        if (FD_ISSET(socket.getFd(), &readfds)) { // Check if socket has recieved data
        
            APKet::Logger::getInstance().logInfo("Accepted connection");
            std::shared_ptr<APKet::EmberClient> new_client;
            try {
                new_client = std::make_shared<APKet::EmberClient>(socket.accept());
            } catch (std::runtime_error e) {
                APKet::Logger::getInstance().logError("Error while accepting new connection", e);
                continue;
            }
            
            this->clients.push_back(new_client);
            this->handlers.push_back(std::shared_ptr<APKet::S101PacketHandler>(new APKet::S101PacketHandler(clients.back(), this->root_device)));

        }


        for (size_t i = 0; i < clients.size(); i++) {
            auto& client = clients.at(i);
            auto& handler = handlers.at(i);

            if (FD_ISSET(client->getFD(), &readfds)) {
                Logger::getInstance().logDebug("Reading data from " + client->getIPAddress());
                if (connection_main(*client, *handler) == 1) { // If rseult of main indicates that the connection is closed
                    clients.erase(clients.begin() + i);
                    handlers.erase(handlers.begin() + i);
                }
            }
        }

    } while (!stop_predicate());

    APKet::Logger::getInstance().logInfo("Stop predicate returned true. Shutting down server.");

}

int APKet::EmbServer::connection_main(APKet::EmberClient& client, APKet::S101PacketHandler& monster) {

    do {

        libember::util::OctetStream new_packet;

        try {

            new_packet = client.read();

        }
        catch (const std::runtime_error& e) {
            std::ignore = e;
            APKet::Logger::getInstance().logInfo(client.getIPAddress() + " Disconnected.");
            monster.cleanUp();
            return 1;
        } // Close somehow

        try {

            monster.feed_packet(new_packet);

        }
        catch (const std::runtime_error& e) { APKet::Logger::getInstance().logError("Error while handling packet from " + client.getIPAddress() + ": ", e); }

    } while (!client.bufferIsEmpty());

    return 0;

}

void APKet::EmbServer::reset_select_params(fd_set& readfds, timeval& timeout, i32& max_fd, Socket& socket, std::vector<std::shared_ptr<APKet::EmberClient>>& clients) {
    timeout.tv_sec = 0;
    timeout.tv_usec = 250 * 1000;
    FD_ZERO(&readfds);
    FD_SET(socket.getFd(), &readfds);
    max_fd = socket.getFd();


    for (auto& client : clients) {
        FD_SET(client->getFD(), &readfds);
        if (client->getFD() > max_fd) max_fd = client->getFD();
    }
}