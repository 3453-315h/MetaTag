# Test executable
add_executable(metatag-tests
    main.cpp
    test_track.cpp
    test_track.h
)

target_link_libraries(metatag-tests
    PRIVATE
        metatag-core
        metatag-import
        metatag-utils
        Qt6::Test
        Qt6::Widgets
)

target_include_directories(metatag-tests
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
)

add_test(NAME metatag-tests COMMAND metatag-tests)