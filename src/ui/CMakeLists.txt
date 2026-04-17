add_executable(metatag-ui
    main.cpp
    mainwindow.cpp
)

target_link_libraries(metatag-ui
    PRIVATE
        metatag-core
        Qt6::Widgets
        Qt6::Core
        Qt6::Gui
)

target_include_directories(metatag-ui
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
)