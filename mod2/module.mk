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

# Module makefile

MODULES_$(CONFIG_MODULE2) += mod2

SRCS_mod2_$(CONFIG_MODULE2)			= $(wildcard $(SRC_TREE)/mod2/*.c)
HDRDIR_mod2_$(CONFIG_MODULE2)		= $(SRC_TREE)/mod2/h

CFLAGS_mod2 						= -DMOD2
