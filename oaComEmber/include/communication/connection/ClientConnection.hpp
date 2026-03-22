#pragma once

#ifdef _LINUX
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>
#include <unistd.h>
#endif

#ifdef _WIN32
#include <winsock2.h>
#include <WS2tcpip.h>

#pragma comment(lib, "Ws2_32.lib")
#endif
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

#include "ember/util/OctetStream.hpp"

#include "Logger.hpp"
#include "types.hpp"

namespace APKet {
    
    /*
     * A simple class that wraps a socket connection to a client and guarantees that the entire buffer is sent.
     */
    class ClientConnection {
        
        public:

            ClientConnection(i32 fd, struct sockaddr_in addr);

            // ClientConnection(const ClientConnection&) = delete;
            
            /*
             * Destructor. Does not close the socket.
             */
            ~ClientConnection() = default;

            /* 
             * Send function that guarantees entire buffer sent.
             * Otherwise a runtime_error is thrown.
             */
            void send(const std::string& buffer) const;

            void close();

            i32 getFD() const;

            std::string getIPAddress() const;

            /*
             * Read function that returns a string of the data read.
             * Throws a runtime_error if the connection is closed.
             */
            std::string read();

        private:
        
            i32 fd;

            struct sockaddr_in addr;

    };

}