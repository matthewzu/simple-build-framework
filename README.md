# Simple Build Framework

- [Simple Build Framework](#simple-build-framework)
  - [1. Overview](#1-overview)
  - [2. Makefile directly](#2-makefile-directly)
    - [2.1 Module Makefile Segment](#21-module-makefile-segment)
    - [2.2 How to add one module](#22-how-to-add-one-module)
    - [2.3 How to use](#23-how-to-use)
  - [3. Pyhton Generator - ZMake](#3-pyhton-generator---zmake)
    - [3.1 YAML Configuration](#31-yaml-configuration)
    - [3.2 How to add one module](#32-how-to-add-one-module)
    - [3.3 How to use](#33-how-to-use)
  - [4. TODO](#4-todo)

## 1. Overview

This is one simple build framework for the modularized softwares. It makes use of Python, Makefile, Ninja-build and Kconfig, and could supply the following build methods:

- **Makefile directly**: `Makefile` is supplied directly, and Makefile segments are used to configure appliations and libraries;
- **Pyhton Generator - ZMake**: Pythons script are used to generate Makefile or build.ninja by YAML configuration files for appliations and libraries.

The following are required:

- GNU Make tool;
- Ninja-build tool;
- Python3;
- [github.com/ulfalizer/Kconfiglib](https://github.com/ulfalizer/Kconfiglib)

**Note that**, `Kconfiglib` need be installed by `pip3` tool.

## 2. Makefile directly

For this mode, the following features are supplied:

1. Cross-compiler are supported;
2. Multiple applications and libraries are supported;
3. Multiple level modules are supported;
4. Each module has its own public and/or private header files, source files(C/C++/assembly), Kconfig scripts and Makefile segment;
5. All the files that belongs to one module are placed in one directory;
6. The following attribute of the moulde could be specified:

   - Name;
   - Type, application or library;
   - Public header directory;
   - Source files;
   - Compiler flags;

7. The following attribute of the source files could be specified:

    - Compiler flags;

8. Kconfig scripts starts at Kconfig in the root directory, and could be modify as you need;
9. The public header path of the enabled modules will be added to the compile flags for all the source files, so the module pathes could be ignored.

### 2.1 Module Makefile Segment

For this mode, Simple build framework confgure the modules by **Makefile segments**, which must be named as `module.mk`, and has the following options:

```Makefile
# moudle configuration 

# type: application - APPS_XXX moulde - MODULES_XXX
# Enable/Disable: Kconfig option - CONFIG_XXX
# name: <moulde name>, could be one or more
MODULES_<$(CONFIG_XXX)> += <moulde name>
APPS_<$(CONFIG_XXX)>    += <moulde name>

# source files, could be one or more
SRCS_<moulde name>_<$(CONFIG_XXX)>     = $(SRC_TREE)/<moulde path>/xxx.x

# header file directories, could one or more
HDRDIR_<moulde name>_<$(CONFIG_XXX)> = $(SRC_TREE)/<moulde path>/xxx

# Compiler flags for moudle
CFLAGS_<moulde name>            = xxx
CPPFLAGS_<moulde name>            = xxx
ASMFLAGS_<moulde name>            = xxx

# Compiler flags for moudle souce file
CFLAGS_<moulde name>_<source file name>     = xxx
CPPFLAGS_<moulde name>_<source file name>   = xxx
ASMFLAGS_<moulde name>_<source file name>   = xxx
```

### 2.2 How to add one module

1. Create one directory in the framework;
2. Add souce files and `module.mk` to this module;
3. Add public header directory with public header files to this module as you need;
4. Add private header files to this module as you need;
5. Add Kconfig files(`*.config`) to this module， and include them from Kconfig in the root directory of the framework.

### 2.3 How to use

1. Intstall Make, ninja-build and Python3;
2. Install Kconfiglib:

    ```bash
    simple-build-framework$ pip3 install kconfiglib
    ```

3. Kconfiglib path may be need to be added to 'PATH' environment variable; for Linux, execute `export PATH=$PATH:~/.local/bin` in the shell or add this command to `~/.bashrc` or `~/.bash_profile`;
4. Configurate project:

    ```bash
    simple-build-framework$ make OUT=<project path> config
    ```

5. Build project:

    ```bash
    simple-build-framework$ make OUT=<project path>
    simple-build-framework$ make OUT=<project path> V=1 # enable verbose output
    simple-build-framework$ make OUT=<project path> CROSS_COMPILE=<cross-compiler prefix> # enable cross-compiler
    simple-build-framework$ make OUT=<project path> clean
    ```

**NOTE** that **make help** could be used to obtain the usage for all make commands.

## 3. Pyhton Generator - ZMake

For this mode, the following features are supplied:

1. Project are configured by **YAML file**;
2. Tools and basic options for **CC/AR/LD** could be specified;
3. Multiple applications and libraries are supported;
4. Multiple level modules are supported;
5. Each module has its own public and/or private header files, source files(C/C++/assembly), Kconfig scripts and **YAML configuration file**;
6. All the files that belongs to one module are placed in one directory;
7. The following attribute of the libraries could be specified:

   - Name;
   - corresponding Kconfig option that are used to enable/disable this module;
   - Source files;
   - Public header directory;
   - Compiler flags;

8. The following attribute of the applications could be specified:

   - Name;
   - corresponding Kconfig option that are used to enable/disable this module;
   - Source files;
   - Compiler flags;
   - linker flags;
   - libraries depended that are used to include corresponding hedear files and libraries for this module;

9. The following attribute of the source files could be specified:

    - Compiler flags;

10. Kconfig scripts starts at `Kconfig` in the root directory, and `defconfig` could be specifed;
11. Build order are decided by the defined order in YAML configuration files for Makefile;
12. Build order are decided by the depends in YAML configuration files for Ninja build.

### 3.1 YAML Configuration

For this mode, Simple build framework confgure the modules by **YAML configuration files** and statrt at `top.yml` in the root directory.

`top.yml` includes the configuration template and the referenece to other configuration files for moudles. For examle:

```yaml
# zmake top configuartion

# includes, note that file contents MUST NOT be overlapped,
# otherwise the latter will overwrite the former.

includes:
  - mod1/mod11/mod11.yml  # library mod11 yaml
  - mod1/mod12/mod12.yml  # library mod12 yaml
  - mod2/mod2.yml         # library mod2 yaml
  - main/main.yml         # application main/mani2 yaml

# entities defines for the following types:
#   1)'var':    variables that is used to save build arguments or intermediate variables,
#   could be be referenced by '$(variable name)';
#   2)'target': target for build command(make/ninja...);
#   3)'app':    applications that could be executed;
#   4)'lib':    libraries that could be linked to applications.

# system variables
#   1)SRC_PATH: path for source code
#   2)PRJ_PATH: path for project

# customer variables
#
# example:
#
#   variable name:  # must be unique for all entities
#     type: var
#     desc: xxx # optional, description that is only for display
#     val:  xxx # string that could include references to other variables
                # that have beed defined, such as '$(var_name)', or any value

CC:
  type: var
  desc: compiler for objects
  val:  gcc -MD

AR:
  type: var
  desc: archiver for libraries
  val:  ar

LD:
  type: var
  desc: linker for applications
  val:  gcc

# libraries
#
# example:
#
# library name:             # must be unique for all entities
#   type:       lib
#   desc:       xxx         # optional, description that is only for display
#   opt:        CONFIG_XXX  # optional, Kconfig option that decides whether library is enabled:
#                           #   if present, it must be a Kconfig option that will be 'y' or 'n';
#                           #   if absent, library will be will be forced to enable.
#   src:                    # list, source files or directories:
#     - $(ZMake variable name)/xxx/xxx.c
#     - $(ZMake variable name)/xxx  # for directory, all source files in it will be involved
#   hdrdirs:                # optional, list, public header file directories
#     - $(ZMake variable name)/xxx
#   cflags:                 # optional, additional compiler flags for C files
#     all:      xxx         # compiler flags for all C files
#     xxx.c:    xxx         # compiler flags for xxx.c
#   cppflags:               # optional, additional compiler flags for cpp files
#     all:      xxx         # compiler flags for all CPP files
#     xxx.cpp:  xxx         # compiler flags for xxx.cpp
#   asmflags:   xxx         # optional, additional compiler flags for assembly files
#     all:      xxx         # compiler flags for all assembly files
#     xxx.s:    xxx         # compiler flags for xxx.s
#     xxx.S:    xxx         # compiler flags for xxx.S

# applications
#
# example:
#
# application name:         # must be unique for all entities
#   type:       app
#   desc:       xxx         # optional, description that is only for display
#   opt:        CONFIG_XXX  # optional, Kconfig option that decides whether application is enabled:
#                           #   if present, it must be a Kconfig option that will be 'y' or 'n';
#                           #   if absent, application will be will be forced to enable.
#   src:                    # list, source files or directories:
#     - $(ZMake variable name)/xxx/xxx.c
#     - $(ZMake variable name)/xxx  # for directory, all source files in it will be involved
#   cflags:                 # optional, additional compiler flags for C files
#     all:      xxx         # compiler flags for all C files
#     xxx.c:    xxx         # compiler flags for xxx.c
#   cppflags:               # optional, additional compiler flags for cpp files
#     all:      xxx         # compiler flags for all CPP files
#     xxx.cpp:  xxx         # compiler flags for xxx.cpp
#   asmflags:   xxx         # optional, additional compiler flags for assembly files
#     all:      xxx         # compiler flags for all assembly files
#     xxx.s:    xxx         # compiler flags for xxx.s
#     xxx.S:    xxx         # compiler flags for xxx.S
#   linkflags:  xxx         # optional, additional linker flags
#   libs:       xxx         # optional, list, libraries depended:
#     - xxx

# system targets
#
#   1)config:     confogure project
#   2)all:        building all applications/libraries, default target
#   3)clean:      clean all compiled files
#
#   To enable verbose output, add "V=1" option for make or add "-v" for ninja.

# customer targets
#
# example:
#
# target name:      # must be unique for all entities
#   type: target
#   desc: xxx # optional, description that is only for display
#   cmd:  xxx # optional, commands that need be executed with description:
#     desc:   command
#   deps: xxx # optional, modules depended:
#     - xxx
#
# Note that 'cmd' and 'deps' MUST NOT be absent at the same time.
```

Then libraries and applications could be defined as the following:

```yaml
mod11:
  type:         lib
  desc:         moudle11 library
  opt:          CONFIG_MODULE11
  src:
    - $(SRC_PATH)/mod1/mod11
  hdrdirs:
    - $(SRC_PATH)/mod1/mod11/include
  cflags:
    all:      -DMOD11
    mod11.c:  -DMOD11_MOD11 -I$(SRC_PATH)/mod1/mod11/include

main:
  type:   app
  desc:   main application
  src:
    - $(SRC_PATH)/main/main.c
  cflags:
    - all:  -DMAIN
  libs:
    - mod11
    - mod12
```

### 3.2 How to add one module

1. Create one directory in the framework;
2. Add souce files and `YAML configuration file` to this module;
3. Add public header directory with public header files to this module as you need;
4. Add private header files to this module as you need;
5. Add Kconfig files(`*.config`) to this module，and include them from Kconfig in the root directory of the framework.

### 3.3 How to use

1. Intstall Make and Python3;
2. Install Kconfiglib:

    ```bash
    simple-build-framework$ pip3 install kconfiglib
    ```

3. Kconfiglib path may be need to be added to 'PATH' environment variable; for Linux, execute `export PATH=$PATH:~/.local/bin` in the shell or add this command to `~/.bashrc` or `~/.bash_profile`;
4. Configurate project:

    ```bash
    simple-build-framework$ python3 zmake.py ../build/zmake             # generate Makefile in ../build/zmake
    simple-build-framework$ python3 zmake.py ../build/zmake -g ninja    # generate build.ninja in ../build/zmake
    simple-build-framework$ python3 zmake.py ../build/zmake -V          # generate Makefile in ../build/zmake with verbose output enabled
    ```

    Note that all the options could be used:

    ```bash
    simple-build-framework$ python3 zmake.py --h
    usage: zmake.py [-h] [-v] [-V] [-d "defconfig file" | -m "Source Code Path"] [-g {make,ninja}] project

    zmake project builder

    positional arguments:
    project               project path

    optional arguments:
    -h, --help            show this help message and exit
    -v, --version         show version
    -V, --verbose         enable verbose output
    -d "defconfig file", --defconfig "defconfig file"
                            specify defconfig file
    -m "Source Code Path", --menuconfig "Source Code Path"
                            enable menuconfig method, used after project created ONLY
    -g {make,ninja}, --generator {make,ninja}
                            build generator
    ```

5. Build project:

    ```bash
    ../build/zmake$ make config     # configuration project
    ../build/zmake$ make            # build project
    ../build/zmake$ make clean      # clean project
    ../build/zmake$ make V=1        # build project with verbose output enabled
    ../build/zmake$ 
    ../build/zmake$ ninja config    # configuration project
    ../build/zmake$ ninja           # build project
    ../build/zmake$ ninja clean     # clean project
    ../build/zmake$ ninja -v        # build project with verbose output enabled
    ```

## 4. TODO

1. Split ZMake from this repo and transfer it to python package;
2. Add support for dynamic library.
