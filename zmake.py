import sys, os, re, argparse, pprint
import yaml, subprocess
import logging, fnmatch

logging.basicConfig(level = logging.DEBUG, format = '%(levelname)s[%(asctime)s]:%(message)s')

# global 

ZMAKE_VER = 'V0.1 20231023'

# project

_SRC_TREE   = ''    # source code path
_PRJ_DIR    = ''    # project path
_PRJ_GEN    = ''    # build generator
_CC_PREFIX  = ''    # cross compiler prefix

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
        if type not in _ZMAKE_ENT_TYPES:
            raise _zmake_exception("invalid type for ZMake Entity(%s)" %type)
        
        if not isinstance(name, str):
            raise _zmake_exception("'name' MUST be str for ZMake Entity(%s)" %(name, name))
        
        if not isinstance(desc, str):
            raise _zmake_exception("'desc' MUST be str for ZMake Entity(%s)" %(name, name))

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

        logging.info("create ZMake variable %s\n\tdesc = %s val = %s",
            name, desc, str(self.val))
        zmake_var._vars.setdefault(name, self)

    # internal functions, find ZMake variable object by name

    @staticmethod
    def _find(name):
        if name in zmake_var._vars:
            return zmake_var._vars[name]
        else:
            return None

    # internal functions, check whether a string is a reference to ZMake
    # variable object and return ZMake variable name

    @staticmethod
    def _is_reference(var_expr):
        reg_var = re.compile('\$\((\S*)\)')
        temp = reg_var.search(var_expr)
        if temp != None:
            var_name = temp.group(1)
            return var_name
        else:
            return None

    # dereference a string including some reference strings to ZMake variable objects，
    # and replace reference strings to value of ZMake variable object.

    @staticmethod
    def dereference(expr: str):
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

class _zmake_obj(zmake_entity):
    """ZMake Object
        name:   string, full source path including file name('*.c', '*.cpp', '*.s' or '*.S')
        type:   string, one of `c`, `cpp` and `asm`
        desc:   string, ignored
        flags:  string, compiler flags
    """

    def __new__(cls, name, desc = "", flags = ''):
            return super(_zmake_obj, cls).__new__(cls, name, _ZMAKE_ENT_TYPE_OBJ, desc)

    def __init__(self, name, desc = "", flags = ''):
        self.name   = name
        self.flags = flags
        logging.info("create ZMake Object %s\n\tflags = %s", name, flags)

class _zmake_module(zmake_entity):
    """ZMake module - application/library
        name:       string, the name of the entity
        type:       string, the content is "var" and need not be specified
        src:                    # list, source files or directories:
            - $(ZMake variable name)/xxx/xxx.c
            - $(ZMake variable name)/xxx  # for directory, all source files in it will be involved
        desc:       string, optional, the description of the entity
        cflags:                 # optional, additional compiler flags for C files
            all:      xxx       # compiler flags for all C files
            xxx.c:    xxx       # compiler flags for xxx.c
        cppflags:               # optional, additional compiler flags for cpp files
            all:      xxx       # compiler flags for all CPP files
            xxx.cpp:  xxx       # compiler flags for xxx.cpp
        asmflags:   xxx         # optional, additional compiler flags for assembly files
            all:      xxx       # compiler flags for all assembly files
            xxx.s:    xxx       # compiler flags for xxx.s
            xxx.S:    xxx       # compiler flags for xxx.S
    """

    def __new__(cls, name, type, src, desc = "", cflags = {}, cppflags = {}, asmflags = {}):
        if type != _ZMAKE_ENT_TYPE_APP and type != _ZMAKE_ENT_TYPE_LIB:
            raise _zmake_exception("invalid type %s for ZMake module(%s)" %(type, name))

        if not isinstance(src, list):
            raise _zmake_exception("'src' (%s) MUST be list for ZMake module(%s)" %(src, name))

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
                self.src.setdefault(file_name, _zmake_obj(file, type, flags = file_flags))

    # find source files from specified path
    # 1) if path is a file and exists, then return a list including given path;
    # 2) if path is a directory and exists, then search and return a list including paths
    # of all source file('*.c', '*.cpp', '*.s' or '*.S')
    # 3) otherwise return {}

    @staticmethod
    def src_find(path):
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

    # find flags for specified file and type

    @staticmethod
    def _find_flags(file_name, type, cflags, cppflags, asmflags):
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
                    raise _zmake_exception("compiler flags(%s) MUST be dict for ZMake module(%s)" %(flags))
            else:
                raise _zmake_exception("compiler flags(%s) MUST be dict for ZMake module(%s)" %(flags))

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
            all:      xxx       # compiler flags for all C files
            xxx.c:    xxx       # compiler flags for xxx.c
        cppflags:               # optional, additional compiler flags for cpp files
            all:      xxx       # compiler flags for all CPP files
            xxx.cpp:  xxx       # compiler flags for xxx.cpp
        asmflags:   xxx         # optional, additional compiler flags for assembly files
            all:      xxx       # compiler flags for all assembly files
            xxx.s:    xxx       # compiler flags for xxx.s
            xxx.S:    xxx       # compiler flags for xxx.S
    """
    
    _libs = {}

    def __new__(cls, name, src, desc = "", hdrdirs = [], cflags = {}, cppflags = {}, asmflags = {}):
        if not isinstance(hdrdirs, list):
            raise _zmake_exception("'hdrdirs' MUST be list for ZMake library(%s)" %(hdrdirs, name))

        return super(zmake_lib, cls).__new__(cls, 
            name, _ZMAKE_ENT_TYPE_LIB, src, desc, cflags, cppflags, asmflags)

    def __init__(self, name, src, desc = "", hdrdirs = [], cflags = {}, cppflags = {}, asmflags = {}):
        super(zmake_lib, self).__init__(name, _ZMAKE_ENT_TYPE_LIB, src, desc, cflags, cppflags, asmflags)
        
        self.hdrdirs = []
        for dir in hdrdirs:
            self.hdrdirs.append(zmake_var.dereference(dir))

        logging.info("create ZMake library %s\n\tdesc = %s\n\tsrc = %s\n\thdrdirs = %s",
            name, desc, pprint.pformat(self.src), pprint.pformat(self.hdrdirs))
        zmake_lib._libs.setdefault(name, self)

class zmake_app(_zmake_module):
    """ZMake application
        name:       string, the name of the entity
        src:                    # list, source files or directories:
            - $(ZMake variable name)/xxx/xxx.c
            - $(ZMake variable name)/xxx  # for directory, all source files in it will be involved
        desc:       string, optional, the description of the entity
        cflags:                 # optional, additional compiler flags for C files
            all:      xxx       # compiler flags for all C files
            xxx.c:    xxx       # compiler flags for xxx.c
        cppflags:               # optional, additional compiler flags for cpp files
            all:      xxx       # compiler flags for all CPP files
            xxx.cpp:  xxx       # compiler flags for xxx.cpp
        asmflags:   xxx         # optional, additional compiler flags for assembly files
            all:      xxx       # compiler flags for all assembly files
            xxx.s:    xxx       # compiler flags for xxx.s
            xxx.S:    xxx       # compiler flags for xxx.S
    """
    
    _apps = {}
    def __new__(cls, name, src, desc = "", cflags = {}, cppflags = {}, asmflags = {}):
        return super(zmake_app, cls).__new__(cls, 
            name, _ZMAKE_ENT_TYPE_APP, src, desc, cflags, cppflags, asmflags)
    
    def __init__(self, name, src, desc = "", cflags = {}, cppflags = {}, asmflags = {}):
        super(zmake_app, self).__init__(name, _ZMAKE_ENT_TYPE_APP, src, desc, cflags, cppflags, asmflags)
        logging.info("create ZMake application %s\n\tdesc = %s\n\tsrc = %s",
            name, desc, pprint.pformat(self.src))
        zmake_app._apps.setdefault(name, self)

class zmake_target(zmake_entity):
    """ZMake target
        name: string, the name of the entity
        desc: string, optional, the description of the entity
        cmd:  dict, optional, commands that need be executed with description:
            desc:   command
        deps: list, optional, modules depended:
            - libXXX
            - appXXX
    """

    _targets = {}

    def __new__(cls, name, desc = "", cmd = {}, deps = {}):
        if not isinstance(cmd, dict):
            raise _zmake_exception("'cmd' MUST be dict for ZMake target(%s)" %(cmd, name))

        if not isinstance(deps, list):
            raise _zmake_exception("'deps' MUST be dict for ZMake target(%s)" %(deps, name))

        return super(zmake_target, cls).__new__(cls, name, _ZMAKE_ENT_TYPE_TGT, desc)

    def __init__(self, name, desc = "", cmd = {}, deps = {}):
        self.name   = name
        self.desc   = desc
        self.cmd    = cmd
        self.deps   = deps
        logging.info("create ZMake target %s\n\tdesc = %s\n\tcmd = %s\n\tdeps = %s",
            name, desc, pprint.pformat(cmd), pprint.pformat(deps))
        zmake_target._targets.setdefault(name, self)

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

    if defconfig != '':
        if not os.path.exists(defconfig):
            raise _zmake_exception("%s is invalid path" %defconfig)
        else:
            _KCONFIG_DEFCONFIG = os.path.abspath(defconfig)

    _KCONFIG_CONFIG_PATH = os.path.abspath(_KCONFIG_CONFIG_PATH)
    logging.info("Create Kconfig output directory %s", _KCONFIG_CONFIG_PATH)
    _KCONFIG_CONFIG_PATH = os.path.join(_PRJ_DIR, _KCONFIG_CONFIG_PATH)
    create_dir(_KCONFIG_CONFIG_PATH)

    _KCONFIG_CONFIG = os.path.join(_KCONFIG_CONFIG_PATH, _KCONFIG_CONFIG)
    _KCONFIG_HDR = os.path.join(_KCONFIG_CONFIG_PATH, _KCONFIG_HDR)

def kconfig_gen():
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
                logging.info(line)
                _KCONFIG_MODULE_OPTIONS.append(temp.group(1)) 

def kconfig_options_find(opt):
    return opt in _KCONFIG_MODULE_OPTIONS

# Yaml functions

def yml_file_load(path):
    global _YAML_FILES
    global _YAML_DATA

    if not os.path.isfile(path):
        raise _zmake_exception("yaml load: %s NOT exist" %path)

    logging.info("open %s", path)
    fd = open(path, 'r', encoding='utf-8')

    logging.info("load %s", path)
    data = yaml.safe_load(fd.read())
    if data == None:
        raise _zmake_exception("%s is empty" %path)

    fd.close()
    _YAML_FILES += os.path.abspath(path)
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
        logging.info("parse YAML object %s:\n\t%s", name, pprint.pformat(config))
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
                config.get("asmflags", {}))
        elif obj_type == _ZMAKE_ENT_TYPE_TGT:
            zmake_target(name, config.get("desc", ""), config.get("cmd", {}),
                config.get("deps", {}))
        else:
            logging.warning("invalid object type %s for YAML Object %s", obj_type, name)
            continue
        
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
                        default = '',
                        help    = 'defconfig file')
    group.add_argument("-m", "--menuconfig",
                        default = False, action ='store_true',
                        help    = 'enable menuconfig method, \nused after project created ONLY')

    parser.add_argument("-g", "--generator",
                        default = 'make', choices = ['make'],
                        help    = 'build generator')
    parser.add_argument("-c", "--cross-compile",
                        default = '',
                        help    = 'cross compiler prefix(for exmaple, aarch64-linux-gnu-)')
    parser.add_argument("project",
                        help    ='project path')

    args = parser.parse_args()

    if not args.verbose:
        logging.disable(logging.INFO)   # disable Debug/INFO logging

    logging.info("arguments:")
    logging.info(" defconfig file              : %s", args.defconfig)
    logging.info(" enable menuconfig method    : %s", args.menuconfig)
    logging.info(" build generator             : %s", args.generator)
    logging.info(" cross compiler prefix       : %s", args.cross_compile)
    logging.info(" project path                : %s", args.project)

    _SRC_TREE   = os.path.abspath('.')
    _PRJ_DIR    = os.path.abspath(args.project)
    _PRJ_GEN    = args.generator
    _CC_PREFIX  = args.cross_compile

    kconfig_init(args.defconfig)
    
    if args.menuconfig:
        kconfig_menu()
    else:
        kconfig_gen()
        
    kconfig_parse()
    
    yml_file_load(_YAML_ROOT_FILE)
    
    _SRC_TREE = os.path.abspath(os.getcwd())
    zmake_var("SRC_PATH", _SRC_TREE, "source code path")
    zmake_var("PRJ_PATH", _PRJ_DIR, "project path")
    yml_file_parse()

#help:
#  type: target
#  desc: |       # optional, only for display
#    Build:
#      make [options] [command]
#      ----------------------------------------------------------------------------------------
#      SYNOPSIS:
#          make V=0|1 [command]
#      ----------------------------------------------------------------------------------------
#      command:
#          config    - configure all modules and generate header and mk
#          all       - build all modules and generate finally output
#          clean     - clean all compiled files
#          distclean - clean all compiled/generated files
#          help      - print help message
#          info      - print informations for all moudles
#
#      Note that "all" will be used if [target] is absent.
#      ----------------------------------------------------------------------------------------
#      options:
#          V         - verbos level for debug level, 0 - no debug information 1 - display debug information
#  # cmd:  xxx     # optional, commands need be executed in shell
#  # depneds: xxx  # optional, target dependent modules
