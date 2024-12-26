import os
import json
from collections import defaultdict
import time

class WeightedGraph:
    def __init__(self):
        self.nodes = set()
        self.edges = defaultdict(dict)

    def add_node(self, node):
        self.nodes.add(node)

    def add_edge(self, source, target, weight, rpctype):
        if (source, target) in self.edges and self.edges[(source, target)]['rpctype'] == rpctype:
            self.edges[(source, target)]['weight'] = max(self.edges[(source, target)]['weight'], weight)
        else:
            self.nodes.add(source)
            self.nodes.add(target)
            self.edges[(source, target)] = {'weight': weight, 'rpctype': rpctype}


input_dir = "./sample_data/call_graph"
output_dir = "./sample_data/dependency_graph"

start_time = time.time()

for service_folder in os.listdir(input_dir):
    service_folder_path = os.path.join(input_dir, service_folder)
    if os.path.isdir(service_folder_path):
        merged_graph = WeightedGraph()

        for file_name in os.listdir(service_folder_path):
            if file_name.endswith('.json'):
                file_path = os.path.join(service_folder_path, file_name)
                with open(file_path, 'r') as file:
                    data = json.load(file)

                    nodes = data.get("nodes", [])
                    edges = data.get("edges", [])

                    for node in nodes:
                        merged_graph.add_node(node)

                    for edge in edges:
                        source = edge.get("source")
                        target = edge.get("target")
                        weight = edge.get("weight")
                        rpctype = edge.get("rpctype")
                        merged_graph.add_edge(source, target, weight, rpctype)

        merged_graph.nodes = sorted(merged_graph.nodes)
        merged_graph.edges = dict(sorted(merged_graph.edges.items()))

        output_file_path = os.path.join(output_dir, f"{service_folder}.json")
        os.makedirs(output_dir, exist_ok=True)

        with open(output_file_path, 'w') as json_file:
            json.dump({
                'nodes': list(merged_graph.nodes),
                'edges': [{'source': source, 'target': target, 'weight': data['weight'], 'rpctype': data['rpctype']} 
                            for (source, target), data in merged_graph.edges.items()]
            }, json_file, indent=2)

end_time = time.time()
processing_time = end_time - start_time
print("Total processing time:", processing_time, "seconds")