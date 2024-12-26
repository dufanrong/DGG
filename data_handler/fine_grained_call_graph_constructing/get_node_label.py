import os
import json
import csv

database = set()
Memcached = set()
blackhole = set()
relay = set()
normal = set()
source = set()
target = set()

base_path = "./sample_data/call_graph"

for service_folder in os.listdir(base_path):
    service_folder_path = os.path.join(base_path, service_folder)
    if os.path.isdir(service_folder_path):
        for json_file in os.listdir(service_folder_path):
            if json_file.endswith(".json"):
                json_path = os.path.join(service_folder_path, json_file)
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    for edge in data['edges']:
                        source_node = edge['source']
                        target_node = edge['target']
                        rpctype = edge['rpctype']
                        if '_' in target_node:
                            target_parts = target_node.split('_')
                            if len(target_parts) > 2:
                                target_node = '_'.join(target_parts[:2]) 
                        if '_' in source_node:
                            source_parts = source_node.split('_')
                            if len(source_parts) > 2:
                                source_node = '_'.join(source_parts[:2])
                        if rpctype == 'mc':
                            Memcached.add(target_node)
                        elif rpctype == 'db':
                            database.add(target_node)
                        else:
                            target.add(target_node)
                        if source_node != "USER":
                            source.add(source_node)
                                

print("Database nodes:", sorted(database))
print("Memcached nodes:", sorted(Memcached))
print("Target nodes num:", len(target))

target_not_in_source = sorted(target - source)
blackhole.update(target_not_in_source)
print("Blackhole nodes:", len(blackhole),sorted(blackhole))

normal = target - blackhole
print("Normal:",len(normal),sorted(normal))

fieldnames = ["msname", "label"]

with open("./sample_data/node_label.csv", "w", newline="") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    for label, elements in [("database", database), ("Memcached", Memcached), ("blackhole", blackhole), ("normal", normal)]:
        for msname in elements:
            writer.writerow({"msname": msname, "label": label})
