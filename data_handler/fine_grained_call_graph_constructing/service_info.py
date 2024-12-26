import pandas as pd

service_traceid_num_df = pd.read_csv("./sample_data/traceid_num.csv")
cg_num_df = pd.read_csv("./sample_data/cg_num.csv")

merged_df = service_traceid_num_df[service_traceid_num_df['service'].isin(cg_num_df['service'])]

final_df = pd.merge(merged_df, cg_num_df, on='service')

# 保存合并后的结果到新的 CSV 文件
final_df.to_csv("./sample_data/service_info.csv", index=False)