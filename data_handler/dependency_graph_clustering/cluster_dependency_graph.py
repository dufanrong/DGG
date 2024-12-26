import numpy as np
import json
import time
import os
import pandas as pd
from sklearn.cluster import KMeans
from grakel import Graph
from grakel.kernels import NeighborhoodSubgraphPairwiseDistance

def create_graph_from_json(json_file: str) -> Graph:
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    edges = [(edge["source"], edge["target"]) for edge in data["edges"]]
    edge_labels = {(edge["source"], edge["target"]): edge["rpctype"] for edge in data["edges"]}
    node_labels = {node["node"]: node["label"] for node in data["nodes"]}
    
    return Graph(edges, node_labels=node_labels, edge_labels=edge_labels, graph_format="adjacency")

input_path = "./sample_data/dependency_graph_with_label"

graph_data = []
for filename in os.listdir(input_path):
    if filename.endswith(".json"):
        service = os.path.splitext(filename)[0]
        json_file = os.path.join(input_path, filename)
        graph = create_graph_from_json(json_file)
        graph_data.append((service, graph))

Gs = [data[1] for data in graph_data]

nk = NeighborhoodSubgraphPairwiseDistance(normalize=True)
print("NeighborhoodSubgraphPairwiseDistance start...")
start_time = time.time()
similarity_matrix = nk.fit_transform(Gs)
end_time = time.time()
elapsed_time = end_time - start_time
print("Time of NeighborhoodSubgraphPairwiseDistance:", elapsed_time, "seconds")

# n_clusters is the k value with the highest contour coefficient in the decide_k.py result, in Alibaba dataset, this value is 6
kmeans = KMeans(n_clusters=6, random_state=42, n_init=10)
labels = kmeans.fit_predict(similarity_matrix)

service_names = [data[0] for data in graph_data]
cluster_info = pd.DataFrame({'service': service_names, 'label': labels})

service_info_path = "./sample_data/service_info.csv"
service_info = pd.read_csv(service_info_path)

merged_info = pd.merge(service_info, cluster_info, on='service', how='left')

merged_info.to_csv(service_info_path, index=False)