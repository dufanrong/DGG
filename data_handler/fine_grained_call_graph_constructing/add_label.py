import os
import json
import csv

node_info_path = "./sample_data/node_label.csv"
input_cg_path = './sample_data/call_graph'
output_cg_path = "./sample_data/call_graph_with_label"
input_dg_path = './sample_data/dependency_graph'
output_dg_path = "./sample_data/dependency_graph_with_label"

if not os.path.exists(output_cg_path):
    os.makedirs(output_cg_path)

if not os.path.exists(output_dg_path):
    os.makedirs(output_dg_path)

node_label = {}

with open(node_info_path, "r", newline="") as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        msname = row["msname"]
        label = row["label"]
        node_label[msname] = label

node_label["USER"] = "relay"

# add label to call graphs
for service_folder in os.listdir(input_cg_path):
    service_path = os.path.join(input_cg_path, service_folder)
    output_base_path = os.path.join(output_cg_path, service_folder)
    if not os.path.exists(output_base_path):
        os.makedirs(output_base_path)
    for root, dirs, files in os.walk(service_path):
        for file_name in files:
            json_path = os.path.join(root, file_name)
            output_json_path = os.path.join(output_base_path, file_name)

            with open(json_path, "r") as json_file:
                data = json.load(json_file)

                nodes = data.get("nodes", [])
                new_nodes = []
                for node in nodes:
                    if '_' in node:
                        parts = node.split('_')
                        if len(parts) > 2:
                            new_node = '_'.join(parts[:2])
                            label = node_label.get(new_node, "")
                        else:
                            label = node_label.get(node, "")
                    else:
                        label = node_label.get(node, "")

                    new_nodes.append({"node": node, "label": label})

                data["nodes"] = new_nodes
                if 'traceids' in data:
                    del data['traceids']

                with open(output_json_path, "w") as output_file:
                    json.dump(data, output_file, indent=4)

# add label to dependency graphs
for file_name in os.listdir(input_dg_path):
    if file_name.endswith(".json"):
        json_path = os.path.join(input_dg_path, file_name)
        output_json_path = os.path.join(output_dg_path, file_name)

        with open(json_path, "r") as json_file:
            data = json.load(json_file)

            nodes = data.get("nodes", [])
            new_nodes = []
            for node in nodes:
                if '_' in node:
                    parts = node.split('_')
                    if len(parts) > 2:
                        new_node = '_'.join(parts[:2]) 
                        label = node_label.get(new_node, "")
                    else:
                        label = node_label.get(node, "")
                else:
                    label = node_label.get(node, "")

                new_nodes.append({"node": node, "label": label})

            data["nodes"] = new_nodes

            with open(output_json_path, "w") as output_file:
                json.dump(data, output_file, indent=4)

