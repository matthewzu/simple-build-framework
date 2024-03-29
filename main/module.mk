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

# Main Module makefile

APPS_y	+= main main2

SRCS_main_y		= $(wildcard $(SRC_TREE)/main/main.c)
CFLAGS_main 	= -DMAIN

SRCS_main2_y	= $(wildcard $(SRC_TREE)/main/main2.c)
CFLAGS_main2 	= -DMAIN2
