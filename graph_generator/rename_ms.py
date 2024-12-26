import json
import os
import pandas as pd
from collections import deque
from collections import defaultdict
import time
import csv

global new_name, new_func
new_func = {}
new_name = {}

class WeightedGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = defaultdict(dict)

    def add_node(self, node, label, num):
        key = (node, label)
        if key in self.nodes:
            self.nodes[key] += num
        else:
            self.nodes[key] = num

    def add_edge(self, source, target, weight, rpctype):
        if (source, target) in self.edges and self.edges[(source, target)]['rpctype'] == rpctype:
            self.edges[(source, target)]['weight'] = max(self.edges[(source, target)]['weight'], weight)
        else:
            self.edges[(source, target)] = {'weight': weight, 'rpctype': rpctype}

input_dir = "./sample_data/real_call_graph"
cg_num_path = "./sample_data/service_info.csv" 
output_path = "./sample_data/dependency_graph_with_node_num" 

cg_num = {}
with open(cg_num_path, 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        cg_num[row['service']] = int(row['cg_num'])

for subdir in os.listdir(input_dir):
    subdir_path = os.path.join(input_dir, subdir)
    output_dir = os.path.join(output_path, subdir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if os.path.isdir(subdir_path):
        for service_folder in os.listdir(subdir_path):
            service_folder_path = os.path.join(subdir_path, service_folder)
            if os.path.isdir(service_folder_path):
                merged_graph = WeightedGraph()

                num_of_cg = cg_num.get(service_folder, 0)

                for i in range(1, num_of_cg + 1):
                    file_path = os.path.join(service_folder_path, f"graph{i}.json")
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as file:
                            nodes = data.get("nodes", [])
                            edges = data.get("edges", [])
                            num = data.get("num")

                            for node in nodes:
                                merged_graph.add_node(node['node'], node['label'], num)

                            for edge in edges:
                                source = edge.get("source")
                                target = edge.get("target")
                                weight = edge.get("weight")
                                rpctype = edge.get("rpctype")
                                merged_graph.add_edge(source, target, weight, rpctype)

                output_file_path = os.path.join(output_dir, f"{service_folder}.json")
                os.makedirs(output_dir, exist_ok=True)

                with open(output_file_path, 'w') as json_file:
                    json.dump({
                        'nodes': [{'node': node, 'label': label, 'num': num} for (node, label), num in merged_graph.nodes.items()],
                        'edges': [{'source': source, 'target': target, 'weight': data['weight'], 'rpctype': data['rpctype']} 
                                for (source, target), data in merged_graph.edges.items()]
                    }, json_file, indent=2)


def add_depth_to_edges_in_json(json_file_path):
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    node_depths = {}
    target_depths = {}
    node_num = {} 
    node_label = {} 
    func_num = {} 
    local_new_name = {} 
    local_new_func = {} 

    for node_info in data["nodes"]:
        if node_info["node"] != "USER":
            target = node_info["node"]
            num = node_info["num"]
            node_name_parts = target.split('_')
            if len(node_name_parts) > 2:
                nodename = '_'.join(node_name_parts[:2])
                oldfunc = '_'.join(node_name_parts[2:])
                if oldfunc in new_func:
                    local_new_func[oldfunc] = new_func[oldfunc]
                else:
                    if oldfunc in func_num:
                        func_num[oldfunc] += num
                    else:
                        func_num[oldfunc] = num
            else:
                nodename = target

            if nodename in new_name:
                local_new_name[nodename] = new_name[nodename]
            else:
                if nodename in node_num:
                    node_num[nodename] += num
                else:
                    node_num[nodename] = num

                node_label[nodename] = node_info["label"]

    queue = deque([(edge["source"], 1) for edge in data["edges"] if edge["source"] == "USER"])
    while queue:
        source, depth = queue.popleft()
        edges_with_source = [edge for edge in data["edges"] if edge["source"] == source]
        for edge in edges_with_source:
            target = edge["target"]
            node_name_parts = target.split('_')
            if len(node_name_parts) > 2:
                nodename = '_'.join(node_name_parts[:2])
            else:
                nodename = target
            if nodename not in new_name:
                if nodename not in node_depths:
                    node_depths[nodename] = depth + 1
            if target not in target_depths:
                target_depths[target] = depth + 1
                queue.append((target, depth + 1))

    return node_depths, node_num, node_label, func_num, local_new_name, local_new_func

def calculate_node_and_func_idx(node_depths, node_num, node_label, func_num, local_new_name, local_new_func):
    grouped_nodes = {} 

    used_indices = {}
    for idx in local_new_name.values():
        idx_parts = idx.split('.')
        node_idx_val = int(idx_parts[-1])
        
        label_parts = idx_parts[0].split('_')[1].split('+')
        label = label_parts[0]

        if len(label_parts) > 1:
            depth = int(label_parts[1])
        else:
            depth = 0

        key = (label, depth) if label in ['normal', 'relay'] else (label,)
        
        if key not in used_indices:
            used_indices[key] = set()
        used_indices[key].add(node_idx_val)

    for node, depth in node_depths.items():
        label = node_label[node]
        if label == 'normal' or label == 'relay':
            key = (label, depth)
        else:
            key = (label,) 

        if key not in grouped_nodes:
            grouped_nodes[key] = []
        grouped_nodes[key].append(node)

    new_node_idx = {}
    for key, nodes in grouped_nodes.items():
        if key not in used_indices:
            used_indices[key] = set()
        sorted_nodes = sorted(nodes, key=lambda x: node_num[x], reverse=True)
        idx = 1
        for node in sorted_nodes:
            while idx in used_indices[key]:
                idx += 1
            new_node_idx[node] = idx
            idx += 1

    used_indices = set()
    for idx in local_new_func.values():
        func_idx = int(idx[4:])
        used_indices.add(func_idx)

    sorted_funcs = sorted(func_num.keys(), key=lambda x: func_num[x], reverse=True)
    func_idx = {}
    idx = 1
    for func in sorted_funcs:
        while idx in used_indices:
            idx += 1
        func_idx[func] = idx
        idx += 1

    return new_node_idx, func_idx

def update_json(json_file_path, cg_file_path, output_folder):

    with open(json_file_path, 'r') as f:
        data = json.load(f)

    node_depths, node_num, node_label, func_num, local_new_name, local_new_func = add_depth_to_edges_in_json(json_file_path)
    node_idx, func_idx = calculate_node_and_func_idx(node_depths, node_num, node_label, func_num, local_new_name, local_new_func)

    for func, idx in func_idx.items():
        new_func[func] = f"func{idx}"
        local_new_func[func] = f"func{idx}"

    for node, depth in node_depths.items():
        if node in node_num and node in node_label and node in node_idx :
            # print(node)
            label = node_label[node]
            if label == 'normal' or label == 'relay':
                local_new_name[node] = f"MS_{node_label[node]}+{node_depths[node]}.{node_idx[node]}"
            else:
                local_new_name[node] = f"MS_{node_label[node]}.{node_idx[node]}"
            new_name[node] = local_new_name[node]

    for file_name in os.listdir(cg_file_path):

        cg_json_file_path = os.path.join(cg_file_path, file_name)

        if os.path.isfile(cg_json_file_path):

            with open(cg_json_file_path, 'r') as cg_file:
                cg_data = json.load(cg_file)

            for node_entry in cg_data["nodes"]:
                if node_entry["node"] != "USER":
                    original_node_name = node_entry["node"]
                    node_name_parts = original_node_name.split('_')
                    if len(node_name_parts) > 2:
                        base_node_name = '_'.join(node_name_parts[:2])
                        oldfunc = '_'.join(node_name_parts[2:])
                        
                        if base_node_name in local_new_name:
                            new_base_node_name = local_new_name[base_node_name]
                            newfunc = local_new_func[oldfunc]
                            new_node_name = f"{new_base_node_name}_{newfunc}"
                            node_entry["node"] = new_node_name
                    elif original_node_name in local_new_name:
                        node_entry["node"] = local_new_name[original_node_name]

            # Update target and source in edges
            for edge in cg_data["edges"]:
                source = edge["source"]
                target = edge["target"]
                source_parts = source.split('_')
                target_parts = target.split('_')
                
                # Replace source
                if len(source_parts) > 2:
                    base_source_name = '_'.join(source_parts[:2])
                    source_interface = '_'.join(source_parts[2:])
                    if base_source_name in local_new_name:
                        new_base_source_name = local_new_name[base_source_name]
                        new_source_name = f"{new_base_source_name}_{local_new_func[source_interface]}"
                        edge["source"] = new_source_name
                elif source in local_new_name:
                    edge["source"] = local_new_name[source]
                    
                # Replace target
                if len(target_parts) > 2:
                    base_target_name = '_'.join(target_parts[:2])
                    target_interface = '_'.join(target_parts[2:])
                    if base_target_name in local_new_name:
                        new_base_target_name = local_new_name[base_target_name]
                        new_target_name = f"{new_base_target_name}_{local_new_func[target_interface]}"
                        edge["target"] = new_target_name
                elif target in local_new_name:
                    edge["target"] = local_new_name[target]

            output_json_file_path = os.path.join(output_folder, file_name)
            with open(output_json_file_path, 'w') as cg_file:
                json.dump(cg_data, cg_file, indent=4)

def update_all_files(service_path, cg_path, output_path, service_list):

    for service_name in service_list:

        cg_file_path = os.path.join(cg_path, service_name)

        file_path = os.path.join(service_path, f"{service_name}.json")
        output_folder = os.path.join(output_path, service_name)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        if os.path.isfile(file_path):
            update_json(file_path, cg_file_path, output_folder)


type_range = range(6)
csv_path = './sample_data/service_info.csv'

df = pd.read_csv(csv_path)
grouped = df.groupby('label')

for type_num in type_range:

    service_type = f'type{type_num}'
    service_path = f'./sample_data/dependency_graph_with_node_num/{service_type}'
    cg_path = f'./sample_data/real_call_graph/{service_type}'
    output_path = f'./sample_data/real_call_graph_renamed/{service_type}'

    if type_num in grouped.groups:
        service_list = grouped.get_group(type_num)
        service_list = service_list.sort_values(by='top90_trace_num', ascending=False)
        service_list = service_list['service'].tolist()
    else:
        service_list = []

    update_all_files(service_path, cg_path, output_path, service_list)