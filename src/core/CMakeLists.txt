add_library(metatag-core)

target_sources(metatag-core
    PRIVATE
        tag_reader.cpp
        track.cpp
    PUBLIC
        include/tag_reader.h
        include/track.h
)

target_include_directories(metatag-core
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_link_libraries(metatag-core
    PUBLIC
        TagLib::TagLib
        Qt6::Core
)

install(TARGETS metatag-core
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(FILES include/tag_reader.h include/track.h
    DESTINATION include/metatag
)