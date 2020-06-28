#Simple Build Framework

## Overview

This is one simple build framework for the modularized softwares.

To make use this framework, you need:

1. split your entire software to one main module and several modules;
2. make sure all the files of one module in one directory;
3. add Kconfig file and moudle.mk for all the modules;
4. intstall Python3 and clone Kconfiglib from https://github.com/ulfalizer/Kconfiglib.git.

With this framework, you could:

1. add one module with one makefile segment(module.mk);
2. add one file to one existed module with the directory the module does exist or not;
3. specify compiler flags for one specified module or file(C/C++/Assemble);
4. specify output directory for objects/libraries/executable file;
5. confiure the modules with the Kconfig files.

## How to use

1. create your own modules refers to main/mod1/mod2;
2. add your source code to modules and add them and compiler flags for them to module.mk;
3. type **make OUT='project path' KCONFIG='Kconfiglib path' config** in root directory to create and configurate one project;
4. typpe **make OUT='project path'**/**make OUT='project path' clean** to build/clean the entire software and obtain the executable file **<project path>/main**.

**NOTE**:
you could use type **make help** to obtain the usage for all make commands.

## TODO

1. support for header files;
2. more configuration options(compiler, name of executable file, and so on).
