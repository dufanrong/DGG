from get_distribution import construct_target_dict_from_directory, print_target_dict,MicroService, print_target_set
from filter import process_types
import random
import string
import numpy as np
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
import copy
import csv
import time

class Node:
    def __init__(self, rpcid, um, dm, compara, time=1):
        self.rpcid = rpcid
        self.um = um
        self.dm = dm
        self.compara = compara
        self.time = time

    def to_dict(self):
        return {
            "rpcid": self.rpcid,
            "um": self.um,
            "dm": self.dm,
            "time": self.time,
            "compara": self.compara
        }

class GraphGenerator:
    def __init__(self, service_type_directory, callgraph_directory, brother_influence_alpha = 0.5, service_types=None):
        self.service_type_directory = service_type_directory
        self.callgraph_directory = callgraph_directory
        self.brother_influence_alpha = brother_influence_alpha
        self.service_types = service_types if service_types else [0, 1, 2, 3, 4, 5]
        self.service_type_info = {} 
        self.service_targets = {} 
        self.service_prob = {} 
        self.ms_label = {service_type: {} for service_type in self.service_types}
        self.graph_num = {}
        self.cur_svc = None 
        self.call_graph_path = None
        self.service_ms_influence = {} 
        self._initialize_service_type_info()

        start_time = time.time()
        self._initialize_service_targets()
        end_time = time.time()
        initialize_model_time = end_time - start_time
        print("Initializa model time:",initialize_model_time)

    def _initialize_service_type_info(self):
        df = pd.read_csv(self.service_type_directory)

        self.service_prob = {}
        self.service_type_info = {}

        total_top90_trace_num_all = df['top90_trace_num'].sum()

        grouped = df.groupby('label')

        for label, group_df in grouped:
            if label not in self.service_types:
                continue

            total_top90_trace_num_group = group_df['top90_trace_num'].sum()

            group_ratio = total_top90_trace_num_group / total_top90_trace_num_all

            service_prob_list = []

            for index, row in group_df.iterrows():

                service_prob = row['top90_trace_num'] / total_top90_trace_num_group
                service_prob_list.append((row['service'], service_prob))

            self.service_prob[label] = service_prob_list

            self.service_type_info[label] = group_ratio

    def _initialize_service_targets(self):
        for label, service_prob_list in self.service_prob.items():
            callgraph_path = os.path.join(self.callgraph_directory, f"type{label}")
            for service, _ in service_prob_list:
                service_directory = os.path.join(callgraph_path, service)
                self.service_targets[service], label_dict = construct_target_dict_from_directory(service_directory)
                if not self.ms_label[label]:
                    self.ms_label[label] = label_dict.copy()
                else:
                    for key, value in label_dict.items():
                        self.ms_label[label][key] = value

    def calculate_depth(self, rpcid):
        depth = rpcid.count('.') + 2
        return depth

    def is_relay(self, msname, depth):
        if self.cur_svc is None:
            raise ValueError("Current type is not set.")

        key = (msname, depth)
        if key not in self.service_targets[self.cur_svc]:
            return False
        
        target_list = self.service_targets[self.cur_svc][key]
        if not target_list:
            return False

        target_list_copy = copy.deepcopy(target_list)
        
        total_weight = sum(num for _, _, num in target_list_copy)
        if not total_weight:
            return False
        
        selected_weight = random.randint(1, total_weight)
        
        cumulative_weight = 0
        for targets, _, num in target_list_copy:
            cumulative_weight += num
            if targets and cumulative_weight >= selected_weight:
                return True
        
        return False

    def get_target(self, msname, depth):
        if self.cur_svc is None:
            raise ValueError("Current type is not set.")

        key = (msname, depth)
        if key not in self.service_targets[self.cur_svc]:
            return set()
        
        target_list = self.service_targets[self.cur_svc][key]
        if not target_list:
            return set()

        target_list_copy = copy.deepcopy(target_list)
        
        non_empty_targets = [(targets, num) for targets, _, num in target_list_copy if targets]
        # print(non_empty_targets)
        total_weight = sum(num for _, num in non_empty_targets)
        if not total_weight:
            return set()
        
        selected_weight = random.randint(1, total_weight)
        
        cumulative_weight = 0
        for targets, num in non_empty_targets:
            cumulative_weight += num
            if cumulative_weight >= selected_weight:
                return targets
        
        return set()

    def get_target_with_brother_influence(self, um, depth, brothers):
        if self.cur_svc is None:
            raise ValueError("Current type is not set.")

        key = (um, depth)
        if key not in self.service_targets[self.cur_svc]:
            return set()
        
        target_list = self.service_targets[self.cur_svc][key]
        if not target_list:
            return set()

        target_list_copy = copy.deepcopy(target_list)
        brothers_set = set(brothers)
        
        non_empty_targets = [
            (targets, num) for targets, brothers_sets, num in target_list_copy
            if targets and any(brothers_set == brothers_set_item for brothers_set_item in brothers_sets)
        ]

        if not non_empty_targets:
            return set()
        
        total_weight = sum(num for _, num in non_empty_targets)
        if not total_weight:
            return set()
        
        selected_weight = random.randint(1, total_weight)
        
        cumulative_weight = 0
        for targets, num in non_empty_targets:
            cumulative_weight += num
            if cumulative_weight >= selected_weight:
                return targets
        
        return set()

    def generate_callgraph(self):
        node_list = []
        brother_influence_dict = {}
        targets = self.get_target("USER", 1)
        if targets:
            target = targets.pop()
            dm = target.name
            compara = target.comPara
            user = Node('0', "USER", dm, compara, 1)
            node_list = [user]
            queue = [user]

            while queue:
                current_node = queue.pop(0)
                rpcid, um = current_node.rpcid, current_node.dm
                depth = self.calculate_depth(rpcid)
                
                if self.is_relay(um, depth):
                    # if (um, depth) in brother_influence_dict and random.random() < self.brother_influence_alpha:
                    if (um, depth) in brother_influence_dict:
                        brothers = brother_influence_dict[(um, depth)]
                        targets = self.get_target_with_brother_influence(um, depth, brothers)
                    else:
                        targets = self.get_target(um, depth)

                    brother_influenced_ms = None

                    for target in targets:
                        ms = target.name
                        if self.service_ms_influence.get((self.cur_svc, ms, depth + 1), False):
                            brother_influenced_ms = ms
                            break
                    
                    if brother_influenced_ms:
                        brother_names = [target.name for target in targets if target.name != brother_influenced_ms]
                        brother_influence_dict[(brother_influenced_ms, depth + 1)] = brother_names
                    
                    for i, target in enumerate(targets):
                        compara = target.comPara
                        rpcidChild = f"{rpcid}.{i+1}"
                        dm = target.name
                        time = target.time
                        new_node = Node(rpcidChild, um, dm, compara, time)
                        node_list.append(new_node)
                        queue.append(new_node)

        return node_list

    def save_node_list_to_json(self, node_list, output_file):
        data = {"edges": []}
        for node in node_list:
            node_data = {
                "rpcid": node.rpcid,
                "um": node.um,
                "dm": node.dm,
                "time": node.time,
                "compara": node.compara
            }
            data["edges"].append(node_data)

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=4)

    def generate_and_save_unique_graphs(self, n, output_folder):
        output_folder = os.path.join(output_folder, datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(output_folder, exist_ok=True)
        self.call_graph_path = output_folder

        type_counts = self._calculate_type_counts(n)

        total_time_for_loop = 0
        total_time_generate_callgraph = 0

        for service_type, count in type_counts.items():

            unique_graphs = {}
            start_time_for_loop = time.time()
            for i in range(count):
                selected_service = random.choices([service for service, _ in self.service_prob[service_type]], 
                                              weights=[prob for _, prob in self.service_prob[service_type]])[0]

                self.cur_svc = selected_service
                # print(service_type, self.cur_svc)

                start_time_generate_callgraph = time.time()
                graph = self.generate_callgraph()  
                end_time_generate_callgraph = time.time()

                total_time_generate_callgraph += (end_time_generate_callgraph - start_time_generate_callgraph)

                graph_str = json.dumps([node.to_dict() for node in graph], sort_keys=True, default=str)
                graph_hash = hashlib.sha256(graph_str.encode()).hexdigest()
                if graph_hash not in unique_graphs:
                    unique_graphs[graph_hash] = {'graph': graph, 'count': 1}  
                else:
                    unique_graphs[graph_hash]['count'] += 1  

            
            end_time_for_loop = time.time()
            
            total_time_for_loop += (end_time_for_loop - start_time_for_loop)

            sorted_graphs = sorted(unique_graphs.items(), key=lambda x: x[1]['count'], reverse=True)
            output_path = os.path.join(output_folder, f"type{service_type}")
            os.makedirs(output_path, exist_ok=True)
            for idx, (graph_hash, info) in enumerate(sorted_graphs, start=1):
                output_file = os.path.join(output_path,f"graph{idx}.json")
                node_labels = {}
                for node in info['graph']:
                    um = node.um  # Accessing um attribute of Node object
                    node_labels[um] = self.ms_label[service_type].get(um, None)
                    dm = node.dm  # Accessing um attribute of Node object
                    node_labels[dm] = self.ms_label[service_type].get(dm, None)
                nodes_data = [{"node": node, "label": label} for node, label in node_labels.items()]
                graph_data = {
                    "nodes": nodes_data,
                    "edges": [node.to_dict() for node in info['graph']],
                    "num": info['count']
                }
                with open(output_file, 'w') as f:
                    json.dump(graph_data, f, indent=4)

            self.graph_num[service_type] = len(unique_graphs)

        average_time_for_loop = total_time_for_loop / n
        average_time_generate_callgraph = total_time_generate_callgraph / n

        print(f"Average time for generate_callgraph: {average_time_generate_callgraph} seconds")

        
    def _calculate_type_counts(self, n):
        type_counts = {}
        for service_type in self.service_types:
            probability = self.service_type_info[service_type]
            type_counts[service_type] = round(n * probability)
        return type_counts

    def print_generated_cg_num(self):
        print("Generated Graph Num:")
        for service_type, num in self.graph_num.items():
            service_type_key = f"type{service_type}"
            print(f"{service_type_key}: {num}")

    
    def filter_low_frequency_graphs(self):
        print("Filtered Graph Num:")
        process_types(self.call_graph_path, self.service_types)

service_type_directory = './sample_data/service_info.csv'
callgraph_directory = './sample_data/real_call_graph_renamed'

graph_gen = GraphGenerator(service_type_directory, callgraph_directory)
graph_gen.generate_and_save_unique_graphs(n=10000,output_folder='./sample_data/DGG_gen_cgs')

graph_gen.print_generated_cg_num()

graph_gen.filter_low_frequency_graphs()