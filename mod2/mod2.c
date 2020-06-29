#include <config.h>
#include <stdio.h>
#include <mod2.h>

#ifdef CONFIG_MODULE2_DEBUG
#include <mod2_dbg.h>
#endif

void mod2_rtn()
{
    printf("%s!\n", CONFIG_MODULE2_INFO);
#ifdef CONFIG_MODULE2_DEBUG
    MOD2_DBG("\t - Module 2 Debug!\n");
#endif
}

