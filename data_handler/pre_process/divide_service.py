import os
import pandas as pd
import time

directory = "./sample_data/data_origin"
service_list_path = "./sample_data/service_info.csv"
output_path = "./sample_data/service_original"

if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path)

service_df = pd.read_csv(service_list_path)
selected_services = service_df['service'].tolist()

total_file_processing_time = 0
start_total_time = time.time()

for filename in os.listdir(directory):
    if filename.endswith(".csv"):
        file_path = os.path.join(directory, filename)

        start_file_time = time.time()
        
        data_df = pd.read_csv(file_path)

        filtered_data = data_df[data_df['service'].isin(selected_services)]

        for service_name, service_data in filtered_data.groupby('service'):
            service_output_path = os.path.join(output_folder_path, f"{service_name}.csv")
            
            if os.path.exists(service_output_path):
                service_data.to_csv(service_output_path, mode='a', header=False, index=False)
            else:
                service_data.to_csv(service_output_path, index=False)
        
        end_file_time = time.time()
        file_processing_time = end_file_time - start_file_time
        total_file_processing_time += file_processing_time
        print(f"Processed {filename} in {time.strftime('%H:%M:%S', time.gmtime(file_processing_time))}")

end_total_time = time.time()
total_time = end_total_time - start_total_time

print(f"Total processing time for all files: {time.strftime('%H:%M:%S', time.gmtime(total_time))}")