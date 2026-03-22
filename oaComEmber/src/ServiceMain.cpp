#include "ServiceMain.hpp"

namespace fs = std::filesystem;

// NOTE: Currently this only works for 64 bit builds. IDK why yet

int _tmain(int argc, TCHAR* argv[])
{
    // Get the directory containing the executable
    fs::path executablePath = fs::absolute(fs::path(argv[0])).parent_path();

    // Set the current working directory to the directory containing the executable
    fs::current_path(executablePath);

    std::stringstream wd;
    wd << "Current working directory: " << std::filesystem::current_path();

    APKet::Logger::getInstance().logInfo(wd.str());


    const char* name = "EmberCSV";

    // Allocate memory for the LPSTR
    size_t length = strlen(name) + 1; // +1 for the null terminator
    LPSTR lpstr = new char[length];

    // Copy the C-style string to the LPSTR
    strcpy(lpstr, name);

    SERVICE_TABLE_ENTRY ServiceTable[2];
    ServiceTable[0].lpServiceName = lpstr;
    ServiceTable[0].lpServiceProc = (LPSERVICE_MAIN_FUNCTION)ServiceMain;
    ServiceTable[1].lpServiceName = NULL;
    ServiceTable[1].lpServiceProc = NULL;
    //  =
    // {
    //     {lpwstr, (LPSERVICE_MAIN_FUNCTION)ServiceMain},
    //     {NULL, NULL}
    // };

    if (StartServiceCtrlDispatcher(ServiceTable) == FALSE)
    {
        return GetLastError();
    }


    return 0;
}


VOID WINAPI ServiceMain(DWORD argc, LPTSTR* argv)
{

    // std::string inputString(SERVICE_NAME);
    // int wideStringLength = MultiByteToWideChar(CP_UTF8, 0, inputString.c_str(), -1, NULL, 0);
    // wchar_t* wideString = new wchar_t[wideStringLength];
    // MultiByteToWideChar(CP_UTF8, 0, inputString.c_str(), -1, wideString, wideStringLength);

    DWORD Status = E_FAIL;

    // Register our service control handler with the SCM
    g_StatusHandle = RegisterServiceCtrlHandler(SERVICE_NAME, ServiceCtrlHandler);

    if (g_StatusHandle == NULL)
    {
        return;
    }

    // Tell the service controller we are starting
    ZeroMemory(&g_ServiceStatus, sizeof(g_ServiceStatus));
    g_ServiceStatus.dwServiceType = SERVICE_WIN32_OWN_PROCESS;
    g_ServiceStatus.dwControlsAccepted = 0;
    g_ServiceStatus.dwCurrentState = SERVICE_START_PENDING;
    g_ServiceStatus.dwWin32ExitCode = 0;
    g_ServiceStatus.dwServiceSpecificExitCode = 0;
    g_ServiceStatus.dwCheckPoint = 0;

    if (SetServiceStatus(g_StatusHandle, &g_ServiceStatus) == FALSE)
    {
        OutputDebugString(_T(
            "My Sample Service: ServiceMain: SetServiceStatus returned error"));
    }

    /*
     * Perform tasks necessary to start the service here
     */

     // Create a service stop event to wait on later
    g_ServiceStopEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
    if (g_ServiceStopEvent == NULL)
    {
        // Error creating event
        // Tell service controller we are stopped and exit
        g_ServiceStatus.dwControlsAccepted = 0;
        g_ServiceStatus.dwCurrentState = SERVICE_STOPPED;
        g_ServiceStatus.dwWin32ExitCode = GetLastError();
        g_ServiceStatus.dwCheckPoint = 1;

        if (SetServiceStatus(g_StatusHandle, &g_ServiceStatus) == FALSE)
        {
            OutputDebugString(_T(
                "My Sample Service: ServiceMain: SetServiceStatus returned error"));
        }
        return;
    }

    // Tell the service controller we are started
    g_ServiceStatus.dwControlsAccepted = SERVICE_ACCEPT_STOP;
    g_ServiceStatus.dwCurrentState = SERVICE_RUNNING;
    g_ServiceStatus.dwWin32ExitCode = 0;
    g_ServiceStatus.dwCheckPoint = 0;

    if (SetServiceStatus(g_StatusHandle, &g_ServiceStatus) == FALSE)
    {
        OutputDebugString(_T(
            "My Sample Service: ServiceMain: SetServiceStatus returned error"));
    }

    // Start a thread that will perform the main task of the service
    HANDLE hThread = CreateThread(NULL, 0, ServiceWorkerThread, NULL, 0, NULL);

    // Wait until our worker thread exits signaling that the service needs to stop
    WaitForSingleObject(hThread, INFINITE);


    /*
     * Perform any cleanup tasks
     */

    CloseHandle(g_ServiceStopEvent);

    // Tell the service controller we are stopped
    g_ServiceStatus.dwControlsAccepted = 0;
    g_ServiceStatus.dwCurrentState = SERVICE_STOPPED;
    g_ServiceStatus.dwWin32ExitCode = 0;
    g_ServiceStatus.dwCheckPoint = 3;

    if (SetServiceStatus(g_StatusHandle, &g_ServiceStatus) == FALSE)
    {
        OutputDebugString(_T(
            "My Sample Service: ServiceMain: SetServiceStatus returned error"));
    }
}

VOID WINAPI ServiceCtrlHandler(DWORD CtrlCode)
{
    switch (CtrlCode)
    {
    case SERVICE_CONTROL_STOP:

        if (g_ServiceStatus.dwCurrentState != SERVICE_RUNNING)
            break;

        /*
         * Perform tasks necessary to stop the service here
         */

        g_ServiceStatus.dwControlsAccepted = 0;
        g_ServiceStatus.dwCurrentState = SERVICE_STOP_PENDING;
        g_ServiceStatus.dwWin32ExitCode = 0;
        g_ServiceStatus.dwCheckPoint = 4;

        if (SetServiceStatus(g_StatusHandle, &g_ServiceStatus) == FALSE)
        {
            OutputDebugString(_T(
                "My Sample Service: ServiceCtrlHandler: SetServiceStatus returned error"));
        }

        // This will signal the worker thread to start shutting down
        SetEvent(g_ServiceStopEvent);

        break;

    default:
        break;
    }
}

DWORD WINAPI ServiceWorkerThread(LPVOID lpParam)
{

    auto stop_predicate = []() { // Will return true if ready to stop the service
        return WaitForSingleObject(g_ServiceStopEvent, 0) == WAIT_OBJECT_0;
    };

    APKet::Config& config = APKet::Config::getInstance();

    std::shared_ptr<APKet::GlowDevice> midi_collection = std::dynamic_pointer_cast<APKet::GlowDevice>(std::make_shared<APKet::HUIDeviceCollection>(config.getPaths().size()));

    APKet::EmbServer server = APKet::EmbServer(midi_collection);

    try {
        server.listen(config.getPort(), stop_predicate);
    } catch (const std::runtime_error e) {
        APKet::Logger::getInstance().logError("Error encountered in service thread.", e);
    }

    return ERROR_SUCCESS;
}
    