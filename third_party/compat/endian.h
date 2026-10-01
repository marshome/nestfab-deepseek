/* Minimal <endian.h> for MinGW, where that POSIX header does not exist.
 *
 * Clp's CoinAbcCommon.hpp does:
 *     #ifndef __BYTE_ORDER
 *     #include <endian.h>
 *     #endif
 *     #if __BYTE_ORDER == __LITTLE_ENDIAN
 *     #define ABC_INTEL
 * and later uses __BYTE_ORDER to pick the little endian double tests. The target is x86-64, i.e.
 * little endian, so this shim is exact rather than approximate.
 */
#ifndef LCNS_COMPAT_ENDIAN_H
#define LCNS_COMPAT_ENDIAN_H

#define __LITTLE_ENDIAN 1234
#define __BIG_ENDIAN    4321
#define __PDP_ENDIAN    3412
#define __BYTE_ORDER    __LITTLE_ENDIAN

#define LITTLE_ENDIAN   __LITTLE_ENDIAN
#define BIG_ENDIAN      __BIG_ENDIAN
#define PDP_ENDIAN      __PDP_ENDIAN
#define BYTE_ORDER      __BYTE_ORDER

/* the byte swap helpers glibc's endian.h provides are not needed by Clp, but keep the names
   unavailable rather than silently wrong */

#endif /* LCNS_COMPAT_ENDIAN_H */
