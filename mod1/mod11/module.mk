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

# Module makefile

MODULES_$(CONFIG_MODULE11) += mod11

SRC_TREE_MOD11					= $(SRC_TREE)/mod1/mod11
SRCS_mod11_$(CONFIG_MODULE11)	= $(SRC_TREE_MOD11)/source/mod11.c
HDRDIR_mod11_$(CONFIG_MODULE11)	= $(SRC_TREE_MOD11)/include
HDRS_mod11_$(CONFIG_MODULE11)	= $(SRC_TREE_MOD11)/include/mod11/mod11.h

CFLAGS_mod1 					= -DCFALSG_MOD1
CFLAGS_mod1_mod11 				= -DCFLAGS_MOD1_MOD11
