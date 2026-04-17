add_library(metatag-online)

target_sources(metatag-online
    PRIVATE
        cover_finder.cpp
        musicbrainz_lookup.cpp
    PUBLIC
        include/cover_finder.h
        include/musicbrainz_lookup.h
)

target_include_directories(metatag-online
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_link_libraries(metatag-online
    PUBLIC
        metatag-core
        Qt6::Network
)