import numpy as np
import json
import time
import os
from sklearn.cluster import KMeans
from grakel import Graph
from grakel.kernels import SubgraphMatching
from grakel.kernels import EdgeHistogram
from grakel.kernels import NeighborhoodSubgraphPairwiseDistance
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

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

sk = SubgraphMatching(verbose=True,normalize=True)
nk = NeighborhoodSubgraphPairwiseDistance(normalize=True)
ek = EdgeHistogram(normalize=True)
print("SubgraphMatching start...")
start_time = time.time()
similarity_matrix = nk.fit_transform(Gs)
end_time = time.time()
elapsed_time = end_time - start_time
print("Time of SubgraphMatching:", elapsed_time, "seconds")
silhouette_scores = []
k_values = range(2, 20)

for k in k_values:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=1)
    labels = kmeans.fit_predict(similarity_matrix)
    
    num_labels = len(set(labels))
    silhouette_avg = silhouette_score(similarity_matrix, labels)
    silhouette_scores.append((k, silhouette_avg))

sorted_scores = sorted(silhouette_scores, key=lambda x: x[1], reverse=True)
print("Sorted silhouette scores in descending order:")