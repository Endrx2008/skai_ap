cmake_minimum_required(VERSION 3.5)

project(OllamaChat LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTOMOC ON)

find_package(Qt5 COMPONENTS Widgets REQUIRED)

add_executable(OllamaChat
    main.cpp
    mainwindow.cpp
)

target_link_libraries(OllamaChat Qt5::Widgets)
