# Simple Build Framework

## Overview

This is one simple build framework for the modularized softwares. It makes use of Makefile and Kconfig. The following are required:
* GNU Make tool;
* Python3;
* [github.com/ulfalizer/Kconfiglib](https://github.com/ulfalizer/Kconfiglib)

Simple build framework has the following features:

1. Multiple applications and libraries are supported;
2. Multiple level modules are supported;
3. Each module has its own public and/or private header files, source files(C/C++/assembly), Kconfig scripts and Makefile segment;
4. All the files that belongs to one module are placed in one directory;
5. The following attribute of the moulde could be specified:

   * Name;
   * Type, application or library;
   * Public header directory;
   * Source files;
   * Compiler flags;

6. The following attribute of the source files could be specified:

    * Compiler flags;

7. Kconfig scripts starts at Kconfig in the root directory, and could be modify as you need;
8. The header files in the public header directories of the enabled modules will be copied to `include` directory of the output directory and keep their own structures, and will be added to the compile flags for all the source files, so the module pathes could be ignored while including the public header files.

## Module Makefile Segment

Simple build framework confgure the modules by Makefile segments, which must be named as `module.mk`, and has the following options:

```Makefile
# moudle configuration 

# type: application - APPS_XXX moulde - MODULES_XXX
# Enable/Disable: Kconfig option - CONFIG_XXX
# name: <moulde name>, could be one or more
MODULES_<$(CONFIG_XXX)> += <moulde name>
APPS_<$(CONFIG_XXX)>    += <moulde name>

# source files, could be one or more
SRCS_<moulde name>_<$(CONFIG_XXX)>	    = $(SRC_TREE)/<moulde path>/xxx.x

# base directory for header files, one must and only
HDRDIR_<moulde name>_<$(CONFIG_XXX)>	= $(SRC_TREE)/<moulde path>/xxx

# header files, could be one or more
HDRS_<moulde name>_<$(CONFIG_XXX)>	    = HDRDIR_<moulde name>_<$(CONFIG_XXX)>/xxx/xxx.x

# Compiler flags for moudle
CFLAGS_<moulde name> 			        = xxx
CPPFLAGS_<moulde name> 			        = xxx
ASMFLAGS_<moulde name> 			        = xxx

# Compiler flags for moudle souce file
CFLAGS_<moulde name>_<source file name>     = xxx
CPPFLAGS_<moulde name>_<source file name>   = xxx
ASMFLAGS_<moulde name>_<source file name>   = xxx
```

## How to add one module

1. Create one directory in the framework;
2. Add souce files and `module.mk` to this module;
3. Add public header directory with public header files to this module; as you need;
4. Add private header files to this module; as you need;
5. Add Kconfig files(`*.config`) to this module; and include them from Kconfig in the root directory of the framework.

## How to use

1. Intstall Make and Python3;
2. Clone [github.com/ulfalizer/Kconfiglib](https://github.com/ulfalizer/Kconfiglib);
3. Configurate project:

    ```bash
    simple-build-framework$ make OUT=<project path> KCONFIG=<Kconfiglib path>
    ```

4. Build project:

    ```bash
    simple-build-framework$ make OUT=<project path>
    simple-build-framework$ make OUT=<project path> clean
    ```

**NOTE** that **make help** could be used to obtain the usage for all make commands. 

## TODO

1. compiler;
2. Add `Ninja + Python` corresponding to `Makefile`.
