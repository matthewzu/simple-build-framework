#Simple Build Framework

## Overview 

This is one simple build framework for the modularized softwares.

To make use this framework, you need:
1.split your entire software to one main module and several modules;
2.make sure all the files of one module should be in the directories of the module.  

With this framework, you could:
1.add one module with one makefile segement(moudle.mk);
2.add one file to one existed module with the directory the module does exist or not;
3.specify compiler flags for one specfied module or file;
4.specify output directory for objects/libaries/executable file.

## How to use

1.create your own modules refers to main/mod1/mod2;
2.add your soucre code to moduls and add them and compiler flags for them to module.mk;
3.type **make** in root directory to build the entire software and obtain the executable file.
**main**.

**NOTE**: 
you could use type **make help** to obatin the usage for all make commands.

## TODO

1.support for C++/Assembly files and header files;
2.kconfig command(make config, make menuconfig, and so on);
3.more configuration options(compiler, name of executable file, level of debug information, and so on). 
