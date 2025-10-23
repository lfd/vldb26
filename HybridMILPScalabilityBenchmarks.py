#!/usr/bin/env python
# coding: utf-8

# In[1]:

import numpy as np
import math
import config as config
import gurobipy as gp
from gurobipy import GRB
import Scripts.ProblemLoader as ProblemLoader
import Scripts.JOUtil as JOUtil

import json
import os
import pathlib
import csv
from os import listdir
from os.path import isfile, join
from pathlib import Path


def save_to_csv(data, path, filename):

    sd = os.path.abspath(path)
    pathlib.Path(sd).mkdir(parents=True, exist_ok=True) 
    
    f = open(path + '/' + filename, 'a', newline='')
    writer = csv.writer(f)
    writer.writerow(data)
    f.close()


def load_data(path, filename):
    datafile = os.path.abspath(path + '/' + filename)
    if os.path.exists(datafile):
        with open(datafile, 'rb') as file:
            return json.load(file)
        
def load_all_results(path):
    if not os.path.isdir(path):
        return []
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    data = []
    for datafile in onlyfiles:
        with open(path + '/' + datafile, 'rb') as file:
            data.append(json.load(file))
    return data

def save_data(data, path, filename, override=True):
    datapath = os.path.abspath(path)
    pathlib.Path(datapath).mkdir(parents=True, exist_ok=True) 
    
    datafile = os.path.abspath(path + '/' + filename)
    if os.path.exists(datafile):
        if override:
            try:
                os.remove(datafile)
            except OSError:
                pass
        else:
            return
    mode = 'a' if os.path.exists(datafile) else 'w'
    with open(datafile, mode) as file:
        json.dump(data, file)



def generate_template(num_relations, num_right_leaf_predecessors, depth_limit=5):
    num_active_joins = num_relations - 1
    
    successors = []
    
    # balanced structure
    current_nodes = [0]
    join_counter = 1
    left_deep_nodes = [0]
    right_join_leaf = 0

    done_counter = 0
    while join_counter < num_active_joins and done_counter < depth_limit:
        next_nodes = []
        current_index = 0
        left_children_done = False
        done = False
        while not done:
            current_node = current_nodes[current_index]
            child = join_counter
            successors.append((child, current_node))
            if left_deep_nodes[-1] == current_node:
                left_deep_nodes.append(child)
            if right_join_leaf == current_node:
                if child not in left_deep_nodes:
                    right_join_leaf = child
            if child not in next_nodes:
                next_nodes.append(child)
            
            join_counter = join_counter + 1
            if join_counter >= num_active_joins:
                break
            current_index = current_index + 1
            if current_index == len(current_nodes):
                if left_children_done:
                    done = True
                    done_counter = done_counter + 1
                else:
                    left_children_done = True   
                    current_index = 0
        current_nodes = next_nodes        
       

    num_joins = join_counter
    
    num_left_deep_leaf_successors = num_relations-len(left_deep_nodes)-1
    

    if num_right_leaf_predecessors > 0:
        leaf_joins = {left_deep_nodes[-1]: num_left_deep_leaf_successors, right_join_leaf: num_right_leaf_predecessors}
    else:
        leaf_joins = {left_deep_nodes[-1]: num_left_deep_leaf_successors}
    
    tree_template = {"successors": successors, "num_joins": num_joins, "leaf_joins": leaf_joins}
    print(tree_template)
    return tree_template


def get_predecessors_and_successors(successor_list, num_joins):
    predecessors = {}
    successors = {}
    for i in range(num_joins):
        predecessors[i] = []
        
    for (i, j) in successor_list:
        predecessors[j].append(i)
        successors[i] = j
    return predecessors, successors
    
def get_global_predecessors(num_joins, predecessors, successors):
    global_predecessors = {}
    for i in range(num_joins):
        global_predecessors[i] = []
        
    current_joins = [0]
    leaves = [x for x in range(num_joins) if len(predecessors[x]) == 0]
    
    current_joins = leaves
    while len(current_joins) > 0:
        current_join = current_joins.pop(0)
        if current_join in successors.keys():
            successor = successors[current_join]
            global_predecessors[successor].append(current_join)
            global_predecessors[successor].extend(global_predecessors[current_join])
            current_joins.insert(0, successor)
        
    for i in range(num_joins):
        global_predecessors[i] = list(set(global_predecessors[i]))
    return global_predecessors
    
    
def get_leaf_coeff(num_variables, bound):
    var_coeff = []
    for i in range(num_variables-1):
        var_coeff.append(int(pow(2, i)))
    suffix_value = bound + 1 - int(pow(2, num_variables-1))
    var_coeff.append(int(suffix_value))
    return var_coeff
    
def solve_template(tree_template, card, pred, pred_sel, thresholds_for_join, time_limit, penalty_value):
    wlsaccessid = config.configuration["gurobi-wlsaccessid"]
    wlssecret = config.configuration["gurobi-wlssecret"]
    gurobi_licenseid = config.configuration["gurobi-licenseid"]
    
    if wlsaccessid == "" or wlssecret == "" or gurobi_licenseid == 0:
        print("Please provide wlsaccessid, wlssecret and gurobi_licenseid in the configuration file.")
        return
    
    params = {  
    "WLSACCESSID": wlsaccessid,
    "WLSSECRET": wlssecret,
    "LICENSEID": gurobi_licenseid,
    }
    env = gp.Env(params=params)
    
    
    num_tables = len(card)
    num_joins = tree_template["num_joins"]
    num_preds = len(pred)
    leaf_joins = tree_template["leaf_joins"]
    
    m = gp.Model("bip", env=env)

    
    v = m.addVars(num_tables, num_joins, vtype=GRB.BINARY, name="v")
    
    ja = m.addVars(num_joins-1, vtype=GRB.BINARY, name="ja")
    
    leaf_join_var_dict = {}
    leaf_join_var_coeffs = {}
    for (leaf_join, num_predecessors) in leaf_joins.items():
        M = int(math.floor(np.log2(num_predecessors)))
        bound = M + 1
        leaf_join_var_dict[leaf_join] = m.addVars(bound, vtype=GRB.BINARY, name="leaf" + str(leaf_join))
        leaf_join_var_coeffs[leaf_join] = get_leaf_coeff(bound, num_predecessors)
    
    pao = m.addVars(num_preds, num_joins, vtype=GRB.BINARY, name="pao")
    
    successor_list = tree_template["successors"] 
    
    predecessors, successors = get_predecessors_and_successors(successor_list, num_joins)
    
    global_predecessors = get_global_predecessors(num_joins, predecessors, successors)
    
    
    # Enforce that root join contains all operands
    m.addConstr(v.sum('*', 0) == num_tables)
    
    # Enforce the correct amount of join active variables
    max_num_leaf_vars = max(leaf_joins.values())
    num_active_joins = num_tables - 2
    
    constr_coeffs = []
    constr_vars = []
    for leaf_join in leaf_joins.keys():
        leaf_join = int(leaf_join)
        for idx in range(len(leaf_join_var_coeffs[leaf_join])):
            constr_coeffs.append(leaf_join_var_coeffs[leaf_join][idx])
            constr_vars.append(leaf_join_var_dict[leaf_join][idx])

    m.addConstr(ja.sum('*') + gp.quicksum(constr_coeffs[i]*constr_vars[i] for i in range(len(constr_coeffs)))  == num_active_joins)
    
    for i in range(num_joins):
        pred_i = predecessors[i]
        global_pred_i = global_predecessors[i]
        
        if i != 0:
            # Active predecessor joins imply active root join
            if i in leaf_joins.keys():
                m.addConstr(gp.quicksum(leaf_join_var_coeffs[i][j]*leaf_join_var_dict[i][j] for j in range(len(leaf_join_var_dict[i]))) <= leaf_joins[i]*ja[i-1])
            else:
                m.addConstrs(ja[j-1] <= ja[i-1] for j in pred_i)

            # Operands imply active join
            m.addConstrs(v[t, i] <= ja[i-1] for t in range(num_tables))
                
            applicable_leaves = [x for x in leaf_joins.keys() if x == i or x in global_pred_i]
 
            constr_coeffs = []
            constr_vars = []
            for applicable_leaf in applicable_leaves:
                for idx in range(len(leaf_join_var_coeffs[applicable_leaf])):
                    constr_coeffs.append(leaf_join_var_coeffs[applicable_leaf][idx])
                    constr_vars.append(leaf_join_var_dict[applicable_leaf][idx])
       
            m.addConstr(v.sum('*', i) == 2*ja[i-1] + gp.quicksum(ja[j-1] for j in global_pred_i) + gp.quicksum(constr_coeffs[j]*constr_vars[j] for j in range(len(constr_coeffs))))
                
            # Predecessor operands imply root operands
            m.addConstrs(v[t, j] <= v[t, i] for t in range(num_tables) for j in pred_i)
                
            #if i in leaf_joins.keys():
                #m.addConstr(pao.sum('*', i) == v.sum('*', i)-1)
            
        # Prevent conflicting assignments
        if len(pred_i) == 2:
            m.addConstrs(v[t, pred_i[0]] + v[t, pred_i[1]] <= 1 for t in range(num_tables))
    
    # Prevent invalid predicates
    
    m.addConstrs(pao[p, i] <= v[pred[p][0], i] for p in range(num_preds) for i in range(num_joins))
    m.addConstrs(pao[p, i] <= v[pred[p][1], i] for p in range(num_preds) for i in range(num_joins))
    

    log_thresholds_for_join = {}
    for (i, thresholds) in thresholds_for_join.items():
        log_thresholds_for_join[i] = [np.log2(x) for x in thresholds]
    
    log_card = [np.log2(x) for x in card]
    log_pred_sel = [np.log2(x) for x in pred_sel]
    cto_dict = {}
    for i in range(num_joins):
        if i == 0:
            continue
        num_thresh = len(thresholds_for_join[i])
        cto = m.addVars(num_thresh, vtype=GRB.BINARY, name="cto")
        cto_dict[i] = cto
        for t in range(num_thresh):
            log_thres = log_thresholds_for_join[i][t]
            m.addConstr(gp.quicksum(log_card[r]*v[r, i] for r in range(num_tables)) + gp.quicksum(log_pred_sel[p]*pao[p, i] for p in range(num_preds)) - cto[t]*penalty_value <= log_thres)

    m.setObjective(gp.quicksum(cto_dict[i][t]*thresholds_for_join[i][t] for t in range(len(thresholds_for_join[i])) for i in range(1, num_joins)), GRB.MINIMIZE)

    m.setParam('TimeLimit', time_limit)
    
    m.update()
        
    m.optimize()
    
    if m.SolCount < 1:
        return {}
        
    op_list = {}
    for i in range(num_joins):
        op_list[i] = []
        
    for (k, val) in v.items():
        table_index = k[0]
        join_index = k[1]
        if np.rint(val.X) == 1:
            op_list[join_index].append(table_index)

    costs, int_costs, cp_flag = JOUtil.get_costs_for_bushy_tree(list(op_list.values()), card, pred, pred_sel, {})
    raw_result = {"costs": costs, "join_operands": op_list, "join_predecessors": predecessors, "leaf_joins": list(leaf_joins.keys()), "opt_time": m.Runtime, "status": m.status, "intermediate_costs": int_costs}
    

    return raw_result



def conduct_experiments_template(graph_types, relations, problems, max_depth, num_right_leaf_predecessors, problem_path_prefix, threshold_path_prefix, threshold_index, time_limit, result_path_prefix):
    for graph_type in graph_types:
        for i in relations:
            for j in problems:
                j = int(j)

                problem_path_main = graph_type + '_graph/' + str(i) + 'relations/' + str(j)
                card, pred, pred_sel = ProblemLoader.get_join_ordering_problem(problem_path_prefix + '/synthetic/' + problem_path_main, generated_problems=True)
                tree_template = generate_template(i, num_right_leaf_predecessors, depth_limit=max_depth)
                
                card = [float(x) for x in card]
                if 0.0 in pred_sel:
                    continue
                
                thresholds_for_join = {}
                
                threshold_path = threshold_path_prefix + str(threshold_index) + '/' + graph_type + '_graph/' + str(i) + 'relations/' + str(j)
                threshold_list = load_data(threshold_path, 'thresholds.json')
           
                for join in range(tree_template["num_joins"]):
                    thresholds_for_join[join] = threshold_list
                        
                result = solve_template(tree_template, card, pred, pred_sel, thresholds_for_join, time_limit, 100000)
                result_path = result_path_prefix + '/' + graph_type + '_graph/' + str(i) + 'relations/' + str(j) + '/maxdepth_' + str(max_depth) + '/thresh_' + str(threshold_index) + '/' + str(num_right_leaf_predecessors) + '_right_pred/' + str(time_limit) + 's'
                save_data(result, result_path, 'raw_result.json')
                

if __name__ == "__main__":
    
    problem_path_prefix = 'Experiments/Problems'
    threshold_path_prefix = 'Experiments/Thresholds'
    result_path_prefix = 'Experiments/Raw_Results'
    graph_types = ['TREE']
    relations = [20, 30, 40, 50, 60, 70, 80, 90, 100]
    problems = np.arange(100).tolist()
    
    time_limit = 60
    
    max_depth = 4
    threshold_index = 1
    num_right_leaf_predecessors = 10
    conduct_experiments_template(graph_types, relations, problems, max_depth, num_right_leaf_predecessors, problem_path_prefix, threshold_path_prefix, threshold_index, time_limit, result_path_prefix)
    
    max_depth = 5
    threshold_index = 1
    num_right_leaf_predecessors = 10
    conduct_experiments_template(graph_types, relations, problems, max_depth, num_right_leaf_predecessors, problem_path_prefix, threshold_path_prefix, threshold_index, time_limit, result_path_prefix)
    
    max_depth = 6
    threshold_index = 1
    num_right_leaf_predecessors = 10
    conduct_experiments_template(graph_types, relations, problems, max_depth, num_right_leaf_predecessors, problem_path_prefix, threshold_path_prefix, threshold_index, time_limit, result_path_prefix)
    
    max_depth = 7
    threshold_index = 1
    num_right_leaf_predecessors = 10
    conduct_experiments_template(graph_types, relations, problems, max_depth, num_right_leaf_predecessors, problem_path_prefix, threshold_path_prefix, threshold_index, time_limit, result_path_prefix)