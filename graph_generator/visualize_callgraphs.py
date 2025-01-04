import json
import pygraphviz as pgv
import os

def visualize_gen_tree(json_file_path):
    with open(json_file_path, 'r') as f:
        data = json.load(f)

    G = pgv.AGraph(strict=True, directed=True)

    for edge in data["edges"]:
        G.add_edge(edge["um"], edge["dm"], label=str(edge["time"]))

    G.graph_attr.update(layout='dot') 

    return G

def visualize_gen_tree_from_folder(folder_path, output_path, service_types):
    for service_type in service_types:
        type_folder = f'type{service_type}'
        type_folder_path = os.path.join(folder_path, type_folder)
        output_folder = os.path.join(output_path, type_folder)
        os.makedirs(output_folder, exist_ok=True)
        for file_name in os.listdir(type_folder_path):
            if file_name.endswith('.json'):
                file_path = os.path.join(type_folder_path, file_name)

                G = visualize_gen_tree(file_path)

                output_file_path = os.path.join(output_folder, file_name.replace('.json', '.pdf'))
                G.draw(output_file_path, format='pdf', prog='dot')


callgraph_path = "./sample_data/DGG_gen_cgs/20241226_102814"
output_path = "./sample_data/visualize"
os.makedirs(output_path, exist_ok=True)
service_types = [0, 1, 2, 3, 4, 5]
visualize_gen_tree_from_folder(callgraph_path, output_path, service_types)