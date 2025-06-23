# Service Dependency Graph Generator (DGG)

The **Service Dependency Graph Generator (DGG)** is a tool designed to generate service dependency graphs with production-level characteristics from benchmark traces. It enables researchers and practitioners to simulate realistic microservice environments for performance evaluation and analysis. 

DGG consists of two main components:

1. **Data Handler**:
    - Constructs fine-grained call graphs that capture dynamic interface and repeated calling features from the trace data.
    - Merges these call graphs into dependency graphs.
    - Clusters the dependency graphs into different categories based on their topological structures and invocation types.

2. **Graph Generator**:
    - Takes the organized data and a selected category from the Data Handler.
    - Simulates real-world microservice invocation processes using a random graph model.
    - Generates multiple call graphs and merges them into a small-scale service dependency graph that reflects production-level characteristics.

## Overview
![DGG Overview](https://github.com/dufanrong/DGG/blob/main/docs/DGG_overview.png)

For more details about DGG, you can read our paper: [https://hpcrl.github.io/ICS2025-webpage/program/Proceedings_ICS25/ics25-22.pdf)

## Quick Start
In the `sample_data` folder, we provide real microservice call graphs constructed using Alibaba trace data. You can use this dataset directly to generate simulated dependency graphs and microservice call graphs. 

To generate graphs, run the following command:
```
python3 graph_generator/generator_with_sibling.py
```
DGG generates a set of call graphs for each clustering category and saves them in the `/sample_data/DGG_gen_cgs` folder. The generated graph folders are named based on the generation timestamp.

We also provide a simple visualization script to visualize the generated call graphs as PDFs for easy observation of their features. Replace the `callgraph_path` in line 34 of `visualize_callgraphs.py` with the path of your generated call graphs and run:
```
python3 visualize_callgraphs.py
```
The visualized images will be saved in the `DGG/sample_data/visualize` folder.

## Getting Started

This README guides you through the setup, installation, and execution of the various components of DGG.

### Prerequisites
Before using DGG, ensure you have the following:
- Python 3.7+
- Pandas
- GraKeL (for clustering service dependency graphs)
- PyGraphviz (for creating and visualizing graphs, optional)

### Installation
Clone the repository:
```
git clone https://github.com/dufanrong/DGG.git
cd DGG
```

---

### Data Handler

The **data_handler** module processes the trace data in three stages: **Pre-process**, **Fine-grained Call Graph Constructing**, and **Dependency Graph Clustering**.

#### Folder Structure

- `DGG/sample_data/data_origin`: Contains the original, unprocessed trace data.
- `DGG/sample_data/service_original`: Contains the divided service trace CSV files.
- `DGG/sample_data/checked`: Contains the filtered trace data with disconnected traces removed.

#### 1. Pre-process

The **Pre-process** step prepares the raw trace data by performing the following tasks:

**1.1 Trace Statistics**

The first step is to count the query frequency of each service based on the traces. This helps identify which services are frequently invoked and which are less common. The output file `traceid_num.csv` saves the number of queries for each service in the trace.

```
python3 data_handler/pre_process/traceid_count.py
```

**1.2 Divide Services**

Run the `divide_service.py` script to divide the trace data based on services. Each service’s trace will be saved as a separate CSV file.

```
python3 data_handler/pre_process/divide_service.py
```

**1.3 Filter Disconnected Trace Data**

In some cases, traces may be incomplete or disconnected. These disconnected traces should be filtered out to ensure that only valid, connected traces are used in subsequent analysis.

```
python3 data_handler/pre_process/filter_disconnected_trace_data.py 
```

---

#### 2. Fine-grained Call Graph Constructing

This step constructs the call graphs and dependency graphs for each service based on the traces. It also assigns labels to services based on their communication patterns and downstream invocations.

File Structure:
- `DGG/sample_data/call_graph`: Fine-grained call graphs constructed from the traces. Each subfolder stores all call graphs for a specific service, sorted by query count.
- `DGG/sample_data/cg_num.csv`: The number of call graphs per service.
- `DGG/sample_data/dependency_graph`: The dependency graphs for each service.
- `DGG/sample_data/service_info.csv`: Service statistics, including the number of call graphs, query counts, and cluster categories.
- `DGG/sample_data/node_label.csv`: Labels for each service, including `relay`, `normal`, `blackhole`, `Memcached`, and `database`.
- `DGG/sample_data/call_graph_with_label`, `DGG/sample_data/dependency_graph_with_label`: Call graphs and dependency graphs with labels.

**Construct Fine-grained Call Graphs**
```
python3 data_handler/fine_grained_call_graph_constructing/construct_cg.py
```

**Count the number of call graphs per service**
```
python3 data_handler/fine_grained_call_graph_constructing/count_cg_num.py
```

**Merge all call graphs to form the dependency graph**
```
python3 data_handler/fine_grained_call_graph_constructing/merge_cg.py
```

**Get service statistics**
```
python3 data_handler/fine_grained_call_graph_constructing/service_info.py
```

**Assign labels to services based on their communication behaviors:**
- If the communication mode is `mc`, label the service as `Memcached`.
- If the service always calls downstream services in all call graphs, label it as `relay`.
- If the service never calls downstream services, label it as `blackhole`.
- Otherwise, label it as `normal`.

```
python3 data_handler/fine_grained_call_graph_constructing/get_node_label.py
```

**Add labels to the constructed call graphs and dependency graphs**
```
python3 data_handler/fine_grained_call_graph_constructing/add_label.py
```

#### 3. Dependency Graph Clustering

Use graph kernel methods to cluster the dependency graphs based on their topological structure, service labels, and communication patterns. The clustering is performed using k-means clustering.

File Structure:
- `DGG/sample_data/real_call_graph`: Real call graphs grouped by clustering categories.
- `DGG/sample_data/real_dependency_graph`: Real dependency graphs grouped by clustering categories.

**Determine the optimal value for `k` (number of clusters)** by iterating over possible values and selecting the one that maximizes the silhouette score.
```
python3 data_handler/dependency_graph_clustering/decide_k.py
```

**Cluster the dependency graphs using k-means**
```
python3 data_handler/dependency_graph_clustering/cluster_dependency_graph.py
```

**Divide call graphs and dependency graphs into categories based on clustering results**
```
python3 data_handler/dependency_graph_clustering/call_graph_divide_type.py
python3 data_handler/dependency_graph_clustering/dependency_graph_divide_type.py
```

### Graph Generator

The **Graph Generator** first creates a probability model for the real call graphs, then generates simulated call graphs based on this model. You can generate call graphs for all clustering categories or for specific categories as needed.


File Structure:
- `DGG/sample_data/real_call_graph_renamed`: Real call graphs with renamed services.
- `DGG/sample_data/DGG_gen_cgs`: Simulated call graphs generated by DGG.
- `DGG/sample_data/visualize`: PDFs of visualized call graphs.

#### Random Graph Modeler

Map the microservice names and interfaces in the call graph to similar features, renaming them to have the same names where applicable.
```
python3 graph_generator/rename_ms.py
```

Generate simulated call graphs. Modify line 346 of `generator_with_sibling.py` to specify the number of call graphs (`n`) and the service types (`service_types`) for which you wish to generate call graphs, then run:
```
python3 graph_generator/generator_with_sibling.py
```

The script will use the probability model to simulate the call graph generation process. Based on the specified number of graphs and cluster categories, DGG will generate call graphs for each cluster, filtering out low-frequency graphs (this can be skipped by commenting out `graph_gen.filter_low_frequency_graphs()`).

**Visualize the generated call graphs as PDFs**
```
python3 visualize_callgraphs.py
```

---

Feel free to adjust the scripts and parameters based on your specific needs and configurations.
