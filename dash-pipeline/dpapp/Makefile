SHELL=/bin/bash
BUILD_DIR=build
CMAKE_ARGS=

ifeq ($(V),1)
CMAKE_ARGS += --verbose
endif

all: dpapp

.PHONY:configure install clean

configure:
	@cmake $(CMAKE_ARGS) -G Ninja -S . -B $(BUILD_DIR)

dpapp: configure
	@cmake --build $(BUILD_DIR) $(CMAKE_ARGS)

clean:
	@cmake --build $(BUILD_DIR) $(CMAKE_ARGS) -- clean

install:
	@sudo cmake --build $(BUILD_DIR) $(CMAKE_ARGS) -- install

