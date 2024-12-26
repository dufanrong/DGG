
import os
import pandas as pd
import shutil

def copy_json_files(input_path, output_folder, services):
    for service in services:
        json_file = os.path.join(input_path, f"{service}.json")
        output_path = os.path.join(output_folder, f"{service}.json")
        shutil.copy(json_file, output_path)

def process_group(group, input_path, output_base_path):
    label = group['label'].iloc[0]
    output_folder = os.path.join(output_base_path, f"type{label}")
    os.makedirs(output_folder, exist_ok=True)

    copy_json_files(input_path, output_folder, group['service'])

csv_path = './sample_data/service_info.csv'
input_path = './sample_data/dependency_graph_with_label'
output_path = './sample_data/real_dependency_graph'

data = pd.read_csv(csv_path)
grouped_data = data.groupby('label')

for label, group in grouped_data:
    process_group(group, input_path, output_path)
