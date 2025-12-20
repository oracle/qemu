/*
 * Page cache for QEMU
 * The cache is base on a hash of the page address
 *
 * Copyright 2012 Red Hat, Inc. and/or its affiliates
 *
 * Authors:
 *  Orit Wasserman  <owasserm@redhat.com>
 *
 * This work is licensed under the terms of the GNU GPL, version 2 or later.
 * See the COPYING file in the top-level directory.
 *
 */

#ifndef PAGE_CACHE_H
#define PAGE_CACHE_H

#if defined(CONFIG_GNUTLS)
#include <gnutls/crypto.h>
#endif
#if defined(CONFIG_NETTLE)
#include <nettle/sha2.h>
#include <nettle/sha.h>
#endif
#if defined(CONFIG_GCRYPT)
#include "gcrypt.h"
#endif
#include "hw/core/machine.h"
#include <dlfcn.h>
#if defined(CONFIG_ISAL)
#include <isa-l_crypto/mh_sha256.h>
#include <isa-l_crypto/sha256_mb.h>
#endif

/* Page cache for storing guest pages */
typedef struct PageCache PageCache;

/**
 * cache_init: Initialize the page cache
 *
 *
 * Returns new allocated cache or NULL on error
 *
 * @cache_size: cache size in number of pages
 * @page_size: cache page size
 * @errp: set *errp if the check failed, with reason
 */
PageCache *cache_init(uint64_t cache_size, size_t page_size, size_t item_size, Error **errp);
/**
 * cache_fini: free all cache resources
 * @cache pointer to the PageCache struct
 */
void cache_fini(PageCache *cache);

/**
 * cache_is_cached: Checks to see if the page is cached
 *
 * Returns %true if page is cached
 *
 * @cache pointer to the PageCache struct
 * @addr: page addr
 * @current_age: current bitmap generation
 */
bool cache_is_cached(const PageCache *cache, uint64_t addr,
                     uint64_t current_age);

/**
 * get_cached_data: Get the data cached for an addr
 *
 * Returns pointer to the data cached or NULL if not cached
 *
 * @cache pointer to the PageCache struct
 * @addr: page addr
 */
uint8_t *get_cached_data(const PageCache *cache, uint64_t addr);

/**
 * cache_insert: insert the page into the cache. the page cache
 * will dup the data on insert. the previous value will be overwritten
 *
 * Returns -1 when the page isn't inserted into cache
 *
 * @cache pointer to the PageCache struct
 * @addr: page address
 * @pdata: pointer to the page
 * @current_age: current bitmap generation
 */
int cache_insert(PageCache *cache, uint64_t addr, const uint8_t *pdata,
                 uint64_t current_age);

typedef enum cache_hash_algorithm {
    CACHE_HASH_NONE = 0,
#if defined(CONFIG_GNUTLS)
    CACHE_HASH_GNUTLS_SHA256,
#endif
#if defined(CONFIG_GCRYPT)
    CACHE_HASH_GCRYPT_SHA256,
#endif
#if defined(CONFIG_NETTLE)
    CACHE_HASH_NETTLE_SHA256,
#endif
#if defined(CONFIG_ISAL)
    CACHE_HASH_ISAL_CRYPTO_MB,
#endif
    CACHE_HASH_MAX,
} CacheHashAlgorithm;

/*
 * Algorithm description structure.
 */
typedef struct {
    CacheHashAlgorithm algo;
    const char *name;
    bool (*check_supported)(void);
    size_t (*digest_size)(void);
    void (*digest)(PageCache *cache,
                    const void *buf, size_t size,
                    uint8_t *output_digest);
    PageCache *(*cache_algo_init)(size_t num_pages, size_t page_size,
                                  size_t item_size, Error **errp);
} CacheHashAlgoDesc;

const char *cache_hash_algo_to_str(enum cache_hash_algorithm algo);
CacheHashAlgorithm next_supported_algo(CacheHashAlgorithm current);

static inline bool hash_supported(void) {return true;}
static inline bool hash_not_supported(void) {return false;}

#if defined(CONFIG_ISAL)
PageCache *cache_init_isal(size_t num_pages, size_t page_size,
                           size_t item_size, Error **errp);

bool isal_sha256_mb_supported(void);

static size_t isal_sha256_mb_digest_size(void)
{
    return ISAL_SHA256_DIGEST_WORDS*sizeof(uint32_t);
}
#endif
bool is_exadata_machine(void);

#if defined(CONFIG_GNUTLS)
void cache_hash_gnutls_sha256_digest(PageCache *cache,
                                     const void *buf, size_t size,
                                     uint8_t *output_digest);
static size_t cache_hash_gnutls_sha256_digest_size(void)
{
    return gnutls_hash_get_len(GNUTLS_DIG_SHA256);
}
bool cache_hash_gnutls_sha256_supported(void);
#endif

#if defined(CONFIG_GCRYPT)
void cache_hash_gcrypt_sha256_digest(PageCache *cache,
                                     const void *buf, size_t size,
                                     uint8_t *output_digest);
static size_t cache_hash_gcrypt_sha256_digest_size(void)
{
    return gcry_md_get_algo_dlen(GCRY_MD_SHA256);
}
#endif

#if defined(CONFIG_NETTLE)
void cache_hash_nettle_sha256_digest(PageCache *cache,
                                     const void *buf, size_t size,
                                     uint8_t *output_digest);
static size_t cache_hash_nettle_sha256_digest_size(void)
{
    return SHA256_DIGEST_SIZE;
}
#endif

static const CacheHashAlgoDesc cache_hash_algos[] = {
    { CACHE_HASH_NONE, "none", hash_not_supported, NULL, NULL, NULL },
#if defined(CONFIG_GNUTLS)
    { CACHE_HASH_GNUTLS_SHA256, "gnutls-sha256",
      cache_hash_gnutls_sha256_supported,
      cache_hash_gnutls_sha256_digest_size,
      cache_hash_gnutls_sha256_digest, cache_init },
#endif
#if defined(CONFIG_GCRYPT)
    { CACHE_HASH_GCRYPT_SHA256, "gcrypt-sha256",
      hash_supported,
      cache_hash_gcrypt_sha256_digest_size,
      cache_hash_gcrypt_sha256_digest, cache_init },
#endif
#if defined(CONFIG_NETTLE)
    { CACHE_HASH_NETTLE_SHA256, "nettle-sha256",
      hash_supported,
      cache_hash_nettle_sha256_digest_size,
      cache_hash_nettle_sha256_digest, cache_init },
#endif
#if defined(CONFIG_ISAL)
    { CACHE_HASH_ISAL_CRYPTO_MB, "isal-crypto-mb-sha256",
      isal_sha256_mb_supported,
      isal_sha256_mb_digest_size, NULL, cache_init_isal },
#endif
};

bool isal_sha256_symbols_available(void);

PageCache *cache_hash_init(size_t num_pages, size_t page_size,
                           CacheHashAlgorithm algo, Error **errp);
bool cache_hash_is_cached(PageCache *cache, uint64_t addr, const void *buf,
                          void *digest, void **out_page);
void cache_hash_invalidate(PageCache *cache, uint64_t addr);
size_t cache_hash_item_size(PageCache *cache);
int64_t cache_hash_nsec_per_miss(PageCache *cache);
int64_t cache_hash_nsec_per_hit(PageCache *cache);
int cache_hash_pool_init(PageCache *cache, size_t nr_pages, void **opaque);
void cache_hash_pool_fini(PageCache *cache, size_t nr_pages, void **opaque);
int cache_hash_pool_submit(PageCache *cache, void *opaque, const void *buf,
                           uint64_t base_addr, uint64_t *offset, size_t nr_pages,
                           bool *out_matched, void **out_pages);
bool cache_hash_is_batch(PageCache *cache);
extern PageCache *hash_cache;

#endif
