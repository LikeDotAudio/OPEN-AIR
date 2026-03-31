# CMakeList.txt : CMake project for EmberCSV, include source and define
# project specific logic here.
#


cmake_minimum_required (VERSION 3.8)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if (POLICY CMP0141)
  cmake_policy(SET CMP0141 NEW)
  set(CMAKE_MSVC_DEBUG_INFORMATION_FORMAT "$<IF:$<AND:$<C_COMPILER_ID:MSVC>,$<CXX_COMPILER_ID:MSVC>>,$<$<CONFIG:Debug,RelWithDebInfo>:EditAndContinue>,$<$<CONFIG:Debug,RelWithDebInfo>:ProgramDatabase>>")
endif()

if(MSVC)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

if(NOT DEFINED PROJECT_NAME)
    set(IS_TOPLEVEL ON)
endif()

project ("EmberCSV")
include(CTest)


add_subdirectory(subprojects/libember)
add_subdirectory(subprojects/libs101)

### APK Ember Thing Library
add_library(APKet STATIC 
"src/EmbServer.cpp"
"src/EmberMonster.cpp"
"src/Config.cpp" 
"src/device/HUIParameters.cpp"
"src/device/HUIChannel.cpp" 
"src/device/HUIDevice.cpp" 
"src/device/HUIDeviceCollection.cpp" 
"src/csv/CSV.cpp" 
"src/communication/EmberHeader.cpp" 
"src/communication/S101Packager.cpp" 
"src/communication/connection/ClientConnection.cpp" 
"src/communication/connection/EmberClient.cpp" 
"src/communication/connection/socket.cpp" 
"src/GlowParser.cpp")

target_link_libraries(APKet PRIVATE ember-static)

target_include_directories(APKet PRIVATE subprojects/libember/Headers)
target_include_directories(APKet PRIVATE subprojects/libs101/Headers)
target_include_directories(APKet PRIVATE include)


if (IS_TOPLEVEL)

### EmberCSV EXE ###

  add_executable (EmberCSV "src/main.cpp")

  if (CMAKE_VERSION VERSION_GREATER 3.12)
    set_property(TARGET EmberCSV PROPERTY CXX_STANDARD 20)
  endif()

  target_link_libraries(EmberCSV PRIVATE APKet)

  target_include_directories(EmberCSV PRIVATE include)
  target_include_directories(EmberCSV PRIVATE subprojects/libember/Headers)
  target_include_directories(EmberCSV PRIVATE subprojects/libs101/Headers)


### Service EXE ###

  add_executable (EmberCSVService "src/ServiceMain.cpp")

  if (CMAKE_VERSION VERSION_GREATER 3.12)
    set_property(TARGET EmberCSVService PROPERTY CXX_STANDARD 20)
  endif()

  target_link_libraries(EmberCSVService PRIVATE APKet)

  target_include_directories(EmberCSVService PRIVATE include)
  target_include_directories(EmberCSVService PRIVATE subprojects/libember/Headers)
  target_include_directories(EmberCSVService PRIVATE subprojects/libs101/Headers)

  
### TESTING ###
  enable_testing()
  add_subdirectory(tests)

endif()