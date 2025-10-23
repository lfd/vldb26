#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
from math import prod
import math
import itertools
from math import inf
from sympy.utilities.iterables import multiset_permutations
import Scripts.ProblemLoader as ProblemLoader

import json
import os
import pathlib
import csv
from os import listdir
from os.path import isfile, join
from pathlib import Path

import time

import gzip


# In[ ]:


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
        
def save_data(data, path, filename):
    datapath = os.path.abspath(path)
    pathlib.Path(datapath).mkdir(parents=True, exist_ok=True) 
    
    datafile = os.path.abspath(path + '/' + filename)
    mode = 'a' if os.path.exists(datafile) else 'w'
    with open(datafile, mode) as file:
        json.dump(data, file)
        
def compress_and_save_data(data, path, filename):
    print(path)
    datapath = os.path.abspath(path)
    pathlib.Path(datapath).mkdir(parents=True, exist_ok=True) 
    
    datafile = os.path.abspath(path + '/' + filename)
    
    with gzip.open(datafile, 'wt', encoding='UTF-8') as zipfile:
        json.dump(data, zipfile)
        
def load_compressed_data(path, filename):
    datafile = os.path.abspath(path + '/' + filename)
    if os.path.exists(datafile):
        with gzip.open(datafile, 'rt', encoding='UTF-8') as zipfile:
            return json.load(zipfile)


# In[ ]:


def is_join_order_valid(join_order, num_card):
    jo_set = set(join_order.copy())
    indices = set(np.arange(num_card))
    
    diff1 = jo_set.difference(indices)
    diff2 = indices.difference(jo_set)
    if len(diff1) != 0 or len(diff2) != 0:
        print("Invalid join order detected.")
        return False
    return True
    
def export_benchmark_annealing_results(algorithm_list, benchmarks, problem_path_prefix, result_path_prefix, output_path, na_cost=20, timeout_in_ms=60000, include_header=True):
    if include_header:
        csv_data = ['method', 'benchmark', 'problem', 'baseline_cost', 'cost', 'normalised_cost']
        save_to_csv(csv_data, output_path, 'results.txt')     
    
    for benchmark in benchmarks:
        queries = os.listdir(path=problem_path_prefix + '/' + benchmark)
        for query in queries:
            query_number = int(query.split('q')[1])

            csv_data_list = []
            baseline_cost = inf

            problem_path_main = benchmark + '/' + query
            print(problem_path_main)
            card, pred, pred_sel = ProblemLoader.get_benchmark_join_ordering_problem(problem_path_prefix + '/' + problem_path_main, generated_problems=True)
                
            if len(card) < 3 or 0.0 in pred_sel:
                continue
                                
            algorithm_path = result_path_prefix + '/' + problem_path_main
                
            for algorithm in algorithm_list:
                algorithm_results = load_data(algorithm_path, algorithm + ".json")
                   
                if algorithm_results is None or "costs" not in algorithm_results.keys():
                    if algorithm == "milp":
                        print("MILP result missing")
                        print(problem_path_prefix + '/synthetic/' + problem_path_main)
                    csv_data_list.append([algorithm, benchmark, query_number, 0, 'n/a', na_cost])
                    continue
                       
                costs = algorithm_results["costs"]
                if costs == 0:
                    continue
                if costs < baseline_cost:
                    baseline_cost = costs
                        
                csv_data_list.append([algorithm, benchmark, query_number, 0, costs, 0])
                    
            # Export csv data
            for csv_data in csv_data_list:
                csv_data[3] = baseline_cost
                if csv_data[len(csv_data)-2] != 'n/a' and int(baseline_cost) != 0:
                    normalised_cost = csv_data[len(csv_data)-2]/int(baseline_cost)
                    if normalised_cost > na_cost:
                        csv_data[len(csv_data)-1] = na_cost
                    else:
                        csv_data[len(csv_data)-1] = normalised_cost
                else:
                    csv_data[len(csv_data)-1] = na_cost
                save_to_csv(csv_data, output_path, 'results.txt')    
    

def export_synthetic_annealing_results_saved(algorithm_list, graph_types, relations, problems, problem_path_prefix, result_path_prefix, output_path, na_cost=20, timeout_in_ms=60000, include_header=True):
    if include_header:
        csv_data = ['method', 'num_relations', 'graph_type', 'problem', 'baseline_cost', 'cost', 'normalised_cost']
        save_to_csv(csv_data, output_path, 'results.txt')     
    
    for graph_type in graph_types:
        for relation in relations:
            for j in problems:
                csv_data_list = []
                baseline_cost = inf

                problem_path_main = graph_type + '_graph/' + str(relation) + 'relations/' + str(j)
                card, pred, pred_sel = ProblemLoader.get_join_ordering_problem(problem_path_prefix + '/synthetic/' + problem_path_main, generated_problems=True)
                
                if len(card) < 3 or 0.0 in pred_sel:
                    continue
                
                algorithm_path = result_path_prefix + '/' + problem_path_main
                #algorithm_result_files = os.listdir(path=algorithm_path)
                
                for algorithm in algorithm_list:
                    #algorithm = algorithm_result_file.split(".")[0]
                    #print(algorithm_path)
                    algorithm_results = load_data(algorithm_path, algorithm + ".json")
                   
                    if algorithm_results is None or "costs" not in algorithm_results.keys():
                        if algorithm == "milp":
                            print("MILP result missing")
                            print(problem_path_prefix + '/synthetic/' + problem_path_main)
                        csv_data_list.append([algorithm, relation, graph_type, j, 0, 'n/a', na_cost])
                        continue
                       
                    costs = algorithm_results["costs"]
                    if costs == 0:
                        continue
                    if costs < baseline_cost:
                        baseline_cost = costs
                        
                    csv_data_list.append([algorithm, relation, graph_type, j, 0, costs, 0])
                    
                # Export csv data
                for csv_data in csv_data_list:
                    csv_data[4] = baseline_cost
                    if csv_data[len(csv_data)-2] != 'n/a' and int(baseline_cost) != 0:
                        normalised_cost = csv_data[len(csv_data)-2]/int(baseline_cost)
                        if normalised_cost > na_cost:
                            csv_data[len(csv_data)-1] = na_cost
                        else:
                            csv_data[len(csv_data)-1] = normalised_cost
                    else:
                        csv_data[len(csv_data)-1] = na_cost
                    save_to_csv(csv_data, output_path, 'results.txt')
                    
def export_synthetic_annealing_results(algorithm_list, graph_types, relations, problems, problem_path_prefix, result_path_prefix, output_path, na_cost=20, timeout_in_ms=60000, include_header=True):
    if include_header:
        csv_data = ['method', 'num_relations', 'graph_type', 'problem', 'baseline_cost', 'cost', 'normalised_cost', 'time_in_ms']
        save_to_csv(csv_data, output_path, 'results.txt')     
    
    for graph_type in graph_types:
        for relation in relations:
            for j in problems:
                csv_data_list = []
                baseline_cost = inf

                problem_path_main = graph_type + '_graph/' + str(relation) + 'relations/' + str(j)
                card, pred, pred_sel = ProblemLoader.get_join_ordering_problem(problem_path_prefix + '/synthetic/' + problem_path_main, generated_problems=True)
                
                if len(card) < 3 or 0.0 in pred_sel:
                    continue
                
                algorithm_path = result_path_prefix + '/' + problem_path_main
                #algorithm_result_files = os.listdir(path=algorithm_path)
                
                for algorithm in algorithm_list:
                    #algorithm = algorithm_result_file.split(".")[0]
                    #print(algorithm_path)
                    algorithm_results = load_data(algorithm_path, algorithm + ".json")
                   
                    if algorithm_results is None or "costs" not in algorithm_results.keys():
                        if algorithm == "milp":
                            print("MILP result missing")
                            print(problem_path_prefix + '/synthetic/' + problem_path_main)
                        csv_data_list.append([algorithm, relation, graph_type, j, 0, 'n/a', na_cost, 'n/a'])
                        continue
                       
                    costs = algorithm_results["costs"]
                    if costs == 0:
                        continue
                    if costs < baseline_cost:
                        baseline_cost = costs
                    
                    time_in_ms = 0
                    if "time_in_s" in algorithm_results.keys():
                        time_in_ms = algorithm_results["time_in_s"] * 1000
                        
                    csv_data_list.append([algorithm, relation, graph_type, j, 0, costs, 0, time_in_ms])
                    
                # Export csv data
                for csv_data in csv_data_list:
                    csv_data[4] = baseline_cost
                    if csv_data[len(csv_data)-3] != 'n/a' and int(baseline_cost) != 0:
                        normalised_cost = csv_data[len(csv_data)-3]/int(baseline_cost)
                        if normalised_cost > na_cost:
                            csv_data[len(csv_data)-2] = na_cost
                        else:
                            csv_data[len(csv_data)-2] = normalised_cost
                    else:
                        csv_data[len(csv_data)-2] = na_cost
                    save_to_csv(csv_data, output_path, 'results.txt')                    
                    
def export_synthetic_annealing_result_times(problem_path_prefix, result_path_prefix, output_path, na_cost=20, timeout_in_ms=60000, include_header=True):
    if include_header:
        csv_data = ['method', 'num_relations', 'graph_type', 'problem', 'baseline_cost', 'optimisation_time_in_ms', 'cost', 'normalised_cost']
        save_to_csv(csv_data, output_path, 'synthetic_result_times.txt')     
    
    graph_types = os.listdir(path=problem_path_prefix + '/synthetic_queries/')
    for graph_type_string in graph_types:
        graph_type = graph_type_string.split("_")[0]
        relations = os.listdir(path=problem_path_prefix + '/synthetic_queries/' + graph_type + '_graph')
        for relations_string in relations:
            i = int(relations_string.split("relations")[0])
            problems = os.listdir(path=problem_path_prefix + '/synthetic_queries/' + graph_type + '_graph/' + str(i) + 'relations')
            for j in problems:
                j = int(j)
                csv_data_list = []
                baseline_cost = inf

                problem_path_main = graph_type + '_graph/' + str(i) + 'relations/' + str(j)
                card, pred, pred_sel = ProblemLoader.get_join_ordering_problem(problem_path_prefix + '/synthetic_queries/' + problem_path_main, generated_problems=True)
                
                if len(card) < 3 or 0.0 in pred_sel:
                    continue
                
                algorithm_path = result_path_prefix + '/synthetic_queries/' + problem_path_main
                algorithm_result_files = os.listdir(path=algorithm_path)
                
                for algorithm_result_file in algorithm_result_files:
                    algorithm = algorithm_result_file.split(".")[0]
                    algorithm_results = load_data(algorithm_path, algorithm_result_file)
                    if len(algorithm_results) == 0:
                        csv_data_list.append([algorithm, i, graph_type, j, 0, 0, 'n/a', na_cost])
                        csv_data_list.append([algorithm, i, graph_type, j, 0, timeout_in_ms, 'n/a', na_cost])
                        continue
                    
                    csv_data_list.append([algorithm, i, graph_type, j, 0, 0, 'n/a', na_cost])
                    final_costs = na_cost
                    for algorithm_result in algorithm_results:
                        solution_time = algorithm_result["time"]
                        
                        # In some cases, MILP solution time is slightly above the timeout despite setting the timeout as desired.
                        # We take such cases into consideration by allowing a slight overhead time (1000ms) for MILP
                        if algorithm == 'milp' and solution_time > timeout_in_ms and solution_time <= (timeout_in_ms + 1000):
                            solution_time = timeout_in_ms
                        elif solution_time > timeout_in_ms:
                            continue
                            
                        join_order = algorithm_result["join_order"]
                        if not is_join_order_valid(join_order, len(card)):
                            return
                        costs = Postprocessing.get_costs_for_leftdeep_tree(join_order, card, pred, pred_sel, {})
                        final_costs = costs
                        #if "costs" in final_algorithm_result:
                            #costs = final_algorithm_result["costs"]
                        #elif "cost" in final_algorithm_result:
                            #costs = final_algorithm_result["cost"]

                        if costs < baseline_cost:
                            baseline_cost = costs
                        csv_data_list.append([algorithm, i, graph_type, j, 0, solution_time, costs, 0])
                        
                    csv_data_list.append([algorithm, i, graph_type, j, 0, timeout_in_ms, final_costs, 0])
                # Export csv data
                for csv_data in csv_data_list:
                    csv_data[4] = baseline_cost
                    if csv_data[len(csv_data)-2] != 'n/a' and baseline_cost != 0:
                        normalised_cost = csv_data[len(csv_data)-2]/baseline_cost
                        if normalised_cost > na_cost:
                            csv_data[len(csv_data)-1] = na_cost
                        else:
                            csv_data[len(csv_data)-1] = normalised_cost
                    else:
                        csv_data[len(csv_data)-1] = na_cost
                    save_to_csv(csv_data, output_path, 'synthetic_result_times.txt')
                    

