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
#include "qemu/error-report.h"
#include "qemu/host-utils.h"
#include "qemu/timer.h"
#include "page_cache.h"
#include "trace.h"
#include "migration.h"
#if defined(CONFIG_GNUTLS)
#include <gnutls/crypto.h>
#endif
#if defined(CONFIG_NETTLE)
#include <nettle/sha2.h>
#endif
#if defined(CONFIG_GCRYPT)
#include "gcrypt.h"
#endif
#if defined(CONFIG_ISAL)
#include <isa-l_crypto/mh_sha256.h>
#include <isa-l_crypto/sha256_mb.h>
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
#if defined(CONFIG_ISAL)
    void *dlopen_handle;
    typeof(&isal_sha256_ctx_mgr_init) isal_sha256_ctx_mgr_init;
    typeof(&isal_sha256_ctx_mgr_submit) isal_sha256_ctx_mgr_submit;
    typeof(&isal_sha256_ctx_mgr_flush) isal_sha256_ctx_mgr_flush;
#endif

#define CACHE_HASH_NSEC_PER_MISS 0
#define CACHE_HASH_NSEC_PER_HIT  1
    int64_t nsec_per_access[2];
    void (*hash_func)(PageCache *, const void *, size_t, uint8_t *);
    int (*hash_pool_init)(PageCache *, size_t, void **);
    void (*hash_pool_fini)(PageCache *, size_t, void **);
    int (*hash_pool_submit)(PageCache *, void *, const void *, uint64_t,
                            uint64_t *, size_t, bool *, void **);

#define PAGE_CACHE_SUBMIT_BATCH  (1UL << 0)
    uint64_t flags;
};

const char *cache_hash_algo_to_str(CacheHashAlgorithm algo)
{
    for (int i = CACHE_HASH_NONE; i < ARRAY_SIZE(cache_hash_algos); i++) {
        if (cache_hash_algos[i].algo == algo) {
            return cache_hash_algos[i].name;
        }
    }
    return "unknown";
}

/*
 * Iterates once over all algorithms in CacheHashAlgoDesc.
 * Returns next supported algorithm or
 * returns CACHE_HASH_NONE if none available.
 * If current == CACHE_HASH_NONE, we return first supported
 * algorithm or CACHE_HASH_NONE.
 */
CacheHashAlgorithm next_supported_algo(CacheHashAlgorithm current)
{
    int i, n;

    for (n = 1; n < ARRAY_SIZE(cache_hash_algos); n++) {
        i = (current + n) % ARRAY_SIZE(cache_hash_algos);
        const CacheHashAlgoDesc *d = &cache_hash_algos[i];

        if (d->algo == CACHE_HASH_NONE || !d->check_supported) {
            continue;
        }

        if (d->check_supported()) {
            return d->algo;
        }
    }

    return CACHE_HASH_NONE;
}

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

#if defined(CONFIG_ISAL)
    g_clear_pointer(&cache->dlopen_handle, dlclose);
#endif
    g_clear_pointer(&cache->page_cache, g_free);
    g_clear_pointer(&cache, g_free);
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
bool cache_hash_gnutls_sha256_supported(void)
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

void cache_hash_gnutls_sha256_digest(PageCache *cache,
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
void cache_hash_gcrypt_sha256_digest(PageCache *cache,
                                     const void *buf, size_t size,
                                     uint8_t *output_digest)
{
    gcry_md_hash_buffer(GCRY_MD_SHA256, output_digest, buf, size);
}
#endif
#if defined(CONFIG_NETTLE)
void cache_hash_nettle_sha256_digest(PageCache *cache,
                                     const void *buf, size_t size,
                                     uint8_t *output_digest)
{
    struct sha256_ctx ctx;

    sha256_init(&ctx);
    sha256_update(&ctx, size, buf);
    sha256_digest(&ctx, SHA256_DIGEST_SIZE, output_digest);
}
#endif

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

PageCache *cache_hash_init(size_t num_pages, size_t page_size,
                           CacheHashAlgorithm algo, Error **errp)
{
    ERRP_GUARD();
    struct PageCache *cache = NULL;
    int i;
    Error *local_err = NULL;

    assert(ARRAY_SIZE(cache_hash_algos) == CACHE_HASH_MAX);

    if (algo == CACHE_HASH_NONE) {
        error_setg(errp, "Unsupported algorithm %s",
                   cache_hash_algo_to_str(algo));

        return NULL;
    }

    for (i = 0; i < ARRAY_SIZE(cache_hash_algos); i++) {
        const CacheHashAlgoDesc *desc = &cache_hash_algos[i];

        if (desc->algo != algo) {
            continue;
        }

        if (!desc->check_supported) {
            error_setg(errp, "Cannot determine if hash %s is supported, assume it is not",
                       cache_hash_algo_to_str(algo));
            return NULL;
        }

        if (desc->check_supported && !desc->check_supported()) {
            error_setg(errp, "Hash algorithm %s is not supported",
                       cache_hash_algo_to_str(algo));
            return NULL;
        }

        size_t digest_size = desc->digest_size() ? desc->digest_size() : 0;

        cache = desc->cache_algo_init ? desc->cache_algo_init(num_pages, page_size,
                                                              digest_size,
                                                              &local_err) : NULL;
        if (!cache) {
            if (local_err) {
                error_propagate(errp, local_err);
            }
            return NULL;
        }

        cache->hash_func = desc->digest;
        break;
    }
    return cache;
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

bool is_exadata_machine(void)
{
    if (strstr(machine_get_name(), "-exadata") == NULL) {
        return false;
    }
    return true;
}

#if defined(CONFIG_ISAL)
bool isal_sha256_mb_supported(void)
{

    char *algo_str = migrate_hash_algo();

    /*
     * Do not allow to use isa-l crypto if is not explicitly set for
     * non-exadata machines in migration options.
     * Exadata machines can select it by default.
     */
    if (!algo_str) {
        if (!is_exadata_machine()) {
            return false;
        }
        return isal_sha256_symbols_available();
    }

    if (strcmp(algo_str, "isal-crypto-mb-sha256") == 0) {
        return isal_sha256_symbols_available();
    }

    return false;
}

static void *dlsym_impl(void *handle, const char *sym_name, Error **errp)
{
    void *sym = NULL;

    dlerror();
    if (!sym_name) {
        error_setg(errp, "dlsym failed, empty symbol string");
        return NULL;
    }

    sym = dlsym(handle, sym_name);
    if (!sym) {
        error_setg(errp, "dlsym failed with symbol %s: %s", sym_name, dlerror());
        return NULL;
    }

    return sym;
}

bool isal_sha256_symbols_available(void)
{
    void *mgr_init = NULL, *mgr_submit = NULL, *mgr_flush = NULL;
    void *handle;
    Error *local_err = NULL;
    bool ret = false;

    dlerror();
    handle = dlopen(ISAL_LIB_FILE_NAME, RTLD_LAZY);

    if (handle == NULL) {
        error_report("Could not dlopen library %s", ISAL_LIB_FILE_NAME);
        return false;
    }
    mgr_init = dlsym_impl(handle, "isal_sha256_ctx_mgr_init", &local_err);
    if (!mgr_init) {
        goto out_sym;
    }
    mgr_submit = dlsym_impl(handle, "isal_sha256_ctx_mgr_submit", &local_err);
    if (!mgr_submit) {
        goto out_sym;
    }
    mgr_flush = dlsym_impl(handle, "isal_sha256_ctx_mgr_flush", &local_err);
    if (!mgr_flush) {
        goto out_sym;
    }

    ret = true;

 out_sym:
    if (local_err) {
        error_report_err(local_err);
    }
    g_clear_pointer(&handle, dlclose);

    return ret;
}

struct multi_buffer_ctx {
    ISAL_SHA256_HASH_CTX_MGR *mgr;
    ISAL_SHA256_HASH_CTX *ctx;
};

static int cache_hash_isal_crypto_mb_pool_init(PageCache *cache, size_t nr_pages, void **opaque)
{
    ISAL_SHA256_HASH_CTX_MGR *mgr = NULL;
    struct multi_buffer_ctx *out;
    int ret = 0;

    out = g_try_malloc0(sizeof(*out));
    if (!out) {
        ret = -ENOMEM;
        goto out_err;
    }
    out->mgr = g_try_malloc0(sizeof(*mgr));
    if (!out->mgr) {
        ret = -ENOMEM;
        goto out_err;
    }
    out->ctx = g_try_new0(ISAL_SHA256_HASH_CTX, nr_pages);
    if (!out->ctx) {
        ret = -ENOMEM;
        goto out_err;
    }
    for (int i = 0; i < nr_pages; i++) {
         isal_hash_ctx_init(&out->ctx[i]);
         out->ctx[i].user_data = (void *) ((uint64_t) i);
    }
    ret = cache->isal_sha256_ctx_mgr_init(out->mgr);
    if (ret) {
        goto out_err;
    }
    *opaque = out;
    return 0;

 out_err:
    g_clear_pointer(&out->ctx, g_free);
    g_clear_pointer(&out->mgr, g_free);
    g_clear_pointer(&out, g_free);

    *opaque = NULL;

    return ret;
}

static void cache_hash_isal_crypto_mb_pool_fini(PageCache *cache, size_t nr_pages, void **opaque)
{
    struct multi_buffer_ctx *out = *opaque;

    g_clear_pointer(&out->ctx, g_free);
    g_clear_pointer(&out->mgr, g_free);
    g_clear_pointer(&out, g_free);

    *opaque = NULL;
}

static int cache_hash_isal_crypto_mb_pool_submit(PageCache *cache, void *opaque,
                                                 const void *buf, uint64_t base_addr,
                                                 uint64_t *offset, size_t nr_pages,
                                                 bool *out_matched, void **out_pages)
{
    struct multi_buffer_ctx *mb = opaque;
    ISAL_SHA256_HASH_CTX_MGR *mgr = mb->mgr;
    ISAL_SHA256_HASH_CTX *ctx, *out;
    int64_t time, ts, hash_ts;
    int i, misses = 0;
    int ret;

    if (nr_pages == 0) {
        return 0;
    }
    time = qemu_clock_get_ns(QEMU_CLOCK_REALTIME);
    for (i = 0; i < nr_pages; i++) {
        const void *page = buf + offset[i];

        ctx = &mb->ctx[i];
        isal_hash_ctx_init(ctx);
        ctx->user_data = (void *) ((uint64_t) i);
        ret = cache->isal_sha256_ctx_mgr_submit(mgr, ctx, &out, page,
                                   cache->page_size, ISAL_HASH_ENTIRE);
        if (ret) {
            return -EINVAL;
        }
    }

    out = NULL;
    do {
        ret = cache->isal_sha256_ctx_mgr_flush(mgr, &out);
        if (ret) {
            return -EINVAL;
        }
    } while (out != NULL);

    ts = qemu_clock_get_ns(QEMU_CLOCK_REALTIME);
    time = (ts - time) / nr_pages;
    cache->nsec_per_access[CACHE_HASH_NSEC_PER_MISS] = time;
    cache->nsec_per_access[CACHE_HASH_NSEC_PER_HIT] = time;

    for (i = 0; i < nr_pages; i++) {
        uint64_t addr = base_addr + offset[i];
        const void *host = buf + offset[i];
        void *out_page = out_pages[i];
        bool match = false;
        CacheItem *it;

        ctx = &mb->ctx[i];
        it = cache_get_by_addr(cache, addr);

        /* Match against the batch-calculated hash */
        if (it->it_data && it->it_addr == addr) {
            match = !memcmp(it->it_data, ctx->job.result_digest, cache->item_size);
        }

        /* On a miss hash a copy of the page */
        if (!match) {
            hash_ts = qemu_clock_get_ns(QEMU_CLOCK_REALTIME);
            cache_hash_insert(cache, addr, 0);
            memcpy(out_page, host, cache->page_size);

            /*
             * We don't use the simple multi-hash API as it produces results
             * with different format. Submit a single job and flush it right
             * away. If we care about latency of misses we should copy the page
             * even on hits and skip this step. But it adds up about 400-600
             * cycles on the hit path.
             */
            isal_hash_ctx_init(ctx);
            ret = cache->isal_sha256_ctx_mgr_submit(mgr, ctx, &out, out_page,
                                       cache->page_size, ISAL_HASH_ENTIRE);
            if (ret) {
                return -EINVAL;
            }
            cache->nsec_per_access[CACHE_HASH_NSEC_PER_MISS] = time +
                         (qemu_clock_get_ns(QEMU_CLOCK_REALTIME) - hash_ts);
            ++misses;
        }
        out_matched[i] = match;
        ctx->user_data = (void *) ((bool) match);
    }

    /* We've had only hash matches */
    if (!misses) {
        return 0;
    }

    /* Update timestamp for the misses and wait for completion */
    ts = qemu_clock_get_ns(QEMU_CLOCK_REALTIME);

    out = NULL;
    do {
        ret = cache->isal_sha256_ctx_mgr_flush(mgr, &out);
        if (ret) {
            return -EINVAL;
        }
    } while (out != NULL);

    cache->nsec_per_access[CACHE_HASH_NSEC_PER_MISS] +=
         (qemu_clock_get_ns(QEMU_CLOCK_REALTIME) - ts) / misses;

    for (i = 0; i < nr_pages; i++) {
        uint64_t addr = base_addr + offset[i];
        CacheItem *it;

        ctx = &mb->ctx[i];
        if (ctx->user_data) {
            continue;
        }

        it = cache_get_by_addr(cache, addr);
        memcpy(it->it_data, ctx->job.result_digest, cache->item_size);
    }

    return 0;
}

PageCache *cache_init_isal(size_t num_pages, size_t page_size,
                           size_t item_size, Error **errp)
{
    ERRP_GUARD();
    PageCache *cache = NULL;
    void *mgr_init = NULL, *mgr_submit = NULL, *mgr_flush = NULL;
    void *handle;

    handle = dlopen(ISAL_LIB_FILE_NAME, RTLD_LAZY);
    if (handle == NULL) {
        error_setg(errp, "Could not load library with dlopen %s: , err %s",
                   ISAL_LIB_FILE_NAME, dlerror());
        return NULL;
    }

    mgr_init = dlsym_impl(handle, "isal_sha256_ctx_mgr_init", errp);
    if (!mgr_init) {
        g_clear_pointer(&handle, dlclose);
        return NULL;
    }
    mgr_submit = dlsym_impl(handle, "isal_sha256_ctx_mgr_submit", errp);
    if (!mgr_submit) {
        g_clear_pointer(&handle, dlclose);
        return NULL;
    }
    mgr_flush = dlsym_impl(handle, "isal_sha256_ctx_mgr_flush", errp);
    if (!mgr_flush) {
        g_clear_pointer(&handle, dlclose);
        return NULL;
    }

    cache = cache_init(num_pages, page_size, item_size, errp);
    if (!cache) {
        g_clear_pointer(&handle, dlclose);
        return NULL;
    }

    cache->dlopen_handle = handle;

    cache->isal_sha256_ctx_mgr_init = mgr_init;
    cache->isal_sha256_ctx_mgr_submit = mgr_submit;
    cache->isal_sha256_ctx_mgr_flush = mgr_flush;

    cache->flags |= PAGE_CACHE_SUBMIT_BATCH;
    cache->hash_pool_init = cache_hash_isal_crypto_mb_pool_init;
    cache->hash_pool_fini = cache_hash_isal_crypto_mb_pool_fini;
    cache->hash_pool_submit = cache_hash_isal_crypto_mb_pool_submit;

    return cache;
}
#endif /* CONFIG_ISAL */

/* TODO: check the error at caller site. */
int cache_hash_pool_init(PageCache *cache, size_t nr_pages, void **opaque)
{
    if (!cache_hash_is_batch(cache)) {
        return -EINVAL;
    }

    return cache->hash_pool_init(cache, nr_pages, opaque);
}

void cache_hash_pool_fini(PageCache *cache, size_t nr_pages, void **opaque)
{
    if (!cache_hash_is_batch(cache)) {
        return;
    }

    cache->hash_pool_fini(cache, nr_pages, opaque);
}

/* TODO: check the error at caller site. */
int cache_hash_pool_submit(PageCache *cache, void *opaque, const void *buf,
                           uint64_t base_addr, uint64_t *offset, size_t nr_pages,
                           bool *out_matched, void **out_pages)
{
    if (!cache_hash_is_batch(cache)) {
        return -EINVAL;
    }

    return cache->hash_pool_submit(cache, opaque, buf, base_addr, offset,
                                   nr_pages, out_matched, out_pages);
}

bool cache_hash_is_batch(PageCache *cache)
{
    return cache->flags & PAGE_CACHE_SUBMIT_BATCH;
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
