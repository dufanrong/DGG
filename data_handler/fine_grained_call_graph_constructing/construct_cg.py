import csv
from collections import defaultdict
import pandas as pd
import os
import json
import time

class WeightedGraph:
    def __init__(self):
        self.nodes = set()
        self.edges = defaultdict(dict)

    def add_node(self, node):
        self.nodes.add(node)

    def add_edge(self, source, target, weight, rpctype):
        if (source, target) in self.edges and self.edges[(source, target)]['rpctype'] == rpctype:
            self.edges[(source, target)]['weight'] += weight
        else:
            self.nodes.add(source)
            self.nodes.add(target)
            self.edges[(source, target)] = {'weight': weight, 'rpctype': rpctype}

def construct_weighted_graph_from_df(group_df):
    weighted_graph = WeightedGraph()

    selected_columns = ['traceid', 'rpc_id', 'rpctype', 'um', 'interface', 'dm']
    processed_df = group_df[selected_columns].copy()
    processed_df['rpc_id'] = processed_df['rpc_id'].astype(str)
    enter_id = '0'       
    
    processed_df['um_interface'] = ""
    processed_df['dm_interface'] = processed_df.apply(
        lambda row: f"{row['dm']}_{row['interface']}" if row['rpctype'] == 'rpc' else row['dm'],
        axis=1
    )

    sorted_df = processed_df.sort_values(by='rpc_id', key=lambda x: x.str.len(), ascending=False)

    for index, row in sorted_df.iterrows():
        rpc_id = row['rpc_id']
        um = row['um']

        if rpc_id == enter_id:
            um_interface = um
        else:
            rpc_id_prefix = rpc_id.rsplit('.', 1)[0]
            upstream_row = sorted_df[sorted_df['rpc_id'] == rpc_id_prefix]
            um_interface = upstream_row.iloc[0]['dm_interface'] if not upstream_row.empty else ""
        processed_df.at[index, 'um_interface'] = um_interface

    for index, row in processed_df.iterrows():
        um = str(row['um_interface'])
        dm = str(row['dm_interface'])
        rpctype = row['rpctype']

        weighted_graph.add_edge(um, dm, weight=1, rpctype=rpctype)

    weighted_graph.nodes = sorted(weighted_graph.nodes)
    weighted_graph.edges = dict(sorted(weighted_graph.edges.items()))

    return weighted_graph


input_path = "./sample_data/checked"
output_path = "./sample_data/call_graph"

os.makedirs(output_path, exist_ok=True)
start_time = time.time()

for file_name in os.listdir(input_path):
    input_file_path = os.path.join(input_path, file_name)
    df = pd.read_csv(input_file_path, dtype={'rpc_id': str})
    if not df.empty:
        service = os.path.splitext(file_name)[0] 
        output_dir = os.path.join(output_path, service)
        os.makedirs(output_dir, exist_ok=True)

        grouped = df.groupby('traceid')

        all_graphs = defaultdict(list)

        for traceid, group_df in grouped:
            weighted_graph = construct_weighted_graph_from_df(group_df)

            found = False
            for existing_graph, traceids in all_graphs.items():
                if existing_graph.nodes == weighted_graph.nodes and existing_graph.edges == weighted_graph.edges:
                    traceids.append(traceid)
                    found = True
                    break
            
            if not found:
                all_graphs[weighted_graph] = [traceid]

        sorted_graphs = sorted(all_graphs.items(), key=lambda x: len(x[1]), reverse=True)

        for i, (graph, traceids_list) in enumerate(sorted_graphs):
            json_filename = f'graph{i + 1}.json'
            json_path = os.path.join(output_dir, json_filename)

            with open(json_path, 'w') as json_file:
                json.dump({
                    'nodes': list(graph.nodes),
                    'edges': [{'source': source, 'target': target, 'weight': data['weight'], 'rpctype': data['rpctype']} 
                            for (source, target), data in graph.edges.items()],
                    'num': len(traceids_list),
                    'traceids': traceids_list
                }, json_file, indent=2)

end_time = time.time()
processing_time = end_time - start_time
print(f"Processing time for all services: {processing_time} seconds")
