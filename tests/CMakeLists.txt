# Test executable
add_executable(metatag-tests
    test_track.cpp
)

target_link_libraries(metatag-tests
    PRIVATE
        metatag-core
        metatag-utils
        Qt6::Test
)

target_include_directories(metatag-tests
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
)