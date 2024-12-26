import os
import json
import csv

def calculate_traceid_num(json_path):
    traceid_num = 0
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)
        traceid_num = data.get('num', 0)
    return traceid_num

def process_folder(input_path):
    rows = []
    for service_dir in os.listdir(input_path):
        service_path = os.path.join(input_path, service_dir)

        if os.path.isdir(service_path):
            cg_num = len(os.listdir(service_path)) 
            traceid_nums = []
            for i in range(1, cg_num + 1):
                json_file_path = os.path.join(service_path, f'graph{i}.json')
                if os.path.exists(json_file_path):
                    traceid_num = calculate_traceid_num(json_file_path)
                    traceid_nums.append(traceid_num)
            traceid_nums.sort(reverse=True)
            traceid_sum = sum(traceid_nums)
            top_90_sum = 0
            top_90_count = 0
            for num in traceid_nums:
                top_90_sum += num
                top_90_count += 1
                if top_90_sum > 0.9 * traceid_sum:
                    break
            rows.append([service_dir, cg_num, top_90_count])
    return rows

input_path = "./sample_data/call_graph"
data_rows = process_folder(input_path)

output_file_path = "./sample_data/cg_num.csv"

with open(output_file_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['service', 'cg_num', 'top_90_cg_num'])
    writer.writerows(data_rows)

print("CSV file generated successfully.")