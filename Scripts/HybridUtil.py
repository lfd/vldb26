#!/usr/bin/env python
# coding: utf-8

# In[1]:

import numpy as np
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

import re
from math import inf


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


def generate_template(num_relations, depth_limit=5):
    num_active_joins = num_relations - 1
    
    successors = []
    
    # balanced structure
    current_nodes = [0]
    join_counter = 1
    left_deep_nodes = [0]

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
                    
        
    # left-deep structure 
    left_deep_counter = len(left_deep_nodes)
    current_node = left_deep_nodes[-1]
    while left_deep_counter < num_active_joins:
        successors.append((join_counter, current_node))
        current_node = join_counter
        join_counter = join_counter + 1
        left_deep_counter = left_deep_counter + 1
        
    num_joins = join_counter
    
    tree_template = {"successors": successors, "num_joins": num_joins}
    print(tree_template)
    return tree_template

    
    
def filter_raw_problem(raw_problem, operands):
    filtered_raw_problem = {}
    filtered_raw_problem["relations"] = []
    for relation in raw_problem["relations"]:
        relation_index = int(relation["name"].split("r")[1])
        if relation_index in operands:
            filtered_raw_problem["relations"].append(relation)
            
    filtered_raw_problem["joins"] = []
    join_counter = 0
    for join in raw_problem["joins"]:
        relation1 = int(join["relations"][0].split("r")[1])
        relation2 = int(join["relations"][1].split("r")[1])
        if relation1 in operands and relation2 in operands:
            join_counter = join_counter + 1
            filtered_raw_problem["joins"].append(join)

    filtered_raw_problem["sizes"] = []
    for size in raw_problem["sizes"]:
        relation1 = int(size["relations"][0].split("r")[1])
        relation2 = int(size["relations"][1].split("r")[1])
        if relation1 in operands and relation2 in operands:
            filtered_raw_problem["sizes"].append(size)
    
    if join_counter != len(operands) - 1:
        contains_cp = True
    else:
        contains_cp = False
    return filtered_raw_problem, contains_cp
    
def generate_subproblem(unfinished_operands, graph_type, relations, problem):
    problem_string = ''
    if problem < 10:
        problem_string = '0' + str(problem)
    else:
        problem_string = str(problem)
    if relations < 100:
        filename = 'fk-tree-00' + str(relations) + '-' + problem_string
    else:
        filename = 'fk-tree-0' + str(relations) + '-' + problem_string  
    raw_problem = load_data(raw_problem_path, filename)
    
    filtered_raw_problem, contains_cp = filter_raw_problem(raw_problem, unfinished_operands)
    return filtered_raw_problem, contains_cp
    
    
def get_join_index_for_operands(join_index_for_operands, join_operands, result_operands, join_counter):
    if frozenset(result_operands) not in join_index_for_operands.keys():
        join_index = join_counter 
        join_operands[join_index] = result_operands
        join_index_for_operands[frozenset(result_operands)] = join_index
        return join_index, join_counter + 1
    else: 
        join_index = join_index_for_operands[frozenset(result_operands)]
        return join_index, join_counter
 
def build_join_tree(join_string):
    join_operands = {}
    join_index_for_operands = {}
    join_predecessors = {}
    join_indices = [m.start() for m in re.finditer('join', join_string)]
    join_counter = 0
    
    for join_index in join_indices:
        # Left operand
        left_operand_close_indices = [m.start() for m in re.finditer('\)', join_string[:join_index])]
        left_operand_close_index = left_operand_close_indices[len(left_operand_close_indices)-1]
        left_operand_start_index = None
        left_operand_start_count = 1
        current_position = left_operand_close_index
        while left_operand_start_count > 0:
            close_indices = [m.start() for m in re.finditer('\)', join_string[:current_position])]
            if len(close_indices) > 0:
                next_close_index = close_indices[len(close_indices)-1]
            else:
                next_close_index = None
            start_indices = [m.start() for m in re.finditer('\(', join_string[:current_position])]
            next_start_index = start_indices[len(start_indices)-1]
            if next_close_index is None or next_start_index > next_close_index:
                left_operand_start_count = left_operand_start_count - 1
                current_position = next_start_index
            else:
                left_operand_start_count = left_operand_start_count + 1
                current_position = next_close_index
        left_operand_start_index = next_start_index
        left_operand_string = join_string[left_operand_start_index:left_operand_close_index]
        
        # Right operand
        right_operand_start_indices = [m.start() for m in re.finditer('\(', join_string[join_index:])]
        right_operand_start_index = right_operand_start_indices[0] + join_index
        right_operand_close_index = None
        right_operand_start_count = 1
        current_position = right_operand_start_index + 1
        while right_operand_start_count > 0:
            start_indices = [m.start() for m in re.finditer('\(', join_string[current_position:])]
            if len(start_indices) > 0:
                next_start_index = start_indices[0] + current_position
            else:
                next_start_index = None
            close_indices = [m.start() for m in re.finditer('\)', join_string[current_position:])]
            next_close_index = close_indices[0] + current_position
            if next_start_index is None or next_close_index < next_start_index:
                right_operand_start_count = right_operand_start_count - 1
                current_position = next_close_index + 1
            else:
                right_operand_start_count = right_operand_start_count + 1
                current_position = next_start_index + 1
        right_operand_close_index = next_close_index
        right_operand_string = join_string[right_operand_start_index:right_operand_close_index]
        
        # Extract relations for join
        relations = []
        left_operands = [int(x[1:])-1 for x in re.findall(r'\bR\w+',left_operand_string)]
        left_operands = sorted(left_operands)
        
        right_operands = [int(x[1:])-1 for x in re.findall(r'\bR\w+',right_operand_string)]
        right_operands = sorted(right_operands)

        result = left_operands.copy()
        result.extend(right_operands)
        result = sorted(result)
        
        result_index, join_counter = get_join_index_for_operands(join_index_for_operands, join_operands, result, join_counter)
        join_predecessors[result_index] = []
        if len(left_operands) > 1:
            left_operands_index, join_counter = get_join_index_for_operands(join_index_for_operands, join_operands, left_operands, join_counter) 
            join_predecessors[result_index].append(left_operands_index)
        if len(right_operands) > 1:
            right_operands_index, join_counter = get_join_index_for_operands(join_index_for_operands, join_operands, right_operands, join_counter) 
            join_predecessors[result_index].append(right_operands_index)


    return join_operands, join_predecessors    
    
def parse_results_for_subproblems(graph_types, relations, problems, max_depth, threshold_index, num_right_leaf_predecessors, time_limit, raw_problem_path, problem_path_prefix, result_path_prefix, subproblem_path):
    for graph_type in graph_types:
        for i in relations:
            for j in problems:
                j = int(j)

                problem_path_main = graph_type + '_graph/' + str(i) + 'relations/' + str(j)
                
                card, pred, pred_sel = ProblemLoader.get_join_ordering_problem(problem_path_prefix + '/synthetic/' + problem_path_main, generated_problems=True)
                tree_template = generate_template(i, depth_limit=max_depth)
                num_joins = tree_template["num_joins"]

                card = [float(x) for x in card]
                if 0.0 in pred_sel:
                    continue
                
                result_path = result_path_prefix + '/' + graph_type + '_graph/' + str(i) + 'relations/' + str(j) + '/maxdepth_' + str(max_depth) + '/thresh_' + str(threshold_index) + '/' + str(num_right_leaf_predecessors) + '_right_pred/' + str(time_limit) + 's'
                raw_result = load_data(result_path, 'raw_result.json')
                
                print(result_path)
                #unfinished_operands = raw_result["join_operands"][str(evaluation_bound-1)]
                #print(unfinished_operands)
                problem_for_leaf = {}
                cp_occurred = False
                for leaf_join in raw_result["leaf_joins"]:
                    leaf_operands = raw_result["join_operands"][str(leaf_join)]
                    if len(leaf_operands) == 0:
                        continue
                    filtered_raw_problem, contains_cp = generate_subproblem(leaf_operands, graph_type, i, j)
                    if contains_cp:
                        cp_occurred = True
                        break
                    problem_for_leaf[leaf_join] = filtered_raw_problem
                
                if cp_occurred: 
                    
                    print("cross products found")
                    print(result_path)
                    print("abandon")
                    continue
                for leaf_join in raw_result["leaf_joins"]:
                    leaf_operands = raw_result["join_operands"][str(leaf_join)]
                    if len(leaf_operands) == 0:
                        continue
                    filtered_raw_problem = problem_for_leaf[leaf_join]
                    subproblem_filename = graph_type + '_' + str(i) + '_p' + str(j) + '_md_' + str(max_depth) +'_t_' + str(threshold_index) + '_' + str(num_right_leaf_predecessors) + '_lp_l_' + str(leaf_join) + '_tl_' + str(time_limit)
                    save_data(filtered_raw_problem, subproblem_path, subproblem_filename)
                

         
def derive_total_solutions(graph_types, relations, problems, max_depth, threshold_index, num_right_leaf_predecessors, time_limit, raw_problem_path, problem_path_prefix, raw_result_path_prefix, result_path_prefix, subproblem_solutionpath):
    for graph_type in graph_types:
        for i in relations:
            for j in problems:
                j = int(j)

                problem_path_main = graph_type + '_graph/' + str(i) + 'relations/' + str(j)
                result_path = result_path_prefix + '/' + graph_type + '_graph/' + str(i) + 'relations/' + str(j) + '/maxdepth_' + str(max_depth) + '/thresh_' + str(threshold_index) + '/' + str(num_right_leaf_predecessors) + '_right_pred/' + str(time_limit) + 's'

                print(problem_path_main)
                card, pred, pred_sel = ProblemLoader.get_join_ordering_problem(problem_path_prefix + '/synthetic/' + problem_path_main, generated_problems=True)
                tree_template = generate_template(i, depth_limit=max_depth)
                num_joins = tree_template["num_joins"]

                card = [float(x) for x in card]
                if 0.0 in pred_sel:
                    continue
                
                raw_result_path = raw_result_path_prefix + '/' + graph_type + '_graph/' + str(i) + 'relations/' + str(j) + '/maxdepth_' + str(max_depth) + '/thresh_' + str(threshold_index) + '/' + str(num_right_leaf_predecessors) + '_right_pred/' + str(time_limit) + 's'
                raw_result = load_data(raw_result_path, 'raw_result.json')
                
                final_operands = {}
                final_predecessors = {}
                
                raw_join_operands = raw_result["join_operands"]
                    
                for (k,v) in raw_join_operands.items():
                    join_index = int(k)
                    final_operands[join_index] = v
                    
                raw_predecessors = raw_result["join_predecessors"]
                    
                for (k,v) in raw_predecessors.items():
                    root_index = int(k)
                    final_predecessors[root_index] = []
                    for predecessor in v:
                        pred_index = int(predecessor)
                        if len(final_operands[pred_index]) >= 2:
                            final_predecessors[root_index].append(pred_index)
                      
                result_missing = False
                for leaf_join in raw_result["leaf_joins"]:
                
                    leaf_operands = raw_result["join_operands"][str(leaf_join)]
                    
                    if len(leaf_operands) == 0:
                        continue
                    subproblem_filename = subproblem_solutionpath + '/' + graph_type + '_' + str(i) + '_p' + str(j) + '_md_' + str(max_depth) +'_t_' + str(threshold_index) + '_' + str(num_right_leaf_predecessors) + '_lp_l_' + str(leaf_join) + '_tl_' + str(time_limit) + '-adaptive'
                    if not os.path.exists(subproblem_filename):
                        result_missing = True        
                
                if result_missing:
                    print("Missing partial result:")
                    print(subproblem_filename)
                    save_data({}, result_path, 'milp.json')
                    continue  
                
                for leaf_join in raw_result["leaf_joins"]:
                
                    leaf_operands = raw_result["join_operands"][str(leaf_join)]
                    
                    if len(leaf_operands) == 0:
                        continue
                    
                    subproblem_filename = subproblem_solutionpath + '/' + graph_type + '_' + str(i) + '_p' + str(j) + '_md_' + str(max_depth) +'_t_' + str(threshold_index) + '_' + str(num_right_leaf_predecessors) + '_lp_l_' + str(leaf_join) + '_tl_' + str(time_limit) + '-adaptive'
                    

                    with open(subproblem_filename) as file:
                        lines = [line.rstrip() for line in file]
                    join_list = []
                    if len(lines) > 2:
                        join_operands, join_predecessors = build_join_tree(lines[2])
      
                    leaf_operands_index = None
                    
                    num_joins_raw = max(final_operands.keys()) + 1
                    for (k, v) in join_operands.items():
                        parsed_relations = []
                        for relation in v:
                            parsed_relations.append(leaf_operands[relation])
                        if parsed_relations == leaf_operands:
                            leaf_operands_index = k
                            continue
                        final_operands[k+num_joins_raw] = parsed_relations
                    
                    for (k, v) in join_predecessors.items():
                        if k == leaf_operands_index:
                            root_index = leaf_join
                        else:
                            root_index = k+num_joins_raw
                        
                        final_predecessors[root_index] = []
                        for predecessor in v:
                            final_predecessors[root_index].append(predecessor + num_joins_raw)

                #print(final_operands)
                #print(final_predecessors)
                
                if not JOUtil.is_valid(final_operands, final_predecessors, 0, i):
                    print("Invalid solution")
                    return
                costs, int_costs, cp_flag = JOUtil.get_costs_for_bushy_tree(list(final_operands.values()), card, pred, pred_sel, {})
    
                result_file = {'costs': int(costs), 'root_join': 0, 'join_operands': final_operands, 'join_predecessors': final_predecessors, 'intermediate_costs': int_costs}
                
                save_data(result_file, result_path, 'milp.json')
                
                result_path = result_path_prefix + '/' + graph_type + '_graph/' + str(i) + 'relations/' + str(j)

                save_data(result_file, result_path, 'milp.json')
                
                        
def derive_best_solution_for_configs(graph_types, relations, problems, parameter_configs, time_intervals, result_path_prefix, opt_threshold=1.5):
    for graph_type in graph_types:
        for i in relations:
            for j in problems:
                j = int(j)
                
                print(result_path_prefix + '/' + graph_type + '_graph/' + str(i) + 'relations/' + str(j))
                existing_path = os.path.abspath(result_path_prefix + '/' + graph_type + '_graph/' + str(i) + 'relations/' + str(j) + '/milp.json')
                if os.path.exists(existing_path):
                    try:
                        os.remove(existing_path)
                    except OSError:
                        pass
                min_costs = inf
                best_result = None
                best_config = None
                for (max_depth, threshold_index, num_right_leaf_predecessors) in parameter_configs:
                    for time_interval in time_intervals:
                        result_path = result_path_prefix + '/' + graph_type + '_graph/' + str(i) + 'relations/' + str(j) + '/maxdepth_' + str(max_depth) + '/thresh_' + str(threshold_index) + '/' + str(num_right_leaf_predecessors) + '_right_pred/' + str(time_interval) + 's'
                        result = load_data(result_path, 'milp.json')
                        
                        if result is None or len(result.keys()) == 0:
                            continue
                        if result["costs"] < min_costs:
                            min_costs = result["costs"]
                            best_result = result
                            best_config = (max_depth, threshold_index, num_right_leaf_predecessors)
                
                # Derive optimisation time until 50% threshold of the optimal solution
                
                threshold_reached = False
                current_interval = 0
                max_depth = best_config[0]
                threshold_index = best_config[1]
                num_right_leaf_predecessors = best_config[2]
                
                while not threshold_reached:
                    time_interval = time_intervals[current_interval]
                    result_path = result_path_prefix + '/' + graph_type + '_graph/' + str(i) + 'relations/' + str(j) + '/maxdepth_' + str(max_depth) + '/thresh_' + str(threshold_index) + '/' + str(num_right_leaf_predecessors) + '_right_pred/' + str(time_interval) + 's'
                    result = load_data(result_path, 'milp.json')
                    if result is not None and len(result.keys()) > 0 and result["costs"] <= int(min_costs * opt_threshold):
                        threshold_reached = True
                        best_result = result
                        best_result["time_in_s"] = time_interval
                    else:
                        current_interval = current_interval + 1
                
                result_path = result_path_prefix + '/' + graph_type + '_graph/' + str(i) + 'relations/' + str(j)
                save_data(best_result, result_path, 'milp.json')                

  
            