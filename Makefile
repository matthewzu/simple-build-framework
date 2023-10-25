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

MODULE_MKS			= $(shell find $(SRC_TREE) -name module.mk)
MODULES_y 			= #
MODULES_HDRDIR_y	= #

# rules

define MODULE_MK_PROCESS

include $(1)

endef

define MODULE_OBJS_PROCESS

OBJS_$(1) += $(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).o
DEPS += $(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).d
MODULES_HDRDIR_y += $(HDRDIR_$(1)_y)
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

MODULES_HDRDIR_y += $(OUTPUT)/config
INCS := $(addprefix -I, $(MODULES_HDRDIR_y))

# filter out application module and prepare libraies

MODULES		:= $(filter-out $(APPS_y), $(MODULES_y))
LIBS		:= $(addprefix -l, $(MODULES))

# build mouldes

# rules

define MODULE_OBJ_RULE.c

$(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).o : $(2)
	$(Q)$(if $(QUIET), echo '<$(1)>': CC $(basename $(notdir $(2))).o)
	$(Q)mkdir -p $(OUTPUT)/objs_$(1)
	$(Q)gcc -MD $(INCS) -c $$< -o $$@ $(CFLAGS_$(1)) $(CFLAGS_$(1)_$(basename $(notdir $(2))))
endef

define MODULE_OBJ_RULE.cpp

$(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).o : $(2)
	$(Q)$(if $(QUIET), echo '<$(1)>': CPP $(basename $(notdir $(2))).o)
	$(Q)mkdir -p $(OUTPUT)/objs_$(1)
	$(Q)gcc -MD $(INCS) -c $$< -o $$@ $(CPPFLAGS_$(1)) $(CPPFLAGS_$(1)_$(basename $(notdir $(2))))
endef

define MODULE_OBJ_RULE.s

$(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).o : $(2)
	$(Q)$(if $(QUIET), echo '<$(1)>': AS $(basename $(notdir $(2))).o)
	$(Q)mkdir -p $(OUTPUT)/objs_$(1)
	$(Q)gcc -MD -$(INCS) -c $$< -o $$@ $(ASMFLAGS_$(1)) $(ASMFLAGS_$(1)_$(basename $(notdir $(2))))
endef

define MODULE_RULE

$(foreach module_obj, $(SRCS_$(1)_y), $(call MODULE_OBJ_RULE$(suffix $(module_obj)),$(1),$(module_obj)))

ifneq ($(findstring $(1), $(APPS_y)),)
$(1): $(OBJS_$(1))
	$(Q)$(if $(QUIET), echo '<main>': LK $(1))
	$(Q)gcc -o $(OUTPUT)/$$@ $$^ -L$(OUTPUT) $(LIBS)
else
$(1): $(OBJS_$(1))
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

config: $(MODULE_CFGS)
	$(Q)mkdir -p $(OUTPUT)/config
	$(Q)menuconfig
	$(Q)genconfig --header-path=$(OUTPUT)/config/config.h --config-out=$(KCONFIG_CONFIG)

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

