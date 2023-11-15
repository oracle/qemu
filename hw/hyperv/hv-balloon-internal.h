/*
 * QEMU Hyper-V Dynamic Memory Protocol driver
 *
 * Copyright (C) 2020-2023 Oracle and/or its affiliates.
 *
 * This work is licensed under the terms of the GNU GPL, version 2 or later.
 * See the COPYING file in the top-level directory.
 */

#ifndef HW_HYPERV_HV_BALLOON_INTERNAL_H
#define HW_HYPERV_HV_BALLOON_INTERNAL_H

#include "qemu/osdep.h"

#define HV_BALLOON_PFN_SHIFT 12
#define HV_BALLOON_PAGE_SIZE (1 << HV_BALLOON_PFN_SHIFT)

#define SUM_OVERFLOW_U64(in1, in2) ((in1) > UINT64_MAX - (in2))
#define SUM_SATURATE_U64(in1, in2)              \
    ({                                          \
        uint64_t _in1 = (in1), _in2 = (in2);    \
        uint64_t _result;                       \
                                                \
        if (!SUM_OVERFLOW_U64(_in1, _in2)) {    \
            _result = _in1 + _in2;              \
        } else {                                \
            _result = UINT64_MAX;               \
        }                                       \
                                                \
        _result;                                \
    })

#if !GLIB_CHECK_VERSION(2,68,0)

#if !GLIB_CHECK_VERSION(2,12,0)
#error Glib version far too old
#endif

typedef struct _GTreeNode GTreeNode;

struct _GTreeNode
{
  gpointer   key;         /* key for this node */
  gpointer   value;       /* value stored at this node */
  GTreeNode *left;        /* left subtree */
  GTreeNode *right;       /* right subtree */
  gint8      balance;     /* height (right) - height (left) */
  guint8     left_child;
  guint8     right_child;
};

struct _GTree
{
  GTreeNode        *root;
  GCompareDataFunc  key_compare;
  GDestroyNotify    key_destroy_func;
  GDestroyNotify    value_destroy_func;
  gpointer          key_compare_data;
  guint             nnodes;
  gint              ref_count;
};

static inline gpointer
g_tree_node_value (GTreeNode *node)
{
  g_return_val_if_fail (node != NULL, NULL);

  return node->value;
}

static inline GTreeNode *
g_tree_node_first (GTree *tree)
{
  GTreeNode *tmp;

  g_return_val_if_fail (tree != NULL, NULL);

  if (!tree->root)
    return NULL;

  tmp = tree->root;

  while (tmp->left_child)
    tmp = tmp->left;

  return tmp;
}

static inline GTreeNode *
g_tree_node_last (GTree *tree)
{
  GTreeNode *tmp;

  g_return_val_if_fail (tree != NULL, NULL);

  if (!tree->root)
    return NULL;

  tmp = tree->root;

  while (tmp->right_child)
    tmp = tmp->right;

  return tmp;
}

static inline GTreeNode *
g_tree_node_previous (GTreeNode *node)
{
  GTreeNode *tmp;

  g_return_val_if_fail (node != NULL, NULL);

  tmp = node->left;

  if (node->left_child)
    while (tmp->right_child)
      tmp = tmp->right;

  return tmp;
}

static inline GTreeNode *
g_tree_node_next (GTreeNode *node)
{
  GTreeNode *tmp;

  g_return_val_if_fail (node != NULL, NULL);

  tmp = node->right;

  if (node->right_child)
    while (tmp->left_child)
      tmp = tmp->left;

  return tmp;
}

static inline GTreeNode *
g_tree_upper_bound (GTree         *tree,
                    gconstpointer  key)
{
  GTreeNode *node, *result;
  gint cmp;

  g_return_val_if_fail (tree != NULL, NULL);

  node = tree->root;
  if (!node)
    return NULL;

  result = NULL;
  while (1)
    {
      cmp = tree->key_compare (key, node->key, tree->key_compare_data);
      if (cmp < 0)
        {
          result = node;

          if (!node->left_child)
            return result;

          node = node->left;
        }
      else
        {
          if (!node->right_child)
            return result;

          node = node->right;
        }
    }
}

/*
 * Have to re-implement this as insert + lookup as there's no way to access
 * the internal GTree insert + rebalance function.
 */
static inline GTreeNode *
g_tree_insert_node (GTree    *tree,
                    gpointer  key,
                    gpointer  value)
{
  GTreeNode *node;
  gint cmp;

  g_tree_insert (tree, key, value);

  node = tree->root;
  assert (node);

  while (1)
    {
      cmp = tree->key_compare (key, node->key, tree->key_compare_data);
      if (cmp == 0)
        return node;
      else if (cmp < 0)
        {
          assert (node->left_child);
          node = node->left;
        }
      else
        {
          assert (node->right_child);
          node = node->right;
        }
    }

  assert (false);
}
#endif

#endif
