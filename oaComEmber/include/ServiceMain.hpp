#pragma once

#include "EmbServer.hpp"
#include "device/HUIDeviceCollection.hpp"
#include "Logger.hpp"
#include <filesystem>
#include <windows.h>
#include <winerror.h>
#include <tchar.h>

SERVICE_STATUS        g_ServiceStatus = { 0 };
SERVICE_STATUS_HANDLE g_StatusHandle = NULL;
HANDLE                g_ServiceStopEvent = INVALID_HANDLE_VALUE;

VOID WINAPI ServiceMain(DWORD argc, LPTSTR* argv);
VOID WINAPI ServiceCtrlHandler(DWORD);
DWORD WINAPI ServiceWorkerThread(LPVOID lpParam);

#define SERVICE_NAME  _T("My Sample Service")