import os
import pandas as pd
import time

start_time = time.time() 

directory = "./sample_data/data_origin"

result_df = pd.DataFrame(columns=['service', 'traceidnum'])

for root, dirs, files in os.walk(directory):
    for file in files:
        filepath = os.path.join(root, file)
        data = pd.read_csv(filepath)

        grouped = data.groupby('service')['traceid'].nunique().reset_index()
        grouped.rename(columns={'traceid': 'traceidnum'}, inplace=True)
        
        result_df = pd.concat([result_df, grouped], ignore_index=True)

final_result = result_df.groupby('service')['traceidnum'].sum().reset_index()

output_file = "./sample_data/traceid_num.csv"
final_result.to_csv(output_file, index=False)
end_time = time.time()
execution_time = end_time - start_time 

print("Total processing time:", execution_time, "seconds")