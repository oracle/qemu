/*
 * Multifd zero page detection implementation.
 *
 * Copyright (c) 2024 Bytedance Inc
 *
 * Authors:
 *  Hao Xiang <hao.xiang@bytedance.com>
 *
 * This work is licensed under the terms of the GNU GPL, version 2 or later.
 * See the COPYING file in the top-level directory.
 */

#include "qemu/osdep.h"
#include "qemu/cutils.h"
#include "exec/ramblock.h"
#include "migration.h"
#include "migration-stats.h"
#include "multifd.h"
#include "ram.h"

static bool multifd_zero_page_enabled(void)
{
    return migrate_zero_page_detection() == ZERO_PAGE_DETECTION_MULTIFD;
}

static void swap_page_offset(ram_addr_t *pages_offset, int a, int b)
{
    ram_addr_t temp;

    if (a == b) {
        return;
    }

    temp = pages_offset[a];
    pages_offset[a] = pages_offset[b];
    pages_offset[b] = temp;
}

static void swap_batch_metadata(MultiFDPages_t *pages, int a, int b)
{
    bool tmpmatch;
    void *tmppage;

    if (a == b) {
        return;
    }

    tmppage = pages->cached[a];
    pages->cached[a] = pages->cached[b];
    pages->cached[b] = tmppage;
    tmpmatch = pages->matched[a];
    pages->matched[a] = pages->matched[b];
    pages->matched[b] = tmpmatch;
}

static void multifd_skip_cached_pages(MultiFDSendParams *p, int normal_num)
{
    MultiFDPages_t *pages = &p->data->u.ram;
    RAMBlock *rb = pages->block;
    int i = 0;
    int j = normal_num - 1;
    bool batch = cache_hash_is_batch(hash_cache);

    if (batch) {
        cache_hash_pool_submit(hash_cache, pages->batch_context, rb->host,
                               rb->offset, pages->offset, normal_num,
                               pages->matched, pages->cached);
    }

    /*
     * Sort the page offset array by moving all normal pages to
     * the left and all skipped pages to the right of the array.
     */
    while (i <= j) {
        uint64_t offset = pages->offset[i];
        bool match;

        if (!batch) {
            match = cache_hash_is_cached(hash_cache,
                                         rb->offset + offset,
                                         rb->host + offset, pages->digest,
                                         &pages->cached[i]);
        } else {
            match = pages->matched[i];
        }

        if (!match) {
            i++;
            continue;
        }

        if (batch) {
            swap_batch_metadata(pages, i, j);
        }
        swap_page_offset(pages->offset, i, j);
        ram_release_page(rb->idstr, offset);
        j--;
    }

    stat64_add(&ram_counters.cache_digests, normal_num);
    stat64_add(&ram_counters.cache_misses, i);
    stat64_add(&ram_counters.cache_hits, normal_num - i);

    pages->normal_num = i;
    pages->skipped_num = normal_num - pages->normal_num;
}

/**
 * multifd_send_zero_page_detect: Perform zero page detection on all pages.
 *
 * Sorts normal pages before zero pages in p->pages->offset and updates
 * p->pages->normal_num.
 *
 * @param p A pointer to the send params.
 */
void multifd_send_zero_page_detect(MultiFDSendParams *p)
{
    MultiFDPages_t *pages = &p->data->u.ram;
    RAMBlock *rb = pages->block;
    int i = 0;
    int j = pages->num - 1;
    pages->skipped_num = 0;
    pages->normal_num = 0;

    if (!multifd_zero_page_enabled()) {
        pages->normal_num = pages->num;
        goto out;
    }

    /*
     * Sort the page offset array by moving all normal pages to
     * the left and all zero pages to the right of the array.
     */
    while (i <= j) {
        uint64_t offset = pages->offset[i];

        if (!buffer_is_zero(rb->host + offset, multifd_ram_page_size())) {
            i++;
            continue;
        }

        swap_page_offset(pages->offset, i, j);
        ram_release_page(rb->idstr, offset);
        j--;
    }

    pages->normal_num = i;

    if (migrate_use_hash() && pages->normal_num) {
        multifd_skip_cached_pages(p, pages->normal_num);
    }

out:
    stat64_add(&ram_counters.normal_pages, pages->normal_num);
    stat64_add(&ram_counters.zero_pages, pages->num - pages->normal_num - pages->skipped_num);
}

void multifd_recv_zero_page_process(MultiFDRecvParams *p)
{
    for (int i = 0; i < p->zero_num; i++) {
        void *page = p->host + p->zero[i];
        if (ramblock_recv_bitmap_test_byte_offset(p->block, p->zero[i])) {
            memset(page, 0, multifd_ram_page_size());
        } else {
            ramblock_recv_bitmap_set_offset(p->block, p->zero[i]);
        }
    }
}
