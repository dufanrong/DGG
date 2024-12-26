import os
import pandas as pd
import time

def sanity_check(group):   
    if (group['rpc_id'] == '0').any():
        enter_id = '0'
    else:
        return False

    exclude_condition = ((group['um'].isin(['UNKNOWN', 'UNAVAILABLE'])) | (group['dm'].isin(['UNKNOWN', 'UNAVAILABLE'])))

    if exclude_condition.any():
        return False

    if group['rpc_id'].duplicated().any():
        return False

    sorted_group = group.sort_values('rpc_id', ascending=False)
    for idx, row in sorted_group.iterrows():
        if row['rpc_id'] == enter_id:
            break
        rpc_id_prefix = row['rpc_id'].rsplit('.', 1)[0]
        if rpc_id_prefix not in group['rpc_id'].values:
            return False
        
    return True

def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def process_data(input_path, output_path):
    total_processing_time = 0
    
    for file_name in os.listdir(input_path):
        if file_name.endswith('.csv'):
            print(f"Processing {file_name} ...")
            file_path = os.path.join(input_path, file_name)

            start_time = time.time()
            data = pd.read_csv(file_path, dtype={'rpc_id': str}, on_bad_lines='skip')
            data['rpc_id'] = data['rpc_id'].replace(r'^0.0$', '0', regex=True)

            result_data = data.groupby('traceid').filter(sanity_check)

            result_file_path = os.path.join(output_path, file_name)
            result_data.to_csv(result_file_path, index=False)
            
            end_time = time.time()
            file_processing_time = end_time - start_time
            total_processing_time += file_processing_time
            
            print(f"File {file_name} processed in {format_time(file_processing_time)}")

    print(f"Total processing time: {format_time(total_processing_time)}")

input_path = "./sample_data/service_original"
output_path = "./sample_data/checked"

os.makedirs(output_path, exist_ok=True)
process_data(input_path, output_path)