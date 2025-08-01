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

#include "qemu/osdep.h"

#include "qapi/qmp/qerror.h"
#include "qapi/error.h"
#include "qemu/host-utils.h"
#include "qemu/timer.h"
#include "page_cache.h"
#include "trace.h"
#if defined(CONFIG_GNUTLS)
#include <gnutls/crypto.h>
#endif
#if defined(CONFIG_NETTLE)
#include <nettle/sha2.h>
#endif
#if defined(CONFIG_GCRYPT)
#include "gcrypt.h"
#endif

/* the page in cache will not be replaced in two cycles */
#define CACHED_PAGE_LIFETIME 2

typedef struct CacheItem CacheItem;

struct CacheItem {
    uint64_t it_addr;
    uint64_t it_age;
    uint8_t *it_data;
};

struct PageCache {
    CacheItem *page_cache;
    size_t item_size;
    size_t page_size;
    size_t max_num_items;
    size_t num_items;

#define CACHE_HASH_NSEC_PER_MISS 0
#define CACHE_HASH_NSEC_PER_HIT  1
    int64_t nsec_per_access[2];
    void (*hash_func)(PageCache *, const void *, size_t, uint8_t *);
};

PageCache *cache_init(size_t num_pages, size_t page_size, size_t item_size,
                      Error **errp)
{
    int64_t i;
    size_t new_size = num_pages * item_size;
    PageCache *cache;

    if (new_size < item_size) {
        error_setg(errp, QERR_INVALID_PARAMETER_VALUE, "cache size",
                   "is smaller than one target page size");
        return NULL;
    }

    /* round down to the nearest power of 2 */
    if (!is_power_of_2(num_pages)) {
        error_setg(errp, QERR_INVALID_PARAMETER_VALUE, "cache size",
                   "is not a power of two number of pages");
        return NULL;
    }

    /* We prefer not to abort if there is no memory */
    cache = g_try_malloc(sizeof(*cache));
    if (!cache) {
        error_setg(errp, "Failed to allocate cache");
        return NULL;
    }
    cache->item_size = item_size;
    cache->page_size = page_size;
    cache->num_items = 0;
    cache->max_num_items = num_pages;
    cache->hash_func = NULL;

    trace_migration_pagecache_init(cache->max_num_items);

    /* We prefer not to abort if there is no memory */
    cache->page_cache = g_try_malloc((cache->max_num_items) *
                                     sizeof(*cache->page_cache));
    if (!cache->page_cache) {
        error_setg(errp, "Failed to allocate page cache");
        g_free(cache);
        return NULL;
    }

    for (i = 0; i < cache->max_num_items; i++) {
        cache->page_cache[i].it_data = NULL;
        cache->page_cache[i].it_age = 0;
        cache->page_cache[i].it_addr = -1;
    }

    return cache;
}

void cache_fini(PageCache *cache)
{
    int64_t i;

    g_assert(cache);
    g_assert(cache->page_cache);

    for (i = 0; i < cache->max_num_items; i++) {
        g_free(cache->page_cache[i].it_data);
    }

    g_free(cache->page_cache);
    cache->page_cache = NULL;
    g_free(cache);
}

static size_t cache_get_cache_pos(const PageCache *cache,
                                  uint64_t address)
{
    g_assert(cache->max_num_items);
    return (address / cache->page_size) & (cache->max_num_items - 1);
}

static CacheItem *cache_get_by_addr(const PageCache *cache, uint64_t addr)
{
    size_t pos;

    g_assert(cache);
    g_assert(cache->page_cache);

    pos = cache_get_cache_pos(cache, addr);

    return &cache->page_cache[pos];
}

uint8_t *get_cached_data(const PageCache *cache, uint64_t addr)
{
    return cache_get_by_addr(cache, addr)->it_data;
}

bool cache_is_cached(const PageCache *cache, uint64_t addr,
                     uint64_t current_age)
{
    CacheItem *it;

    it = cache_get_by_addr(cache, addr);

    if (it->it_addr == addr) {
        /* update the it_age when the cache hit */
        it->it_age = current_age;
        return true;
    }
    return false;
}

int cache_insert(PageCache *cache, uint64_t addr, const uint8_t *pdata,
                 uint64_t current_age)
{

    CacheItem *it;

    /* actual update of entry */
    it = cache_get_by_addr(cache, addr);

    if (it->it_data && it->it_addr != addr &&
        it->it_age + CACHED_PAGE_LIFETIME > current_age) {
        /* the cache page is fresh, don't replace it */
        return -1;
    }
    /* allocate page */
    if (!it->it_data) {
        it->it_data = g_try_malloc(cache->item_size);
        if (!it->it_data) {
            trace_migration_pagecache_insert();
            return -1;
        }
        cache->num_items++;
    }

    memcpy(it->it_data, pdata, cache->item_size);

    it->it_age = current_age;
    it->it_addr = addr;

    return 0;
}

#if defined(CONFIG_GNUTLS)
static bool cache_hash_gnutls_sha256_supported(void)
{
    size_t i;
    const gnutls_digest_algorithm_t *algs;

    algs = gnutls_digest_list();
    for (i = 0; algs[i] != GNUTLS_DIG_UNKNOWN; i++) {
        if (algs[i] == GNUTLS_DIG_SHA256) {
            return true;
        }
    }

    return false;
}

static void cache_hash_gnutls_sha256_digest(PageCache *cache,
                                            const void *buf, size_t size,
                                            uint8_t *output_digest)
{
    gnutls_hash_hd_t hash;
    int ret;

    ret = gnutls_hash_init(&hash, GNUTLS_DIG_SHA256);
    assert(ret >= 0);
    gnutls_hash(hash, buf, size);
    gnutls_hash_deinit(hash, output_digest);
}
#endif
#if defined(CONFIG_GCRYPT)
static void cache_hash_gcrypt_sha256_digest(PageCache *cache,
                                            const void *buf, size_t size,
                                            uint8_t *output_digest)
{
    gcry_md_hash_buffer(GCRY_MD_SHA256, output_digest, buf, size);
}
#endif
#if defined(CONFIG_NETTLE)
static void cache_hash_nettle_sha256_digest(PageCache *cache,
                                            const void *buf, size_t size,
                                            uint8_t *output_digest)
{
    struct sha256_ctx ctx;

    sha256_init(&ctx);
    sha256_update(&ctx, size, buf);
    sha256_digest(&ctx, SHA256_DIGEST_SIZE, output_digest);
}
#endif

PageCache *cache_hash_init(size_t num_pages, size_t page_size,
                           enum cache_hash_algorithm algo, Error **errp)
{
    struct PageCache *cache = NULL;

#if defined(CONFIG_GNUTLS)
    if (algo == CACHE_HASH_GNUTLS_SHA256 &&
        cache_hash_gnutls_sha256_supported()) {
        cache = cache_init(num_pages, page_size,
                           gnutls_hash_get_len(GNUTLS_DIG_SHA256), errp);

        if (!cache) {
            return NULL;
        }

        cache->hash_func = cache_hash_gnutls_sha256_digest;
    }
#endif
#if defined(CONFIG_GCRYPT)
    if (algo == CACHE_HASH_GCRYPT_SHA256) {
        cache = cache_init(num_pages, page_size,
                           gcry_md_get_algo_dlen(GCRY_MD_SHA256) , errp);
        if (!cache) {
            return NULL;
        }

        cache->hash_func = cache_hash_gcrypt_sha256_digest;
    }
#endif
#if defined(CONFIG_NETTLE)
    if (algo == CACHE_HASH_NETTLE_SHA256) {
        cache = cache_init(num_pages, page_size, SHA256_DIGEST_SIZE, errp);
        if (!cache) {
            return NULL;
        }

        cache->hash_func = cache_hash_nettle_sha256_digest;
    }
#endif

    if (!cache) {
        error_setg(errp, QERR_INVALID_PARAMETER_VALUE, "algo",
                   "a known hash algorithm");
    }
    return cache;
}

static int cache_hash_insert(PageCache *cache, uint64_t addr,
                             uint64_t current_age)
{
    CacheItem *it;

    /* actual update of entry */
    it = cache_get_by_addr(cache, addr);

    /* allocate page */
    if (!it->it_data) {
        it->it_data = g_try_malloc0(cache->item_size);
        if (!it->it_data) {
            trace_migration_pagecache_insert();
            return -1;
        }
        cache->num_items++;
    } else {
        memset(it->it_data, 0, cache->item_size);
    }

    it->it_age = current_age;
    it->it_addr = addr;

    return 0;
}

bool cache_hash_is_cached(PageCache *cache, uint64_t addr, const void *buf,
                          void *digest, void **out_page)
{
    CacheItem *it = cache_get_by_addr(cache, addr);
    bool match = false;
    uint64_t age = 0;
    int64_t time;

    time = qemu_clock_get_ns(QEMU_CLOCK_REALTIME);
    memset(digest, 0, cache->item_size);
    cache->hash_func(cache, buf, cache->page_size, digest);

    if (it->it_data && it->it_addr == addr) {
        match = !memcmp(it->it_data, digest, cache->item_size);
    }

    if (!match) {
        cache_hash_insert(cache, addr, age);
        memcpy(*out_page, buf, cache->page_size);
        cache->hash_func(cache, *out_page, cache->page_size, it->it_data);
    }

    time = qemu_clock_get_ns(QEMU_CLOCK_REALTIME) - time;
    cache->nsec_per_access[match] = time;

    return match;
}

void cache_hash_invalidate(PageCache *cache, uint64_t addr)
{
    CacheItem *it = cache_get_by_addr(cache, addr);

    if (it->it_data) {
        it->it_addr = -1;
        memset(it->it_data, 0, cache->item_size);
    }
}

size_t cache_hash_item_size(PageCache *cache)
{
    return cache->item_size;
}

int64_t cache_hash_nsec_per_miss(PageCache *cache)
{
    return cache->nsec_per_access[CACHE_HASH_NSEC_PER_MISS];
}

int64_t cache_hash_nsec_per_hit(PageCache *cache)
{
    return cache->nsec_per_access[CACHE_HASH_NSEC_PER_HIT];
}
