#pragma once

#include <iostream>
#include <memory>
#include <string>
#include <cstdlib>

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

#include "communication/connection/ClientConnection.hpp"
#include "types.hpp"

using SA = struct sockaddr;

class Socket {
private:
  i32 fd;
  struct sockaddr_in serv_addr;

public:
  Socket(const u16&);

  i32 getFd();

  auto accept() -> APKet::ClientConnection const;
};
