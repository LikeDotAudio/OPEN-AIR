#pragma once

#ifdef _LINUX
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>
#include <unistd.h>
#include <sys/select.h>
#endif

#ifdef _WIN32
#include <winsock2.h>
#include <WS2tcpip.h>

#pragma comment(lib, "Ws2_32.lib")
#endif

#include "EmbServer.hpp"
#include "device/HUIDeviceCollection.hpp"

