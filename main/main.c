#include <config.h>
#include <stdio.h>

#ifdef CONFIG_MODULE11
#   include <mod11/mod11.h>
#endif /* CONFIG_MODULE11 */

#ifdef CONFIG_MODULE12
#   include <mod12.h>
#endif /* CONFIG_MODULE12 */

#ifndef MAIN
#   error '-DMAIN' is not yet in force, check 'module.mk' please
#endif

void main()
{
    printf("\n%s!\n", CONFIG_MAIN_INFO);

#ifdef CONFIG_MODULE11
    mod11_rtn();
#endif /* CONFIG_MODULE11 */

#ifdef CONFIG_MODULE12
    mod12_rtn();
#endif /* CONFIG_MODULE12 */
}
