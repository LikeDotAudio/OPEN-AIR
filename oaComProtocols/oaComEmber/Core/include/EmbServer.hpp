#include "types.hpp"
#include "GlowDevice.hpp"
#include "EmberMonster.hpp"
#include <functional>

namespace APKet {

    class EmbServer {

        public:

            /*
             * Creates ember producer that hosts the device defined by root_device
             */
            EmbServer(std::shared_ptr<APKet::GlowDevice> root_device);

            EmbServer(const EmbServer&) = delete;

            /*
             * This call will block and listen until the callback returns true
             */
            void listen(u16 port, std::function<bool()> callback);

        private:

            void reset_select_params(fd_set& readfds, timeval& timeout, i32& max_fd, Socket& socket, std::vector<std::shared_ptr<APKet::EmberClient>>& clients);

            int connection_main(APKet::EmberClient& client, APKet::S101PacketHandler& monster);

            std::shared_ptr<APKet::GlowDevice> root_device;

            std::vector<std::shared_ptr<APKet::EmberClient>> clients;
            
            std::vector<std::shared_ptr<APKet::S101PacketHandler>> handlers;

    };

}