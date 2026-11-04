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

if (MSVC)
    set_target_properties(metatag-tests PROPERTIES
        WIN32_EXECUTABLE FALSE
        LINK_FLAGS "/SUBSYSTEM:CONSOLE"
    )
endif()

add_test(NAME metatag-tests COMMAND metatag-tests)
set_tests_properties(metatag-tests PROPERTIES
    ENVIRONMENT "PATH=$<TARGET_FILE_DIR:metatag-tests>\;$ENV{PATH}"
)

if (WIN32 AND CMAKE_VERSION VERSION_GREATER_EQUAL "3.21")
    add_custom_command(TARGET metatag-tests POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            $<TARGET_RUNTIME_DLLS:metatag-tests>
            $<TARGET_FILE_DIR:metatag-tests>
        COMMAND_EXPAND_LISTS
    )
endif()