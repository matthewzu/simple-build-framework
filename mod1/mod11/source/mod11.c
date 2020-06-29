#include <config.h>
#include <stdio.h>
#include <mod11/mod11.h>

#ifndef MOD11
#   error '-DMOD11' is not yet in force, check 'module.mk' please
#endif

#ifndef MOD11_MOD11
#   error '-DMOD11_MOD11' is not yet in force, check 'module.mk' please
#endif

void mod11_rtn(void)
{
    printf("%s!\n", CONFIG_MODULE11_INFO);
}
