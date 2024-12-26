import os
import json

def process_types(input_path, type_list):
    for service_type in type_list:
        input_directory = os.path.join(input_path, f"type{service_type}")
        if not os.path.exists(input_directory):
            continue
        
        num_list = []

        num_files = sum(1 for _ in os.listdir(input_directory) if _.startswith("graph") and _.endswith(".json"))

        for i in range(1, num_files + 1):
            filename = f"graph{i}.json"
            filepath = os.path.join(input_directory, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as file:
                    data = json.load(file)
                    num = data.get("num", 0)
                    num_list.append((num, filepath)) 

        num_list.sort(reverse=True, key=lambda x: x[0])

        total_sum = sum(num for num, _ in num_list)
        target_sum = total_sum * 0.9

        current_sum = 0
        index = 0
        for i, (num, _) in enumerate(num_list):
            current_sum += num
            if current_sum >= target_sum:
                index = i + 1
                break

        print(f"Type {service_type}: {index}")

        for num, filepath in num_list[index:]:
            os.remove(filepath)
