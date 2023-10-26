#include <config.h>
#include <stdio.h>

#ifdef CONFIG_MODULE2
#   include <mod2.h>
#endif /* CONFIG_MODULE2 */

#ifndef MAIN2
#   error '-DMAIN2' is not yet in force, check 'module.mk' please
#endif

void main()
{
    printf("\n%s!\n", CONFIG_MAIN_INFO);

#ifdef CONFIG_MODULE2
    mod2_rtn();
#endif /* CONFIG_MODULE2 */
}
