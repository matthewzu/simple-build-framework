#!/usr/bin/python
# -*- coding: utf-8 -*-
#Copyright 2023 Xiaofeng Zu
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

import sys, os, re, argparse, pprint
import yaml, subprocess
import logging, fnmatch, time

logging.basicConfig(level = logging.DEBUG, format = '%(levelname)s[%(asctime)s]:%(message)s')

# global

ZMAKE_VER = 'V0.1 20231023'

# project

_SRC_TREE   = ''    # source code path
_PRJ_DIR    = ''    # project path
_PRJ_GEN    = ''    # build generator
_PRJ_VREB   = 0     # enable verbose output

# build generator types

_PRJ_GEN_TYPE_MAKE  = 'make'
_PRJ_GEN_TYPE_NINJA = 'ninja'
_PRJ_GEN_TYPES      = ['make', 'ninja']

# yaml

_YAML_ROOT_FILE     = 'top.yml'     # top configuartion yaml
_YAML_FILES         = []
_YAML_DATA          = {}
_YAML_VARS          = {}
_YAML_TARGETS       = {}
_YAML_APPS          = {}
_YAML_LIBS          = {}

# Kconfig

_KCONFIG_DEFCONFIG      = ''
_KCONFIG_CONFIG_PATH    = "config"
_KCONFIG_HDR            = 'config.h'
_KCONFIG_CONFIG         = 'prj.config'
_KCONFIG_MODULE_OPTIONS = []    # CONFIG_XXX for modules

# zmake variables

_VARS           = {}
_VAR_SRC_PATH   = {'name': 'SRC_PATH', }

# source file types

_ZMAKE_SRC_TYPE_C   = "c"
_ZMAKE_SRC_TYPE_CPP = "cpp"
_ZMAKE_SRC_TYPE_ASM = "asm"
_ZMAKE_SRC_TYPES    = {"c": "*.c", "cpp": "*.cpp", "asm": "*.[sS]"}

# ZMake entity types

_ZMAKE_ENT_TYPE_VAR = "var"
_ZMAKE_ENT_TYPE_TGT = "target"
_ZMAKE_ENT_TYPE_APP = "app"
_ZMAKE_ENT_TYPE_LIB = "lib"
_ZMAKE_ENT_TYPE_OBJ = "obj"
_ZMAKE_ENT_TYPES = ("var", "target", "app", "lib", "obj")

# Excpetion Class

class _zmake_exception(Exception):
    def __init__(self, message):
        self.message = message

# ZMake Entity classes

class zmake_entity(object):
    """ZMake Entity:
        name: string, the name of the entity, must be unique for all entities
        type: string, the type of the entity
        desc: string, optional, the description of the entity
    """

    def __new__(cls, name, type, desc= ""):
        if not isinstance(name, str):
            raise _zmake_exception("'name' MUST be str for ZMake Entity" %str(name))

        if type not in _ZMAKE_ENT_TYPES:
            raise _zmake_exception("invalid type for ZMake Entity(%s)" %(str(type), name))

        if not isinstance(desc, str):
            raise _zmake_exception("'desc' MUST be str for ZMake Entity(%s)" %(str(name), name))

        return super(zmake_entity, cls).__new__(cls)

    def __str__(self):
        return '[ZMake Entity: %s Type: %s description: %s]' %(self.name, self.type, self.desc)

class zmake_var(zmake_entity):
    """ZMake variable
        name: string, the name of the entity
        desc: string, optional, the description of the entity
        val:  string that could include references to other variable'
        that have beed defined, such as '$(var_name)', or any value
    """

    _vars = {}

    def __new__(cls, name, val, desc = ""):
        if val == None:
            raise _zmake_exception("invalid value for ZMake variable %s" %name)
        else:
            return super(zmake_var, cls).__new__(cls, name, _ZMAKE_ENT_TYPE_VAR, desc)

    def __init__(self, name, val, desc = ""):
        self.name       = name
        self.desc       = desc

        if not isinstance(val, str):
            self.val    = val
        else:
            self.val    = zmake_var.dereference(val)

        logging.debug("create ZMake variable %s", name)
        logging.debug("\tdesc = %s val = %s", desc, str(self.val))
        zmake_var._vars.setdefault(name, self)

    @staticmethod
    def _find(name):
        """
        internal function, find ZMake variable object by name
            name:   string, name of ZMake variable object
            return: ZMake variable object, or None if not found
        """

        if name in zmake_var._vars:
            return zmake_var._vars[name]
        else:
            return None

    @staticmethod
    def _is_reference(var_expr):
        """
        internal functions, check whether a string is a reference
        to ZMake variable object
            var_expr:   string
            return:     ZMake variable name,
            or None if not a reference string to ZMake variable object
        """

        reg_var = re.compile('\$\((\S*)\)')
        temp = reg_var.search(var_expr)
        if temp != None:
            var_name = temp.group(1)
            return var_name
        else:
            return None

    @staticmethod
    def dereference(expr: str):
        """
        dereference a string including some reference strings to ZMake
        variable objects, and replace reference strings to value of ZMake
        variable object.
            expr:   string, a string including reference strings to ZMake
            variable objects
            return: string, in which reference strings have been replaced with
                value of ZMake variable object
        """

        pattern = r'(\$\(.*?\))'
        fragments = re.split(pattern, expr)
        for idx in range(len(fragments)):
            var_name = zmake_var._is_reference(fragments[idx])
            if var_name == None:
                continue    # not a reference string, so need to replace

            var = zmake_var._find(var_name)
            if var == None:
                raise _zmake_exception("%s could NOT be referenced before defined" %var_name)
            else:
                fragments[idx]  = var.val

        return ''.join(fragments)

    @staticmethod
    def reference_format(expr: str):
        if _PRJ_GEN == _PRJ_GEN_TYPE_NINJA:
            return re.sub(r"\(([^()]+)\)", r"\1", expr)
        else:
            return expr

    @staticmethod
    def all_make_gen(fd):
        """
        generate makefile segments for all ZMake variables and write fo file
        """
        for key, val in zmake_var._vars.items():
            logging.debug("generate variable %s", key)
            fd.write("%s\t= %s\n" %(key, str(val.val)))

        fd.write("\n")
        fd.flush()

    @staticmethod
    def all_ninja_gen(fd):
        """
        generate ninja segments for all ZMake variables and write fo file
        """
        for key, val in zmake_var._vars.items():
            logging.debug("generate variable %s", key)
            fd.write("%s = %s\n" %(key, str(val.val)))

        fd.write("\n")
        fd.flush()

class _zmake_obj(zmake_entity):
    """ZMake Object
        name:   string, full source path including file name('*.c', '*.cpp', '*.s' or '*.S')
        type:   string, one of `c`, `cpp` and `asm`
        desc:   string, ignored
        flags:  string, compiler flags
    """

    def __new__(cls, name, desc = "", flags = '', libname = ''):
            return super(_zmake_obj, cls).__new__(cls, name, _ZMAKE_ENT_TYPE_OBJ, desc)

    def __init__(self, name, desc = "", flags = '', libname = ''):
        self.name   = name
        self.flags  = '-I$(PRJ_PATH)/config ' + flags
        logging.debug("create ZMake Object %s", name)

        self._obj_dir   = os.path.join('$(PRJ_PATH)/objs', libname)
        self._obj_name  = os.path.join(self._obj_dir,
            os.path.splitext(os.path.basename(name))[0] + '.o')
        self._dep_name  = os.path.splitext(self._obj_name)[0] + '.d'

        self.name       = zmake_var.reference_format(self.name)
        self.flags      = zmake_var.reference_format(self.flags)
        self._obj_dir   = zmake_var.reference_format(self._obj_dir)
        self._obj_name  = zmake_var.reference_format(self._obj_name)
        self._dep_name  = zmake_var.reference_format(self._dep_name)
        logging.debug("\tname = %s", self.name)
        logging.debug("\tflags = %s", self.flags)
        logging.debug("\t_obj_dir = %s", self._obj_dir)
        logging.debug("\t_obj_name = %s", self._obj_name)
        logging.debug("\t_dep_name = %s", self._dep_name)

    def make_gen(self, fd, mod_name, added_flags):
        """
        generate makefile segments for specified ZMake objects with module name and write fo file
        """

        logging.debug("generate object %s", self.name)
        fd.write("%s: %s\n" %(self._obj_name, self.name))
        fd.write("\t$(Q)$(if $(QUIET), echo '<%s>': Compiling %s to %s)\n"
                %(mod_name, os.path.basename(self.name), (os.path.basename(self._obj_name))))
        fd.write("\t$(Q)mkdir -p$(VERBOSE) %s\n" %self._obj_dir)
        fd.write("\t$(Q)$(CC) %s %s -c $< -o $@\n" %(added_flags, self.flags))
        fd.write("\n")

    def ninja_gen(self, fd, mod_name, added_flags):
        """
        generate ninja segments for specified ZMake objects with module name and write fo file
        """

        logging.debug("generate object %s", self.name)
        fd.write("build %s: rule_mkdir\n" %self._obj_dir)
        fd.write("build %s: rule_cc %s | %s\n" %(self._obj_name, self.name, self._obj_dir))
        fd.write("    DEP = %s\n" %self._dep_name)
        fd.write("    FLAGS = %s %s\n" %(added_flags, self.flags))
        fd.write("    MOD = %s\n" %mod_name)
        fd.write("    SRC = %s\n" %os.path.basename(self.name))
        fd.write("    OBJ = %s\n" %os.path.basename(self._obj_name))
        fd.write("\n")

class _zmake_module(zmake_entity):
    """ZMake module - application/library
        name:       string, the name of the entity
        type:       string, the content is "var" and need not be specified\n
        src:                    # list, source files or directories
            - $(ZMake variable name)/xxx/xxx.c
            - $(ZMake variable name)/xxx  # for directory, all source
                                            files in it will be involved\n
        desc:       string, optional, the description of the entity\n
        cflags:                 # optional, additional compiler flags for C files\n
            all:      xxx       # string, compiler flags for all C files
            xxx.c:    xxx       # string, compiler flags for xxx.c
        cppflags:               # optional, additional compiler flags for cpp files
            all:      xxx       # string, compiler flags for all CPP files
            xxx.cpp:  xxx       # string, compiler flags for xxx.cpp
        asmflags:   xxx         # optional, additional compiler flags for assembly files
            all:      xxx       # string, compiler flags for all assembly files
            xxx.s:    xxx       # string, compiler flags for xxx.s
            xxx.S:    xxx       # string, compiler flags for xxx.S
    """

    def __new__(cls, name, type, src, desc = "", cflags = {}, cppflags = {}, asmflags = {}):
        if type != _ZMAKE_ENT_TYPE_APP and type != _ZMAKE_ENT_TYPE_LIB:
            raise _zmake_exception("invalid type %s for ZMake module(%s)" %(type, name))

        if not isinstance(src, list):
            raise _zmake_exception("'src' (%s) MUST be list for ZMake module(%s)" %(str(src), name))

        return super(_zmake_module, cls).__new__(cls, name, type, desc)

    def __init__(self, name, type, src, desc = "", cflags = {}, cppflags = {}, asmflags = {}):
        self.name   = name
        self.desc   = desc
        self.src    = {}

        for path in src:
            final_path = zmake_var.dereference(path)
            srcs = _zmake_module.src_find(final_path)
            for file, type in srcs.items():
                file_name = os.path.basename(file)
                file_flags = _zmake_module._find_flags(file_name, type,
                    cflags, cppflags, asmflags)

                reg_src_path = re.compile(_SRC_TREE)
                self.src.setdefault(file_name,
                    _zmake_obj(reg_src_path.sub("$(SRC_PATH)", file), type,
                        flags = file_flags, libname = name))

    def objs(self):
        """
        find all objects of this module and return a string includes all objects
        """
        found = []
        for obj in self.src.values():
            found.append(obj._obj_name)

        return ' '.join(found)

    def make_gen(self, fd, libname, added_flags):
        """
        generate makefile segments for all objects of this module and write fo file
        """
        
        deps = ""
        for key, obj in self.src.items():
            deps += " " + obj._dep_name
            obj.make_gen(fd, libname, added_flags)

        fd.write("-include %s\n\n" %deps)
        fd.flush()

    def ninja_gen(self, fd, libname, added_flags):
        """
        generate ninja segments for all objects of this module and write fo file
        """
        for key, obj in self.src.items():
            obj.ninja_gen(fd, libname, added_flags)

        fd.flush()

    @staticmethod
    def src_find(path: str):
        """
        find source files from specified path
            1) if path is a file and exists, then return a list including given path\n
            2) if path is a directory and exists, then search and return a list
            including paths of all source file('*.c', '*.cpp', '*.s' or '*.S')\n
            3) otherwise return {}\n
        """
        #

        if not os.path.exists(path):
            logging.warning("invalid path: %s", path)
            return {}

        srcs = {}
        if os.path.isfile(path):
            for type, pattern in _ZMAKE_SRC_TYPES.items():
                if fnmatch.fnmatch(path, pattern):
                    srcs.setdefault(os.path.abspath(path), type)
                    return srcs

        if os.path.isdir(path):
            for base, subdirs, files in os.walk(path):
                for type, pattern in _ZMAKE_SRC_TYPES.items():
                    matches = fnmatch.filter(files, pattern)
                    for src in matches:
                        srcs.setdefault(os.path.join(base, src), type)

        return srcs

    @staticmethod
    def _find_flags(file_name, type, cflags, cppflags, asmflags) -> str:
        """
        find flags for specified file and type
            return: string, compiler flags
        """
        if type == _ZMAKE_SRC_TYPE_C:
            flags = cflags
        elif type == _ZMAKE_SRC_TYPE_CPP:
            flags = cppflags
        elif type == _ZMAKE_SRC_TYPE_ASM:
            flags = asmflags
        else:
            raise _zmake_exception("invalid source type %s" %type)

        if not isinstance(flags, dict):
            if isinstance(flags, list):
                if len(flags) == 1 and isinstance(flags[0], dict):
                    flags = flags[0]
                else:
                    raise _zmake_exception("compiler flags(%s) MUST be dict" %str(flags))
            else:
                raise _zmake_exception("compiler flags(%s) MUST be dict" %str(flags))

        if not isinstance(flags.get("all", ""), str):
            raise _zmake_exception("compiler flags(%s) for 'all' MUST be string" %str(flags))

        if not isinstance(flags.get(file_name, ""), str):
            raise _zmake_exception("compiler flags(%s) for '%s' MUST be string" %(str(flags), file_name))

        return flags.get("all", "") + " " + flags.get(file_name, "")

class zmake_lib(_zmake_module):
    """ZMake library
        name:       string, the name of the entity
        src:                    # list, source files or directories:
            - $(ZMake variable name)/xxx/xxx.c
            - $(ZMake variable name)/xxx  # for directory, all source files in it will be involved
        desc:       string, optional, the description of the entity
        hdrdirs:                # string, optional, list, public header file directories
            - $(ZMake variable name)/xxx
        cflags:                 # optional, additional compiler flags for C files
            all:      xxx       # string, compiler flags for all C files
            xxx.c:    xxx       # string, compiler flags for xxx.c
        cppflags:               # optional, additional compiler flags for cpp files
            all:      xxx       # string, compiler flags for all CPP files
            xxx.cpp:  xxx       # string, compiler flags for xxx.cpp
        asmflags:   xxx         # optional, additional compiler flags for assembly files
            all:      xxx       # string, compiler flags for all assembly files
            xxx.s:    xxx       # string, compiler flags for xxx.s
            xxx.S:    xxx       # string, compiler flags for xxx.S
    """

    _libs = {}

    def __new__(cls, name, src, desc = "", hdrdirs = [], cflags = {}, cppflags = {}, asmflags = {}):
        if not isinstance(hdrdirs, list):
            raise _zmake_exception("'hdrdirs' MUST be list for ZMake library(%s)" %(str(hdrdirs), name))

        return super(zmake_lib, cls).__new__(cls,
            name, _ZMAKE_ENT_TYPE_LIB, src, desc, cflags, cppflags, asmflags)

    def __init__(self, name, src, desc = "", hdrdirs = [], cflags = {}, cppflags = {}, asmflags = {}):
        logging.debug("create ZMake library %s", name)
        super(zmake_lib, self).__init__(name, _ZMAKE_ENT_TYPE_LIB,
            src, desc, cflags, cppflags, asmflags)

        logging.debug("ZMake library %s details:", name)
        logging.debug("\tsrc(final) = %s", pprint.pformat(self.src))

        self.hdrdirs = []
        for dir in hdrdirs:
            self.hdrdirs.append(zmake_var.reference_format(dir))
        self._lib_name = 'lib' + name + '.a'

        logging.debug("\thdrdirs(final) = %s", pprint.pformat(self.hdrdirs))
        logging.debug("\t_lib_name = %s", self._lib_name)
        zmake_lib._libs.setdefault(name, self)

    @staticmethod
    def find(name):
        """
        internal function, find ZMake library object by name
            name:   string, name of ZMake library object
            return: ZMake library object, or None if not found
        """

        return zmake_lib._libs.get(name, None)

    @staticmethod
    def find_libs() -> []:
        """
        find all libraries
        """
        return list(zmake_lib._libs.keys())

    @staticmethod
    def all_make_gen(fd):
        """
        generate makefile segments for all libraries and write fo file
        """
        fd.write("# libraries\n\n")

        for name, lib in zmake_lib._libs.items():
            logging.debug("generate library %s", name)
            fd.write("# %s\n\n" %name)
            lib.make_gen(fd, name, "")

            fd.write("%s: %s\n" %(name, lib.objs()))
            fd.write("\t$(Q)$(if $(QUIET), echo '<%s>': Packaging)\n" %name)
            fd.write("\t$(Q)mkdir -p$(VERBOSE) $(PRJ_PATH)/libs\n")
            fd.write("\t$(Q)$(AR) crs$(VERBOSE) $(PRJ_PATH)/libs/%s $^\n" %lib._lib_name)
            fd.write("\n")
            fd.flush()

    @staticmethod
    def all_ninja_gen(fd):
        """
        generate ninja segments for all libraries and write fo file
        """

        fd.write("# libraries\n\n")
        fd.write("build $PRJ_PATH/libs: rule_mkdir\n")
        fd.write("\n")

        for name, lib in zmake_lib._libs.items():
            logging.debug("generate library %s", name)
            fd.write("# %s\n\n" %name)
            lib.ninja_gen(fd, name, "")

            fd.write("build %s: rule_ar %s | $PRJ_PATH/libs\n" %(name, lib.objs()))
            fd.write("    LIB = %s\n" %lib._lib_name)
            fd.write("    MOD = %s\n" %name)
            fd.write("\n")
            fd.flush()

class zmake_app(_zmake_module):
    """ZMake application
        name:       string, the name of the entity\n
        src:                    # list, source files or directories:
            - $(ZMake variable name)/xxx/xxx.c
            - $(ZMake variable name)/xxx  # for directory, all source
                                            files in it will be involved\n
        desc:       string, optional, the description of the entity
        cflags:                 # optional, additional compiler flags for C files
            all:      xxx       # string, compiler flags for all C files
            xxx.c:    xxx       # string, compiler flags for xxx.c
        cppflags:               # optional, additional compiler flags for cpp files
            all:      xxx       # string, compiler flags for all CPP files
            xxx.cpp:  xxx       # string, compiler flags for xxx.cpp
        asmflags:               # optional, additional compiler flags for assembly files
            all:      xxx       # string, compiler flags for all assembly files
            xxx.s:    xxx       # string, compiler flags for xxx.s
            xxx.S:    xxx       # string, compiler flags for xxx.S
        linkflags:    xxx       # string, optional, additional linker flags
        libs:       xxx         # list, optional, libraries depended:
            - xxx
    """

    _apps = {}
    def __new__(cls, name, src, desc = "", cflags = {}, cppflags = {}, asmflags = {}, linkflags = '', libs = []):
        if not isinstance(linkflags, str):
            raise _zmake_exception("'linkflags' MUST be string for ZMake application(%s)" %(str(linkflags), name))

        if not isinstance(libs, list):
            raise _zmake_exception("'linkflags' MUST be string for ZMake application(%s)" %(str(linkflags), name))

        return super(zmake_app, cls).__new__(cls,
            name, _ZMAKE_ENT_TYPE_APP, src, desc, cflags, cppflags, asmflags)

    def __init__(self, name, src, desc = "", cflags = {}, cppflags = {}, asmflags = {}, linkflags = '', libs = []):
        logging.debug("create ZMake application %s", name)
        super(zmake_app, self).__init__(name, _ZMAKE_ENT_TYPE_APP, src, desc, cflags, cppflags, asmflags)
        self.linkflags  = linkflags
        self._lib_dep   = ""
        self._lib_ld    = ""
        self._lib_hdrs  = ""
        logging.debug("ZMake application %s details:", name)
        logging.debug("\tsrc(final) = %s", pprint.pformat(self.src))

        for libname in libs:
            lib = zmake_lib.find(libname)
            if lib == None:
                raise _zmake_exception("invalid library(%s) for ZMake application(%s)" %(str(libname), name))
            else:
                self._lib_dep += " " + libname
                self._lib_ld  += " -l" + libname
                for libhdr in lib.hdrdirs:
                    self._lib_hdrs += " -I" + zmake_var.reference_format(libhdr)

        logging.debug("\t_lib_dep = %s", self._lib_dep)
        logging.debug("\t_lib_ld = %s", self._lib_ld)
        logging.debug("\t_lib_hdrs = %s", self._lib_hdrs)
        zmake_app._apps.setdefault(name, self)

    @staticmethod
    def find_apps() -> []:
        """
        find all applications
        """
        return list(zmake_app._apps.keys())

    @staticmethod
    def all_make_gen(fd):
        """
        generate makefile segments for all applications and write fo file
        """
        fd.write("# applications\n\n")

        for name, app in zmake_app._apps.items():

            logging.debug("generate application %s", name)
            fd.write("# %s\n\n" %name)
            app.make_gen(fd, name, app._lib_hdrs)

            objs = app.objs()
            fd.write("%s: %s %s\n" %(name, objs, app._lib_dep))
            fd.write("\t$(Q)$(if $(QUIET), echo '<%s>': Linking)\n" %name)
            fd.write("\t$(Q)mkdir -p$(VERBOSE) $(PRJ_PATH)/apps\n")
            fd.write("\t$(Q)$(LD) -o $(PRJ_PATH)/apps/$@ %s %s -L$(PRJ_PATH)/libs %s\n"
                %(objs, app.linkflags, app._lib_ld))
            fd.write("\n")
            fd.flush()

    @staticmethod
    def all_ninja_gen(fd):
        """
        generate ninja segments for all applications and write fo file
        """
        fd.write("# applications\n\n")
        fd.write("build $PRJ_PATH/apps: rule_mkdir\n")
        fd.write("\n")

        for name, app in zmake_app._apps.items():
            logging.debug("generate application %s", name)
            fd.write("# %s\n\n" %name)
            app.ninja_gen(fd, name, app._lib_hdrs)

            fd.write("build %s: rule_ld %s | $PRJ_PATH/apps %s\n"
                %(name, app.objs(), app._lib_dep))
            fd.write("    FLAGS = %s %s\n" %(app.linkflags, app._lib_ld))
            fd.write("    MOD = %s\n" %name)
            fd.write("\n")
            fd.flush()

class zmake_target(zmake_entity):
    """ZMake target
        name: string, the name of the entity
        desc: string, optional, the description of the entity
        cmd:  string, optional, commands that need be executed with description
        deps: list, optional, modules depended
            - xxx

        Note that 'cmd' and 'deps' MUST NOT be absent at the same time.
    """

    _targets = {}

    def __new__(cls, name, desc = "", cmd = "", deps = []):
        if not isinstance(cmd, str):
            raise _zmake_exception("'cmd' MUST be string for ZMake target(%s)" %(str(cmd), name))

        if not isinstance(deps, list):
            raise _zmake_exception("'deps' MUST be list for ZMake target(%s)" %(str(deps), name))

        if cmd == "" and deps == []:
            raise _zmake_exception("'cmd' and 'deps' MUST NOT be absent at the same time for ZMake target(%s)" %name)

        return super(zmake_target, cls).__new__(cls, name, _ZMAKE_ENT_TYPE_TGT, desc)

    def __init__(self, name, desc = "", cmd = "", deps = []):
        self.name   = name
        self.desc   = desc
        self.cmd    = cmd
        self.deps   = deps
        logging.debug("create ZMake target %s\n\tdesc = %s\n\tcmd = %s\n\tdeps = %s",
            name, desc, pprint.pformat(cmd), pprint.pformat(deps))

        self.cmd    = zmake_var.reference_format(self.cmd)
        zmake_target._targets.setdefault(name, self)

    def make_gen(self, fd):
        """
        generate makefile segments for specified target and write fo file
        """
        if self.deps == []:
            fd.write(".PHONY: %s\n" %self.name)
            fd.write("%s:\n" %self.name)
        else:
            fd.write("%s: %s\n" %(self.name, ' '.join(self.deps)))

        if self.desc != "":
            fd.write("\t@echo %s\n" %self.desc)

        if self.cmd != "":
            fd.write("\t$(Q)%s\n" %self.cmd)

        fd.write("\n")

    def ninja_gen(self, fd):
        """
        generate ninja segments for specified target and write fo file
        """
        if self.cmd == "":
            fd.write("build %s: phony %s\n" %(self.name, ' '.join(self.deps)))
        else:
            fd.write("build cmd_%s: rule_cmd\n" %self.name)
            fd.write("    pool = console\n")
            fd.write("    CMD = %s\n" %self.cmd)

        if self.desc != "":
            fd.write("    DESC = %s\n" %self.desc)

        if self.cmd != "":
            fd.write("build %s: phony cmd_%s\n" %(self.name, self.name))

        fd.write("\n")

    @staticmethod
    def find_targets() -> []:
        """
        find all targets
        """
        return list(zmake_target._targets.keys())

    @staticmethod
    def all_make_gen(fd):
        """
        generate makefile segments for all targets and write fo file
        """
        fd.write("# targets\n\n")

        for name, target in zmake_target._targets.items():
            fd.write("# %s\n\n" %name)
            target.make_gen(fd)
            fd.flush()

    @staticmethod
    def all_ninja_gen(fd):
        """
        generate ninja segments for all targets and write fo file
        """
        fd.write("# targets\n\n")

        for name, target in zmake_target._targets.items():
            fd.write("# %s\n\n" %name)
            target.ninja_gen(fd)

        fd.write("default all\n\n")
        fd.flush()

def zmake_sys_var_create():
    logging.info("create zmake system variables")
    zmake_var("SRC_PATH", _SRC_TREE, "source code path")
    zmake_var("PRJ_PATH", _PRJ_DIR, "project path")
    zmake_var("KCONFIG_CONFIG", _PRJ_DIR, "Kconfig makefile output")

def zmake_sys_target_create():
    logging.info("create zmake system targets")

    config_cmd = "python3 $(SRC_PATH)/zmake.py -m $(SRC_PATH) $(PRJ_PATH)"
    if _PRJ_GEN == _PRJ_GEN_TYPE_NINJA:
        config_cmd += " -g ninja"
    if _PRJ_VREB == 1:
        config_cmd += " -V"
    zmake_target("config",
        desc = "configure project and generate header and mk",
        cmd = config_cmd)

    zmake_target("all", desc = "Build all applications and libraries",
        deps = zmake_lib.find_libs() + zmake_app.find_apps())

    zmake_target("clean",
        cmd = "rm -rf $(PRJ_PATH)/objs $(PRJ_PATH)/libs $(PRJ_PATH)/apps",
            desc = "Clean all generated files")

# basic functions

def ver():
    return "zmake %s " % ZMAKE_VER

def create_dir(path):
    if os.path.exists(path):
        return

    logging.info("create %s", path)
    os.makedirs(path)

# Kconfig functions

def kconfig_init(defconfig):
    global _KCONFIG_DEFCONFIG
    global _KCONFIG_CONFIG_PATH
    global _KCONFIG_CONFIG
    global _KCONFIG_HDR

    logging.info("set srctree to %s", _SRC_TREE)
    os.environ['srctree'] = _SRC_TREE

    if defconfig != '':
        if not os.path.exists(defconfig):
            raise _zmake_exception("%s is invalid path" %defconfig)
        else:
            _KCONFIG_DEFCONFIG = os.path.abspath(defconfig)

    _KCONFIG_CONFIG_PATH = os.path.join(_PRJ_DIR, _KCONFIG_CONFIG_PATH)
    logging.info("Create Kconfig output directory %s", _KCONFIG_CONFIG_PATH)
    create_dir(_KCONFIG_CONFIG_PATH)

    _KCONFIG_CONFIG = os.path.join(_KCONFIG_CONFIG_PATH, _KCONFIG_CONFIG)
    _KCONFIG_HDR = os.path.join(_KCONFIG_CONFIG_PATH, _KCONFIG_HDR)

def kconfig_gen():
    if _KCONFIG_DEFCONFIG == '':
        if 'KCONFIG_CONFIG' in os.environ:
            logging.info("unset KCONFIG_CONFIG")
            os.environ.pop('KCONFIG_CONFIG')
    else:
        logging.info("set KCONFIG_CONFIG to %s", _KCONFIG_DEFCONFIG)
        os.environ['KCONFIG_CONFIG'] = _KCONFIG_DEFCONFIG

    logging.info("generate %s and %s", _KCONFIG_HDR, _KCONFIG_CONFIG)
    ret = subprocess.run(['genconfig', '--header-path', _KCONFIG_HDR, '--config-out', _KCONFIG_CONFIG])

    if ret.returncode != 0:
        raise _zmake_exception("failed to generate %s" %_KCONFIG_CONFIG)

def kconfig_menu():
    if not os.path.isfile(_KCONFIG_CONFIG):
        raise _zmake_exception("menuconfig method could ONLY be used after project"
            " is created and %s is existed" %_KCONFIG_CONFIG)

    logging.info("set KCONFIG_CONFIG to %s", _KCONFIG_CONFIG)
    os.environ['KCONFIG_CONFIG'] = _KCONFIG_CONFIG

    logging.info("Execute menuconfig")
    ret = subprocess.run(['menuconfig'])

    if ret.returncode != 0:
        raise _zmake_exception("failed to run menuconfig")

    logging.info("generate %s and %s", _KCONFIG_HDR, _KCONFIG_CONFIG)
    ret = subprocess.run(['genconfig', '--header-path', _KCONFIG_HDR, '--config-out', _KCONFIG_CONFIG])

    if ret.returncode != 0:
        raise _zmake_exception("failed to generate %s" %_KCONFIG_CONFIG)

def kconfig_parse():
    global _KCONFIG_MODULE_OPTIONS

    if not os.path.isfile(_KCONFIG_CONFIG):
        raise _zmake_exception("yaml load: %s NOT exist" %_KCONFIG_CONFIG)

    pattern = re.compile('^CONFIG_(\S*)+=y')
    logging.info("parse %s", _KCONFIG_CONFIG)
    with open(_KCONFIG_CONFIG, 'r', encoding='utf-8') as file:
        for line in file:
            temp = pattern.search(line)
            if temp != None:
                logging.debug(line)
                _KCONFIG_MODULE_OPTIONS.append(temp.group(1))

def kconfig_options_find(opt):
    return opt in _KCONFIG_MODULE_OPTIONS

# Yaml functions

def yml_file_load(path):
    global _YAML_FILES
    global _YAML_DATA

    real_path = os.path.join(_SRC_TREE, path)
    if not os.path.isfile(real_path):
        raise _zmake_exception("yaml load: %s NOT exist" %real_path)

    logging.debug("open %s", real_path)
    fd = open(real_path, 'r', encoding='utf-8')

    logging.debug("load %s", real_path)
    data = yaml.safe_load(fd.read())
    if data == None:
        raise _zmake_exception("%s is empty" %real_path)

    fd.close()
    _YAML_FILES += os.path.abspath(real_path)
    _YAML_DATA  = {**_YAML_DATA, **data}

    if 'includes' not in data:
        return

    if data['includes'] == []:
        return

    for file in data['includes']:
        yml_file_load(file)

def yml_file_parse():
    del _YAML_DATA['includes']
    logging.info("parse YAML for ZMake objects")
    for name, config in _YAML_DATA.items():
        logging.debug("parse YAML object %s:\n%s", name, pprint.pformat(config))
        obj_type = config.get("type", "")
        if obj_type == _ZMAKE_ENT_TYPE_VAR:
            zmake_var(name, config.get("val", ""), config.get("desc", ""))
        elif obj_type == _ZMAKE_ENT_TYPE_LIB:
            zmake_lib(name, config.get("src", ""), config.get("desc", ""),
                config.get("hdrdirs", ""), config.get("cflags", ""),
                config.get("cppflags", ""), config.get("asmflags", ""))
        elif obj_type == _ZMAKE_ENT_TYPE_APP:
            zmake_app(name, config.get("src", []), config.get("desc", ""),
                config.get("cflags", {}), config.get("cppflags", {}),
                config.get("asmflags", {}), config.get("linkflags", ""),
                config.get("libs", []))
        elif obj_type == _ZMAKE_ENT_TYPE_TGT:
            zmake_target(name, config.get("desc", ""), config.get("cmd", {}),
                config.get("deps", {}))
        else:
            logging.warning("invalid object type %s for YAML Object %s", obj_type, name)
            continue


def make_gen():
    path = os.path.join(_PRJ_DIR, "Makefile")
    logging.info("generate %s", path)
    fd = open(path, 'w', encoding='utf-8')

    cur_time = time.asctime()
    fd.write("# Generated by Zmake %s on %s\n\n" %(ZMAKE_VER, cur_time))

    fd.write("default: all\n")
    fd.write("\n")

    fd.write("# variables\n")
    fd.write("\n")
    fd.flush()

    zmake_var.all_make_gen(fd)

    fd.write("ifneq ($(V), )\n")
    fd.write("\tVREBOSE_BUILD = $(V)\n")
    fd.write("else\n")
    fd.write("\tVREBOSE_BUILD = 0\n")
    fd.write("endif\n")
    fd.write("\n")

    fd.write("ifeq ($(VREBOSE_BUILD),1)\n")
    fd.write("\tQUIET =\n")
    fd.write("\tQ =\n")
    fd.write("\tVERBOSE = v\n")
    fd.write("else\n")
    fd.write("\tQUIET = quiet\n")
    fd.write("\tQ = @\n")
    fd.write("\tVERBOSE =\n")
    fd.write("endif\n")
    fd.write("\n")
    fd.flush()

    zmake_lib.all_make_gen(fd)
    zmake_app.all_make_gen(fd)
    zmake_target.all_make_gen(fd)

def ninja_gen():
    path = os.path.join(_PRJ_DIR, "build.ninja")
    logging.info("generate %s", path)
    fd = open(path, 'w', encoding='utf-8')

    cur_time = time.asctime()
    fd.write("# Generated by Zmake %s on %s\n" %(ZMAKE_VER, cur_time))
    fd.write("\n")
    fd.flush()

    fd.write("# variables\n")
    fd.write("\n")
    fd.flush()

    zmake_var.all_ninja_gen(fd)

    fd.write("# common rules\n")
    fd.write("\n")

    fd.write("rule rule_cmd\n")
    fd.write("    command = $CMD\n")
    fd.write("    description = $DESC\n")
    fd.write("\n")

    fd.write("rule rule_mkdir\n")
    fd.write("    command = mkdir -p $out\n")
    fd.write("    description = Creating $out\n")
    fd.write("\n")

    fd.write("rule rule_cc\n")
    fd.write("    depfile = $DEP\n")
    fd.write("    deps = gcc\n")
    fd.write("    command = $CC -MF $DEP -c $in -o $out $FLAGS\n")
    fd.write("    description = '<$MOD>': Compiling $SRC to $OBJ\n")
    fd.write("\n")

    fd.write("rule rule_ar\n")
    fd.write("    command = $AR crs $PRJ_PATH/libs/$LIB $in\n")
    fd.write("    description = '<$MOD>': Packaging\n")
    fd.write("\n")

    fd.write("rule rule_ld\n")
    fd.write("    command = $LD -o $PRJ_PATH/apps/$out $in -L$PRJ_PATH/libs $FLAGS\n")
    fd.write("    description = '<$MOD>': Linking\n")
    fd.write("\n")
    fd.flush()

    zmake_lib.all_ninja_gen(fd)
    zmake_app.all_ninja_gen(fd)
    zmake_target.all_ninja_gen(fd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="zmake project builder")

    parser.add_argument('-v', '--version',
                        action  = 'version', version = ver(),
                        help    = 'show version')
    parser.add_argument('-V', '--verbose',
                        default = False, action = 'store_true',
                        help    = 'enable verbose output')

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--defconfig",
                        default = '', metavar = '"defconfig file"',
                        help    = 'specify defconfig file')
    group.add_argument("-m", "--menuconfig",
                        default = '', metavar = '"Source Code Path"',
                        help    = 'enable menuconfig method, \nused after project created ONLY')

    parser.add_argument("-g", "--generator",
                        default = _PRJ_GEN_TYPE_MAKE, choices = _PRJ_GEN_TYPES,
                        help    = 'build generator')
    parser.add_argument("project",
                        help    ='project path')

    args = parser.parse_args()

    if args.verbose:
        _PRJ_VREB = 1
    else:
        logging.disable(logging.DEBUG)   # disable Debug/INFO logging

    logging.info("arguments:")
    logging.info(" defconfig file           : %s", args.defconfig)
    logging.info(" Source Code Path         : %s", args.menuconfig)
    logging.info(" build generator          : %s", args.generator)
    logging.info(" project path             : %s", args.project)

    if args.menuconfig == '':
        _SRC_TREE   = os.path.abspath('.')
    else:
        if not os.path.exists(args.menuconfig):
            raise _zmake_exception("invalid Source Code Path: %s" %args.menuconfig)
        else:
            _SRC_TREE = os.path.abspath(args.menuconfig)

    _PRJ_DIR    = os.path.abspath(args.project)
    _PRJ_GEN    = args.generator

    kconfig_init(args.defconfig)

    if args.menuconfig != '':
        kconfig_menu()
    else:
        kconfig_gen()

    kconfig_parse()
    yml_file_load(_YAML_ROOT_FILE)
    zmake_sys_var_create()
    yml_file_parse()
    zmake_sys_target_create()

    if _PRJ_GEN == _PRJ_GEN_TYPE_MAKE:
        make_gen()
    else:
        ninja_gen()
