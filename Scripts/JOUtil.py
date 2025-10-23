#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import numpy as np
from decimal import *


# In[ ]:

def contains_cross_products(join_operands, pred):
    pred_for_join = {}
    for (join, relations) in join_operands.items():
        pred_for_join[join] = []
        pred_counter = 0
        for (r1, r2) in pred:
            if r1 in relations and r2 in relations:
                pred_for_join[join].append((r1, r2))
                pred_counter = pred_counter + 1
        if pred_counter != len(relations)-1:
            return True
            
    return False

def is_valid(join_operands, join_predecessors, root_index, num_relations):
    if join_operands[root_index] != np.arange(num_relations).tolist():
        print("Root join does not contain all relations")
        return False 
    current_joins = [root_index]
    while len(current_joins) > 0:
        current_root_index = current_joins.pop(0)
        current_root_operands = join_operands[current_root_index]
        if len(current_root_operands) != len(set(current_root_operands)):
            print("Duplicate operands at join " + str(current_root_index))
            return False
        predecessors = join_predecessors[current_root_index]
        if len(predecessors) == 0:
            if len(current_root_operands) != 2:
                print("Incomplete join tree at join index " + str(current_root_index))
                return False
        if len(predecessors) == 1:
            pred_operands = join_operands[predecessors[0]]
            leaf_relations = [x for x in current_root_operands if x not in pred_operands]
            if len(pred_operands) != len(current_root_operands)-1:
                print("Incorrect number of relations at join index " + str(predecessors[0]))
                return False
            if len(leaf_relations) != 1:
                print("Missing relations at join index " + str(current_root_index))
                return False
            current_joins.append(predecessors[0])
        if len(predecessors) >= 2:
            left_operands = join_operands[predecessors[0]]
            right_operands = join_operands[predecessors[1]]
            joint_operands = left_operands.copy()
            joint_operands.extend(right_operands)
            
            if left_operands == current_root_operands or right_operands == current_root_operands:
                print("Predecessor equals root at join " + str(current_root_index))
                return False
            if len(left_operands) < 2 or len(right_operands) < 2:
                print("Invalid number of predecessor operands at join index " + str(current_root_index))
                return False
            if sorted(joint_operands) != current_root_operands:
                print("Predecessor relations do not correspond to root relations at join index " + str(current_root_index))
                return False
            current_joins.append(predecessors[0])
            current_joins.append(predecessors[1])
       
    return True

def get_costs_for_bushy_tree(join_list, card, pred, pred_sel, card_dict={}):

    cost = 0
    int_costs = []
    cp_flag = False
    for relations in join_list:
        relations = sorted(relations)
        jo_hash = str(relations)
        intermediate_cost = 0
        if jo_hash in card_dict:
            intermediate_cost = card_dict[jo_hash]
            
            int_costs.append((relations, intermediate_cost))
            cost = cost + intermediate_cost
            continue
        if len(relations) < 2:
            continue
        if len(relations) == len(card):
            continue
            
        #card_prod = np.prod(np.array(card)[relations])
        card_prod = Decimal(card[relations[0]])
        for i in range(1, len(relations)):
            card_prod = card_prod * Decimal(card[relations[i]])
        
        pred_prod = Decimal(1)
        
        cp_checklist = relations.copy()
        for p in range(len(pred)):
            (r1, r2) = pred[p]
            if r1 in relations and r2 in relations:
                if r1 in cp_checklist:
                    cp_checklist.remove(r1)
                if r2 in cp_checklist:
                    cp_checklist.remove(r2)  
                pred_prod = pred_prod * Decimal(pred_sel[p])
        intermediate_cost = card_prod * pred_prod

        card_dict[jo_hash] = intermediate_cost
        int_costs.append((relations, float(intermediate_cost)))
        cost = cost + intermediate_cost
        if len(cp_checklist) > 0:
            cp_flag = True
            #print(relations)
    #if not cp_flag:
        #print("Non CP costs: " + str(cost))
        
    return float(cost), int_costs, cp_flag

