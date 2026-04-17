add_library(metatag-utils)

target_sources(metatag-utils
    PRIVATE
        string_utils.cpp
        file_utils.cpp
        regex_utils.cpp
    PUBLIC
        include/string_utils.h
        include/file_utils.h
        include/regex_utils.h
)

target_include_directories(metatag-utils
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_link_libraries(metatag-utils
    PUBLIC
        Qt6::Core
)