add_library(metatag-import)

target_sources(metatag-import
    PRIVATE
        csv_import.cpp
        itunes_sync.cpp
    PUBLIC
        include/csv_import.h
        include/itunes_sync.h
)

target_include_directories(metatag-import
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_link_libraries(metatag-import
    PUBLIC
        metatag-core
        Qt6::Core
)