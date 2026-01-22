###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/.
#
###############################################################################

via_tree_node_parent_left_right_tagger_def = '''
DECLARE
    tn VIA_TREE_NODE_CHILD_COUNT;

    nodes_on_the_left BIGINT;
    parents_nodes_on_the_left BIGINT[];
    next_parents_nodes_on_the_left BIGINT[] := ARRAY[0]::BIGINT[];
    parent_idx BIGINT;
    last_level BIGINT := NULL;
    last_parent_id BIGINT := NULL;

    parent_left BIGINT;
    parent_right BIGINT;

    last_node VIA_TREE_NODE_UNROLLED;
    last_node_nodes_on_the_left BIGINT;
    last_node_child_count BIGINT;
BEGIN
    FOR tn IN SELECT *
              FROM UNNEST(unrolled_tree_nodes)
              ORDER BY unique_id LOOP
        IF last_level IS NULL OR last_level != tn.level THEN
            parent_idx := 0;
            parents_nodes_on_the_left := next_parents_nodes_on_the_left;
            next_parents_nodes_on_the_left := ARRAY[]::BIGINT[];
        END IF;

        IF last_parent_id IS NULL THEN
            IF parent_idx = 0 THEN
                parent_idx := 1;
                nodes_on_the_left := parents_nodes_on_the_left[parent_idx];
            ELSE
                nodes_on_the_left := (last_node_child_count
                                      + last_node_nodes_on_the_left
                                      + 1);
            END IF;
        ELSE
            IF last_parent_id != tn.unique_parent_id THEN
                parent_idx := parent_idx + 1;
                nodes_on_the_left := parents_nodes_on_the_left[parent_idx];
            ELSE
                nodes_on_the_left := (last_node_child_count
                                      + last_node_nodes_on_the_left
                                      + 1);
            END IF;
        END IF;

        IF tn.child_count != 0 THEN
            next_parents_nodes_on_the_left := (next_parents_nodes_on_the_left
                                               || nodes_on_the_left);
        END IF;

        parent_left := 1 + 2 * nodes_on_the_left + tn.level;
        parent_right := parent_left + tn.child_count * 2 + 1;

        last_node := (tn.id,
                      tn.parent_id,
                      tn.level,
                      parent_left,
                      parent_right)::VIA_TREE_NODE_UNROLLED;
        RETURN NEXT last_node;

        last_level := tn.level;
        last_parent_id := tn.unique_parent_id;
        last_node_child_count := tn.child_count;
        last_node_nodes_on_the_left := nodes_on_the_left;
    END LOOP;
END
'''

via_tree_node_unroller_def = '''
DECLARE
    tree_nodes_now VIA_TREE_NODE_LEVEL_TAGGER_DATUM[];

    tree_nodes_next VIA_TREE_NODE_LEVEL_TAGGER_DATUM[];

    result VIA_TREE_NODE_LEVEL_TAGGER_DATUM[];

    last_node_count BIGINT := 0;

    current_node_count BIGINT := COALESCE(ARRAY_LENGTH(tree_nodes, 1), 0);

    unique_id_offset BIGINT := 0;

    next_iteration NO SCROLL CURSOR(tree_nodes_ VIA_TREE_NODE_LEVEL_TAGGER_DATUM[],
                                    unique_id_offset_ BIGINT)
        FOR
         WITH top_level AS (
          SELECT
           id,
           (unique_id_offset_ + ROW_NUMBER()
            OVER (ORDER BY
             unique_parent_id ASC,
             -- Additional ordering clauses should go here by making this query dynamic
             id ASC
           ))::BIGINT AS unique_id,
           unique_parent_id
          FROM UNNEST(tree_nodes_) tn
          WHERE unrolling_pid IS NULL
         )
         SELECT
          tn.id AS id,
          tn.parent_id AS parent_id,
          tn.level + (CASE
                       WHEN tn.unrolling_pid IS NULL
                        THEN 0 -- top-level nodes are at this level
                       ELSE 1 -- make all other nodes deeper by one level
                      END) AS level,
          (CASE
            WHEN top_level.id IS NULL
             THEN tn.unrolling_pid -- this node is not the next top-level node
            ELSE NULL -- this node is the next top-level node
           END) AS next_unrolling_pid, -- the next top-level node will have NULL here
          tn.unrolling_pid AS unrolling_pid, -- will be NULL for current top-level nodes
          unique_id_src.unique_id AS unique_id,
          (CASE
            WHEN tn.unrolling_pid IS NULL
             THEN tn.unique_parent_id -- top-level nodes unique_parent_id must stay the same
            ELSE top_level.unique_id -- all other nodes unique_parent_id depends on their parents
           END) AS unique_parent_id
         FROM UNNEST(tree_nodes_) tn
          LEFT JOIN top_level
           ON tn.unrolling_pid = top_level.id
          LEFT JOIN top_level AS unique_id_src
           ON (((tn.unique_parent_id IS NULL OR unique_id_src.unique_parent_id = tn.unique_parent_id)
                 AND unique_id_src.id = tn.id)
               AND tn.unrolling_pid IS NULL);
BEGIN
    tree_nodes_now := (SELECT ARRAY_AGG(
                           DISTINCT
                           (id, parent_id,
                             0, parent_id, NULL, NULL)::VIA_TREE_NODE_LEVEL_TAGGER_DATUM
                       )
                       FROM UNNEST(tree_nodes));

    WHILE last_node_count != current_node_count LOOP
        last_node_count := current_node_count;
        tree_nodes_next := ARRAY[]::VIA_TREE_NODE_LEVEL_TAGGER_DATUM[];
        FOR rec IN next_iteration(tree_nodes_now, unique_id_offset) LOOP
            IF rec.unrolling_pid IS NULL THEN
                unique_id_offset := unique_id_offset + 1;
                result := ARRAY_APPEND(result,
                                       (rec.id,
                                        rec.parent_id,
                                        rec.level,
                                        NULL,
                                        rec.unique_id,
                                        rec.unique_parent_id)::VIA_TREE_NODE_LEVEL_TAGGER_DATUM);
            ELSE
                tree_nodes_next := ARRAY_APPEND(tree_nodes_next,
                                                (rec.id,
                                                 rec.parent_id,
                                                 rec.level,
                                                 rec.next_unrolling_pid,
                                                 NULL,
                                                 rec.unique_parent_id)::VIA_TREE_NODE_LEVEL_TAGGER_DATUM);
            END IF;
        END LOOP;
        tree_nodes_now := tree_nodes_next;
        current_node_count := COALESCE(ARRAY_LENGTH(tree_nodes_now, 1), 0);
    END LOOP;

    RETURN QUERY SELECT * FROM UNNEST(result) ORDER BY unique_id;
END
'''

via_tree_node_count_children_def = '''
BEGIN
    RETURN QUERY
     WITH RECURSIVE
      child_count_table(unique_id, level, child_count) AS (
        (SELECT
          tn.unique_parent_id, (tn.level - 1)::BIGINT, COUNT(tn.unique_id)::BIGINT
         FROM UNNEST(unrolled_tree_nodes) tn
         WHERE
          tn.level = (SELECT MAX(level) AS level FROM UNNEST(unrolled_tree_nodes))
         GROUP BY
          tn.unique_parent_id,
          tn.level)
       UNION ALL
        (WITH frozen_child_count_table AS (
          SELECT * FROM child_count_table
         )
         SELECT
          tn.unique_parent_id, tn.level - 1, (COUNT(tn.unique_id) + COALESCE(SUM(cct.child_count), 0))::BIGINT
         FROM UNNEST(unrolled_tree_nodes) tn
          LEFT JOIN frozen_child_count_table cct
           ON tn.unique_id = cct.unique_id
         WHERE
          tn.level = (SELECT MAX(level) FROM frozen_child_count_table)
         GROUP BY
          tn.unique_parent_id,
          tn.level)
      )
     SELECT
      tn.id, tn.parent_id, tn.level, tn.unique_id, tn.unique_parent_id,
      COALESCE(cct.child_count, 0) AS child_count
     FROM UNNEST(unrolled_tree_nodes) tn
      LEFT JOIN child_count_table cct
       ON tn.unique_id = cct.unique_id
     ORDER BY
      unique_id ASC;
END
'''

via_tree_node_level_tagger_def = '''
BEGIN
    RETURN QUERY SELECT * FROM via_tree_node_parent_left_right_tagger((
        SELECT ARRAY_AGG((id,
                          parent_id,
                          level,
                          unique_id,
                          unique_parent_id,
                          child_count)::VIA_TREE_NODE_CHILD_COUNT)
        FROM via_tree_node_count_children((
            SELECT ARRAY_AGG((id,
                              parent_id,
                              level,
                              unrolling_pid,
                              unique_id,
                              unique_parent_id)::VIA_TREE_NODE_LEVEL_TAGGER_DATUM)
            FROM via_tree_node_unroller(tree_nodes)))
    ));
END
'''
