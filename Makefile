#Copyright 2016 Xiaofeng Zu
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
	ifeq ($(filter $(MAKECMDGOALS), all clean help),)
		$(error Unsupported commands, try "make help" for more details)	
	endif
endif

SRC_TREE 	:= $(shell pwd)

ifeq ($(OUT), )
OUTPUT    	:= $(SRC_TREE)/output
$(warning default output directory ($(OUTPUT)) is used!)
else
OUT			:= $(subst \,/,$(OUT))
OUTPUT    	:= $(OUT)
endif

default: all

# process modules

MODULE_MKS	= $(shell find $(SRC_TREE) -name module.mk)
MODULES_ALL = #

# rules

define MODULE_MK_PROCESS

include $(1)

endef

define MODULE_OBJS_PROCESS

OBJS_$(1) += $(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).o
DEPS += $(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).d

endef

define MODULE_PROCESS
$(foreach module_obj, $(SRCS_$(1)), $(call MODULE_OBJS_PROCESS,$(1),$(module_obj)))
endef

# apply rules for all module to prepare objects

$(foreach module_mk, $(MODULE_MKS),$(eval $(call MODULE_MK_PROCESS,$(module_mk))))

# re-sort modules and remove repeated modules

MODULES_ALL := $(sort $(MODULES_ALL))
$(foreach module, $(MODULES_ALL),$(eval $(call MODULE_PROCESS,$(module))))

# filter out main module and prepare libraies

MODULES		:= $(filter-out main, $(MODULES_ALL)) 
LIBS		:= $(addprefix -l, $(MODULES))

# build mouldes

# rules

define MODULE_OBJ_RULE.c

$(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).o : $(2)
	@echo '<$(1)>': CC $(basename $(notdir $(2))).o
	@mkdir -p $(OUTPUT)/objs_$(1)
	@gcc -MD -c $$< -o $$@ $(CFLAGS_$(1)) $(CFLAGS_$(1)_$(basename $(notdir $(2))))
endef

define MODULE_OBJ_RULE.cpp

$(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).o : $(2)
	@echo '<$(1)>': CPP $(basename $(notdir $(2))).o
	@mkdir -p $(OUTPUT)/objs_$(1)
	@gcc -MD -c $$< -o $$@ $(CFLAGS_$(1)) $(CFLAGS_$(1)_$(basename $(notdir $(2))))
endef

define MODULE_OBJ_RULE.s

$(OUTPUT)/objs_$(1)/$(basename $(notdir $(2))).o : $(2)
	@echo '<$(1)>': AS $(basename $(notdir $(2))).o
	@mkdir -p $(OUTPUT)/objs_$(1)
	@gcc -MD -c $$< -o $$@ $(CFLAGS_$(1)) $(CFLAGS_$(1)_$(basename $(notdir $(2))))
endef

define MODULE_RULE

$(foreach module_obj, $(SRCS_$(1)), $(call MODULE_OBJ_RULE$(suffix $(module_obj)),$(1),$(module_obj)))

ifeq ($(1), main)
main: $(OBJS_$(1))
	@echo '<main>': LINK
	@gcc -o $(OUTPUT)/$$@ $$^ -L$(OUTPUT) $(LIBS) 
else
$(1): $(OBJS_$(1))
	@echo '<lib$$@.a>': PACK
	@ar -r $(OUTPUT)/lib$$@.a $$^
endif
endef 

# apply rules for all module to generate library

$(foreach module, $(MODULES_ALL),$(eval $(call MODULE_RULE,$(module))))

# include depends files

ifneq ($(strip $(DEPS)),)
DEPS_EXISTED = $(foreach dep, $(DEPS), $(wildcard $(obj)))

ifneq ($(strip $(DEPS_EXISTED)),)
include $(DEPS_EXISTED)
endif

endif

# build command 

all: $(MODULES) main
	@echo Generated $(OUTPUT)/main

clean: 
	@rm -rf $(OUTPUT)/*

help:
	@echo 'Build:'
	@echo '    make [options] [command]'
	@echo '----------------------------------------------------------------------------------------'
	@echo 'SYNOPSIS:'
	@echo '    make [OUT=<path for output>] [command]'
	@echo '----------------------------------------------------------------------------------------'
	@echo 'command:'
	@echo '    all   - build all modules and generate finally output'
	@echo '    clean - clean all generated files'
	@echo '    help  - help message'
	@echo ''
	@echo 'Note that "all" will be used if [target] is absent.'
	@echo '----------------------------------------------------------------------------------------'
	@echo 'options:'
	@echo '    OUT   - path for output directory, will be "$(SRC_TREE)/output" if absent.'
	@echo ''

