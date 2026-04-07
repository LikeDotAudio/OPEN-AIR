include(CTest)

enable_testing()

add_executable(GlowParserTest GlowParser.cpp)
target_include_directories(GlowParserTest PRIVATE ../include)
target_include_directories(GlowParserTest PRIVATE ../subprojects/libember/Headers)
target_link_libraries(GlowParserTest PRIVATE APKet)

add_test(NAME GlowParserTest COMMAND GlowParserTest)

# FetchContent_Declare(
#     googletest
#     GIT_REPOSITORY https://github.com/google/googletest.git
#     GIT_TAG release-1.11.0
# )
# FetchContent_MakeAvailable(googletest)
# add_library(GTest::GTest INTERFACE IMPORTED)
# target_link_libraries(GTest::GTest INTERFACE gtest_main)