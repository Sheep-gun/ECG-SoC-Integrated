cmake_minimum_required(VERSION 3.15)
project(exact_cpp_snn_ecg LANGUAGES CXX)

option(EXACT_CPP_TRACE "Enable architectural trace collection" ON)
option(EXACT_CPP_SANITIZERS "Enable supported address/undefined sanitizers" OFF)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(exact_cpp_options INTERFACE)
target_compile_definitions(exact_cpp_options INTERFACE
    $<$<BOOL:${EXACT_CPP_TRACE}>:EXACT_CPP_TRACE=1>
    $<$<NOT:$<BOOL:${EXACT_CPP_TRACE}>>:EXACT_CPP_TRACE=0>)

if(MSVC)
    target_compile_options(exact_cpp_options INTERFACE /W4 /permissive- /EHsc)
else()
    target_compile_options(exact_cpp_options INTERFACE -Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion)
    if(EXACT_CPP_SANITIZERS)
        target_compile_options(exact_cpp_options INTERFACE -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(exact_cpp_options INTERFACE -fsanitize=address,undefined)
    endif()
endif()

enable_testing()
add_library(exact_snn_model STATIC src/feature_blocks.cpp src/snapshot_readout.cpp
    src/exact_model.cpp src/final_membrane.cpp)
target_include_directories(exact_snn_model PUBLIC include)
target_link_libraries(exact_snn_model PUBLIC exact_cpp_options)

add_executable(exact_cpp_ecg src/main.cpp)
target_link_libraries(exact_cpp_ecg PRIVATE exact_snn_model)

add_executable(test_fixed_width tests/test_fixed_width.cpp)
target_include_directories(test_fixed_width PRIVATE include)
target_link_libraries(test_fixed_width PRIVATE exact_cpp_options)
add_test(NAME fixed_width COMMAND test_fixed_width)

add_executable(test_feature_blocks tests/test_feature_blocks.cpp)
target_link_libraries(test_feature_blocks PRIVATE exact_snn_model)
add_test(NAME feature_blocks COMMAND test_feature_blocks)

add_executable(test_adversarial_sequences tests/test_adversarial_sequences.cpp)
target_link_libraries(test_adversarial_sequences PRIVATE exact_snn_model)
add_test(NAME adversarial_sequences COMMAND test_adversarial_sequences)
