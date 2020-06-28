#include <config.h>
#include <stdio.h>

void main()
{
    printf("\n%s!\n", CONFIG_MAIN_INFO);

#ifdef CONFIG_MODULE11
    mod11_rtn();
#endif /* CONFIG_MODULE11 */

#ifdef CONFIG_MODULE12
    mod12_rtn();
#endif /* CONFIG_MODULE12 */

#ifdef CONFIG_MODULE2
    mod2_rtn();
#endif /* CONFIG_MODULE2 */
}
