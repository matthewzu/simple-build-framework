import sys, os, re, argparse, pprint
import yaml, subprocess

# zmake

ZMAKE_VER = 'V0.1 20231023'
_VERBOSE = False

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
_KCONFIG_HDR            = 'config/config.h'
_KCONFIG_CONFIG         = 'config/prj.config'

def ver():
    return "zmake %s " % ZMAKE_VER

def create_dir(path):
    if os.path.exists(path):
        return

    if _VERBOSE:
        print("create %s" %path)

    os.makedirs(path)

def yml_file_load(path):
    global _YAML_FILES
    global _YAML_DATA

    if not os.path.isfile(path):
        print("yaml load: %s NOT exist" %path)
        return False

    if _VERBOSE:
        print("open %s" %path)

    fd = open(path, 'r', encoding='utf-8')

    if _VERBOSE:
        print("load %s" %path)

    data = yaml.safe_load(fd.read())
    if data == None:
        print("%s is empty" %path)
        return False

    if _VERBOSE:
        print("################yaml data####################")
        pprint.pprint(data)
        print("################yaml data end################")

    fd.close()
    _YAML_FILES += os.path.abspath(path)
    _YAML_DATA  = {**_YAML_DATA, **data}

    if 'includes' not in data:
        return True

    if data['includes'] == []:
        return True

    for file in data['includes']:
        yml_file_load(file)

    return True

def kconfig_init(defconfig):
    global _KCONFIG_DEFCONFIG
    global _KCONFIG_CONFIG_PATH
    global _KCONFIG_CONFIG
    global _KCONFIG_HDR

    if defconfig != '':
        if not os.path.exists(defconfig):
            print("%s is invalid path" %defconfig)
            sys.exit()
        else:
            _KCONFIG_DEFCONFIG = defconfig

    _KCONFIG_CONFIG_PATH = os.path.join(_PRJ_DIR, _KCONFIG_CONFIG_PATH)
    create_dir(_KCONFIG_CONFIG_PATH)

    _KCONFIG_CONFIG = os.path.join(_PRJ_DIR, _KCONFIG_CONFIG)
    _KCONFIG_HDR = os.path.join(_PRJ_DIR, _KCONFIG_HDR)

def kconfig_gen():
    if _VERBOSE:
        print("set KCONFIG_CONFIG to %s" %_KCONFIG_DEFCONFIG)

    os.environ['KCONFIG_CONFIG'] = _KCONFIG_DEFCONFIG
    
    if _VERBOSE:
        print("generate %s and %s" %(_KCONFIG_HDR, _KCONFIG_CONFIG))

    ret = subprocess.run(['genconfig', '--header-path', _KCONFIG_HDR, '--config-out', _KCONFIG_CONFIG])

    if ret.returncode != 0:
        print("failed to generate %s" %_KCONFIG_CONFIG)
        sys.exit()

def kconfig_menu():
    if not os.path.isfile(_KCONFIG_CONFIG):
        print("menuconfig method could ONLY be used after project"
            " is created and %s is existed" %_KCONFIG_CONFIG)
        sys.exit()
        
    if _VERBOSE:
        print("set KCONFIG_CONFIG to %s" %_KCONFIG_CONFIG)

    os.environ['KCONFIG_CONFIG'] = _KCONFIG_CONFIG
    ret = subprocess.run(['menuconfig'])

    if ret.returncode != 0:
        print("failed to run menuconfig")
        sys.exit()
    
    if _VERBOSE:
        print("generate %s and %s" %(_KCONFIG_HDR, _KCONFIG_CONFIG))

    ret = subprocess.run(['genconfig', '--header-path', _KCONFIG_HDR, '--config-out', _KCONFIG_CONFIG])

    if ret.returncode != 0:
        print("failed to generate %s" %_KCONFIG_CONFIG)
        sys.exit()

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

    if args.verbose:
        _VERBOSE = True

    if _VERBOSE:
        print("arguments:")
        print(" defconfig file              : %s" %args.defconfig)
        print(" enable menuconfig method    : %s" %args.menuconfig)
        print(" build generator             : %s" %args.generator)
        print(" cross compiler prefix       : %s" %args.cross_compile)
        print(" project path                : %s" %args.project)

    _SRC_TREE   = os.path.abspath('.')
    _PRJ_DIR    = os.path.abspath(args.project)
    _PRJ_GEN    = args.generator
    _CC_PREFIX  = args.cross_compile

    if not yml_file_load(_YAML_ROOT_FILE):
        sys.exit()

    kconfig_init(args.defconfig)
    
    if args.menuconfig:
        kconfig_menu()
    else:
        kconfig_gen()

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

# config:
#   type: target
#   cmd:  # optional, commands need be executed in shell
#     - mkdir -p $(PRJ_DIR)/config
#     - python3 $(KCONFIG_PATH)/genconfig.py --header-path=$(KCONFIG_HDR) --config-out=$(KCONFIG_CONFIG)
#     - python3 $(KCONFIG_PATH)/menuconfig.py
#     - python3 $(KCONFIG_PATH)/genconfig.py --header-path=$(KCONFIG_HDR) --config-out=$(KCONFIG_CONFIG)