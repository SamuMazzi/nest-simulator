# /path/to/nest-simulator/src/fastconn/CMakeLists.txt

# 1. Define Source
set(fastconn_SOURCES fastconn.cpp)

# 2. Find Python (Required for Python.h)
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# 3. Create Shared Library
add_library(fastconn SHARED ${fastconn_SOURCES})

# 4. Set Include Directories (CRITICAL STEP)
# We must manually add the paths to the NEST source folders so #include works.
target_include_directories(fastconn PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${Python3_INCLUDE_DIRS}
    
    # Point to NEST source directories for headers
      ${PROJECT_BINARY_DIR}/libnestutil
      ${PROJECT_SOURCE_DIR}/libnestutil
      ${PROJECT_SOURCE_DIR}/nest
      ${PROJECT_SOURCE_DIR}/nestkernel
      ${PROJECT_SOURCE_DIR}/nestkernel/spatial
      ${PROJECT_SOURCE_DIR}/sli
      ${PROJECT_SOURCE_DIR}/thirdparty
      ${PROJECT_SOURCE_DIR}/models
      # Point to Build directories (sometimes needed for generated config headers)
      ${CMAKE_BINARY_DIR}/nestkernel
      ${PROJECT_BINARY_DIR}/nest
      ${Python_INCLUDE_DIRS}
)

# 5. Link Libraries
# Link against the NEST kernel target and Python
target_link_libraries(fastconn PRIVATE
    nest_kernel
    Python3::Module
)

# 6. Properties for direct Python import (removes 'lib' prefix)
set_target_properties(fastconn PROPERTIES
    PREFIX ""
    OUTPUT_NAME "fastconn"
)

# 7. Install rules
install(TARGETS fastconn
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
