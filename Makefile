#Copyright 2016, 2023 Xiaofeng Zu
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

# Main makefile

# check build options and command an prepare

ifneq ($(MAKECMDGOALS),)
	ifeq ($(filter $(MAKECMDGOALS), config all clean help prehdr),)
		$(error Unsupported commands, try "make help" for more details)
	endif
endif

SRC_TREE 	:= $(shell pwd)

ifneq ($(MAKECMDGOALS), help)

ifeq ($(OUT), )
OUTPUT    		:= $(SRC_TREE)/output
$(warning default output directory ($(OUTPUT)) is used!)
else
OUT				:= $(subst \,/,$(OUT))
OUTPUT    		:= $(OUT)
endif

endif # MAKECMDGOALS != help

ifeq ($(MAKECMDGOALS), config)

ifeq ($(KCONFIG), )
KCONFIG_PATH 	:= $(SRC_TREE)/../Kconfiglib
$(warning default Kconfiglib directory ($(KCONFIG_PATH)) is used!)
else
KCONFIG			:= $(subst \,/,$(KCONFIG))
KCONFIG_PATH    := $(KCONFIG)
endif

ifeq ($(wildcard $(KCONFIG_PATH)/genconfig.py),)
$(error '$(KCONFIG_PATH)' is invalid path for Kconfiglib, obtain it refer to README.md)
endif

endif # MAKECMDGOALS == config

export KCONFIG_CONFIG=$(OUTPUT)/config/config.mk

ifeq ("$(origin V)", "command line")
	VREBOSE_BUILD = $(V)
endif

ifndef VREBOSE_BUILD
	VREBOSE_BUILD = 0
endif

ifeq ($(VREBOSE_BUILD),1)
	QUIET =
	Q =
	VERBOSE = v
else
	QUIET=quiet
	Q = @
	VERBOSE =
endif

default: all

# include config.mk

-include $(KCONFIG_CONFIG)

# process modules

MODULE_MKS	= $(shell find $(SRC_TREE) -name module.mk)
MODULE_HDRS = #
MODULES_y 	= #

# rules

define MODULE_MK_PROCESS

include $(1)

endef

define MODULE_OBJS_PROCESS

OBJS_$(1) += $(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).o
DEPS += $(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).d

endef

define MODULE_PROCESS
$(foreach module_obj, $(SRCS_$(1)_y), $(call MODULE_OBJS_PROCESS,$(1),$(module_obj)))
endef

# apply rules for all module to prepare objects

$(foreach module_mk, $(MODULE_MKS), $(eval $(call MODULE_MK_PROCESS,$(module_mk))))

# re-sort modules and remove repeated modules

APPS_y := $(sort $(APPS_y))
MODULES_y := $(sort $(MODULES_y)) $(APPS_y)
$(foreach module, $(MODULES_y), $(eval $(call MODULE_PROCESS,$(module))))

# filter out main module and prepare libraies

MODULES		:= $(filter-out $(APPS_y), $(MODULES_y))
LIBS		:= $(addprefix -l, $(MODULES))

# build mouldes

# rules

define MODULE_HDR_RULE

MODULE_HDRS += $(patsubst $(HDRDIR_$(1)_y)/%, $(OUTPUT)/include/%,$(2))

$(patsubst $(HDRDIR_$(1)_y)/%, $(OUTPUT)/include/%,$(2)): $(2)
	$(Q)$(if $(QUIET), echo '<$(1)>': CP $(basename $(notdir $(2))).h)
	$(Q)mkdir -p$(VERBOSE) $(dir $(patsubst $(HDRDIR_$(1)_y)/%, $(OUTPUT)/include/%,$(2)))
	$(Q)cp -fu$(VERBOSE) $(2) $(patsubst $(HDRDIR_$(1)_y)/%, $(OUTPUT)/include/%,$(2))

endef

define MODULE_OBJ_RULE.c

$(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).o : $(2)
	$(Q)$(if $(QUIET), echo '<$(1)>': CC $(basename $(notdir $(2))).o)
	$(Q)mkdir -p $(OUTPUT)/objs_$(1)
	$(Q)gcc -MD -I$(OUTPUT)/config -I$(OUTPUT)/include -c $$< -o $$@ $(CFLAGS_$(1)) $(CFLAGS_$(1)_$(basename $(notdir $(2))))
endef

define MODULE_OBJ_RULE.cpp

$(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).o : $(2)
	$(Q)$(if $(QUIET), echo '<$(1)>': CPP $(basename $(notdir $(2))).o)
	$(Q)mkdir -p $(OUTPUT)/objs_$(1)
	$(Q)gcc -MD -I$(OUTPUT)/config -c $$< -o $$@ $(CPPFLAGS_$(1)) $(CPPFLAGS_$(1)_$(basename $(notdir $(2))))
endef

define MODULE_OBJ_RULE.s

$(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).o : $(2)
	$(Q)$(if $(QUIET), echo '<$(1)>': AS $(basename $(notdir $(2))).o)
	$(Q)mkdir -p $(OUTPUT)/objs_$(1)
	$(Q)gcc -MD -I$(OUTPUT)/config -c $$< -o $$@ $(ASMFLAGS_$(1)) $(ASMFLAGS_$(1)_$(basename $(notdir $(2))))
endef

define MODULE_RULE

$(foreach module_hdr, $(HDRS_$(1)_y), $(call MODULE_HDR_RULE,$(1),$(module_hdr)))

$(foreach module_obj, $(SRCS_$(1)_y), $(call MODULE_OBJ_RULE$(suffix $(module_obj)),$(1),$(module_obj)))

ifneq ($(findstring $(1), $(APPS_y)),)
$(1): $(OBJS_$(1))
	$(Q)$(if $(QUIET), echo '<main>': LK $(1))
	$(Q)gcc -o $(OUTPUT)/$$@ $$^ -L$(OUTPUT) $(LIBS)
else
$(1): $(patsubst $(HDRDIR_$(1)_y)/%,$(OUTPUT)/include/%,$(HDRS_$(1)_y)) $(OBJS_$(1))
	$(Q)$(if $(QUIET), echo '<$$@>': AR lib$$@.a)
	$(Q)ar crs$(VERBOSE) $(OUTPUT)/lib$$@.a $$^
endif
endef

# apply rules for all module to generate library

$(foreach module, $(MODULES_y), $(eval $(call MODULE_RULE,$(module))))

# include depends files

ifneq ($(strip $(DEPS)),)
-include $(DEPS)
endif

# build command

prehdr: $(MODULE_HDRS)

config: $(MODULE_CFGS)
	$(Q)mkdir -p $(OUTPUT)/config
	$(Q)python3 $(KCONFIG_PATH)/genconfig.py --header-path=$(OUTPUT)/config/config.h --config-out=$(KCONFIG_CONFIG)
	$(Q)python3 $(KCONFIG_PATH)/menuconfig.py
	$(Q)python3 $(KCONFIG_PATH)/genconfig.py --header-path=$(OUTPUT)/config/config.h --config-out=$(KCONFIG_CONFIG)
	make -C $(SRC_TREE) prehdr

all: $(MODULES) $(APPS_y)
	@echo Generated $(APPS_y) to $(OUTPUT)/

clean:
	@rm -rf $(OUTPUT)/*

help:
	@echo 'Build:'
	@echo '    make [options] [command]'
	@echo '----------------------------------------------------------------------------------------'
	@echo 'SYNOPSIS:'
	@echo '    make [OUT=<path for output>] KCONFIG=<path for Kconfiglib> V=0|1 [command]'
	@echo '----------------------------------------------------------------------------------------'
	@echo 'command:'
	@echo '    config- configure all modules and generate header and mk'
	@echo '    all   - build all modules and generate finally output'
	@echo '    clean - clean all generated files'
	@echo '    help  - help message'
	@echo ''
	@echo 'Note that "all" will be used if [target] is absent.'
	@echo '----------------------------------------------------------------------------------------'
	@echo 'options:'
	@echo '    OUT   	- path for output directory, will be "$(SRC_TREE)/output" if absent.'
	@echo '    KCONFIG 	- path for Kconfiglib directory, will be "$(SRC_TREE)/../Kconfiglib" if absent,'
	@echo '                  could be obtained by "git clone https://github.com/ulfalizer/Kconfiglib.git"'
	@echo '    V   		- verbos level for debug level, 0 - no debug information 1 - display debug information'
	@echo ''

