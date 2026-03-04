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
import Scripts.HybridUtil as HybridUtil

import json
import os
import pathlib
import csv
from os import listdir
from os.path import isfile, join
from pathlib import Path
                

if __name__ == "__main__":
    
    raw_problem_path = 'Experiments/Raw_Problems/TREE_graph'
    problem_path_prefix = 'Experiments/Problems'
    threshold_path_prefix = 'Experiments/Thresholds'
    raw_result_path_prefix = 'Experiments/Raw_Results'
    result_path_prefix = 'Experiments/Results/synthetic'
    subproblem_solutionpath = 'Adaptive/queries/output/subproblems'
    graph_types = ['TREE']
    relations = [20, 30, 40, 50, 60, 70, 80, 90, 100]
    problems = np.arange(100).tolist()
    
    time_limit = 60
    
    max_depth = 4
    num_right_leaf_predecessors = 10
    HybridUtil.derive_total_solutions(graph_types, relations, problems, max_depth, num_right_leaf_predecessors, time_limit, raw_problem_path, problem_path_prefix, raw_result_path_prefix, result_path_prefix, subproblem_solutionpath)

    max_depth = 5
    num_right_leaf_predecessors = 10
    HybridUtil.derive_total_solutions(graph_types, relations, problems, max_depth, num_right_leaf_predecessors, time_limit, raw_problem_path, problem_path_prefix, raw_result_path_prefix, result_path_prefix, subproblem_solutionpath)

    max_depth = 6
    num_right_leaf_predecessors = 10
    HybridUtil.derive_total_solutions(graph_types, relations, problems, max_depth, num_right_leaf_predecessors, time_limit, raw_problem_path, problem_path_prefix, raw_result_path_prefix, result_path_prefix, subproblem_solutionpath)

    max_depth = 7
    num_right_leaf_predecessors = 10
    HybridUtil.derive_total_solutions(graph_types, relations, problems, max_depth, num_right_leaf_predecessors, time_limit, raw_problem_path, problem_path_prefix, raw_result_path_prefix, result_path_prefix, subproblem_solutionpath)
