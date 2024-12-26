import os
import pandas as pd
import shutil

csv_file = './sample_data/service_info.csv'
source_folder = './sample_data/call_graph_with_label'
output_path = './sample_data/real_call_graph'

df = pd.read_csv(csv_file)

labels = df['label'].unique()

os.makedirs(output_path, exist_ok=True)

for label in labels:
    label_folder = os.path.join(output_path, f"type{label}")
    os.makedirs(label_folder, exist_ok=True)
    
    services = df[df['label'] == label]['service'].tolist()
    
    for service in services:
        source_folder_path = os.path.join(source_folder, service)
        destination_folder_path = os.path.join(label_folder, service)

        shutil.copytree(source_folder_path, destination_folder_path)