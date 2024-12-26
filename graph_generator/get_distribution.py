from collections import defaultdict, deque
import os
import json
import csv

class MicroService:
    def __init__(self, name, label, interface="", time=1, comPara=""):
        self.name = name
        self.label = label
        self.interface = interface
        self.time = time
        self.comPara = comPara

    def __eq__(self, other):
        if isinstance(other, MicroService):
            return (self.name == other.name and
                    self.label == other.label and
                    self.interface == other.interface and
                    self.time == other.time and
                    self.comPara == other.comPara)
        return False

    def __hash__(self):
        return hash((self.name, self.label, self.interface, self.time, self.comPara))

def add_depth_to_edges_in_json(json_file_path):
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    node_depths = {"USER": 1}
    queue = deque([(edge["source"], 1) for edge in data["edges"] if edge["source"] == "USER"])
    while queue:
        source, depth = queue.popleft()
        edges_with_source = [edge for edge in data["edges"] if edge["source"] == source]
        for edge in edges_with_source:
            target = edge["target"]
            if target not in node_depths:
                node_depths[target] = depth + 1
                queue.append((target, depth + 1))
    for edge in data["edges"]:
        edge["depth"] = node_depths[edge["source"]]
    
    return data

def create_microservice(node, depth, target_edge, nodes):
    target_name = target_edge["target"]
    target_label = next(item["label"] for item in nodes if item["node"] == target_name)
    interface = target_name.split('_', 2)[-1] if target_name.count('_') >= 2 else ""
    time = target_edge["weight"]
    comPara = target_edge["rpctype"]
    return MicroService(target_name, target_label, interface, time, comPara)

def construct_target_dict(json_data_list):
    target_dict = defaultdict(list)  # Use defaultdict with list as default_factory
    node_label_dict = {}

    for json_data in json_data_list:
        edges = json_data["edges"]
        nodes = json_data["nodes"]
        
        temp_dict = defaultdict(lambda: {'targets': set(), 'brothers': set()})  # Temporary defaultdict to store targets and brothers
        parent_dict = defaultdict(list)  # Dictionary to store parent-child relationships
        
        for node_entry in nodes:
            node_label_dict[node_entry["node"]] = node_entry["label"]

        # Build parent-child relationships
        for edge in edges:
            parent_dict[edge["source"]].append(edge["target"])

        for node_entry in nodes:
            if node_entry["label"] in ["relay", "normal"]:
                node_name = node_entry["node"]
                found_source_match = False  # Flag to indicate if a matching source edge is found
                for edge in edges:
                    if edge["source"] == node_name:
                        depth = edge["depth"]
                        target_microservice = create_microservice(node_name, depth, edge, nodes)
                        temp_dict[(node_name, depth)]['targets'].add(target_microservice)
                        found_source_match = True  # Update the flag if a match is found
                
                # If no edge["source"] == node_name data found, check edge["target"] == node_name
                if not found_source_match:
                    for edge in edges:
                        if edge["target"] == node_name:
                            depth = edge["depth"] + 1
                            temp_dict[(node_name, depth)]['targets'] = set()  # Ensure the set is initialized
                            break

        # Add brother nodes
        for key in temp_dict.keys():
            node_name, depth = key
            for edge in edges:
                if edge["target"] == node_name:
                    parent_node = edge["source"]
                    brother_nodes = parent_dict[parent_node]
                    brothers = set()
                    for brother_node in brother_nodes:
                        if brother_node != node_name:
                            brothers.add(brother_node)
                    if brothers:
                        temp_dict[key]['brothers'].add(frozenset(brothers))  # Use frozenset to store unique combinations of brothers
                    break

        # Update target_dict with temp_dict
        for key, value in temp_dict.items():
            node_name, depth = key
            sorted_targets = sorted(value['targets'], key=lambda ms: ms.name)  # Sort Microservices by node_name
            sorted_brothers_sets = {frozenset(brother_set) for brother_set in value['brothers']}  # Store unique combinations of brothers
            target_list = target_dict[key]
            existing_index = None
            for i, (existing_targets, existing_brothers_sets, num) in enumerate(target_list):
                if existing_targets == sorted_targets:
                    existing_index = i
                    break
            if existing_index is not None:
                # Update existing tuple
                existing_targets, existing_brothers_sets, num = target_list[existing_index]
                combined_brothers_sets = existing_brothers_sets | sorted_brothers_sets  # Merge brother sets
                target_list[existing_index] = (existing_targets, combined_brothers_sets, num + json_data["num"])
            else:
                # Add new tuple
                target_list.append((sorted_targets, sorted_brothers_sets, json_data["num"]))

    return target_dict, node_label_dict

def check_brothers_influence(target_list):
    """
    Check if the brothers of targets are different and return a message indicating the influence.
    """
    # print("target list",target_list)
    if len(target_list) <= 1:
        return False
    
    brother_sets = [brothers for _, brothers, _ in target_list]
    
    # Compare all brother sets with each other
    for i in range(len(brother_sets)):
        for j in range(i + 1, len(brother_sets)):
            if brother_sets[i] != brother_sets[j]:
                return True
    
    return False

def print_target_dict(target_dict):
    """
    Print the contents of the target dictionary.

    Args:
    - target_dict (dict): The target dictionary to be printed.
    """
    for key, value_list in target_dict.items():
        node, depth = key
        # if depth > 2:  # Only consider nodes with depth > 2
        print(f"Node: {node}, Depth: {depth}")
    
        for targets, brothers_sets, num in value_list:
            # if targets and brothers_sets:  # Only consider nodes with non-empty targets and brothers
            
            print(f"  Targets:")
            for ms in targets:
                print(f"    {ms.name}, Label: {ms.label}, Interface: {ms.interface}, Time: {ms.time}, ComPara: {ms.comPara}")
            print(f"  Brothers:")
            for brothers in brothers_sets:
                brother_names = ", ".join(brothers)
                print(f"    {brother_names}")
            print(f"  Num: {num}")
        # Check and print influence
        influence = check_brothers_influence(value_list)
        influence_message = "Influence detected" if influence else "No influence"
        print(f"  Influence: {influence_message}")

def print_target_set(target_set):
    """
    Print the contents of the target set.

    Args:
    - target_set (set): The set of MicroService instances to be printed.
    """
    for ms in target_set:
        print(f"Name: {ms.name}, Label: {ms.label}, Interface: {ms.interface}, Time: {ms.time}, ComPara: {ms.comPara}")

def get_json_file_paths(directory):
    json_files = []
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            json_files.append(os.path.join(directory, filename))
    return json_files

def read_all_json_data(directory):
    json_files = get_json_file_paths(directory)
    json_data_list = []
    for json_file in json_files:
        json_data_list.append(add_depth_to_edges_in_json(json_file))
    return json_data_list

def construct_target_dict_from_directory(directory):
    json_data_list = read_all_json_data(directory)
    return construct_target_dict(json_data_list)


def analyze_services(directory, output_csv):
    results = []
    
    # Traverse all subdirectories (types) in the given directory
    for type_dir in os.listdir(directory):
        type_path = os.path.join(directory, type_dir)
        if os.path.isdir(type_path):
            # Traverse all subdirectories (services) in the type directory
            for service in os.listdir(type_path):
                service_path = os.path.join(type_path, service)
                if os.path.isdir(service_path):
                    # Construct target dictionary for the service
                    target_dict, _ = construct_target_dict_from_directory(service_path)
                    
                    # Check for nodes with depth > 2 and non-empty targets
                    for key, value_list in target_dict.items():
                        node, depth = key
                        if depth > 2:
                            for targets, brothers_sets, num in value_list:
                                if targets:
                                    influence = check_brothers_influence(value_list)
                                    influence_message = "Yes" if influence else "No"
                                    results.append((service, node, depth, influence_message))
    
    # Write results to CSV file
    with open(output_csv, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['service', 'ms', 'depth', 'brothers_influence'])
        csvwriter.writerows(results)
