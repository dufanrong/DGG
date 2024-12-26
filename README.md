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
![DGG Overview](./docs/DGG_overview.pdf)

## Quick Start
In the `sample_data` folder, we provide real microservice call graphs constructed using Alibaba trace data. You can use this dataset directly to generate simulated dependency graphs and microservice call graphs. 

To generate graphs, run the following command:
```bash
python3 graph_generator/generator_with_sibling.py
```

DGG generates a set of call graphs for each clustering category and saves them in the `/sample_data/DGG_gen_cgs` folder. The generated graph folders are named based on the generation timestamp.
## Getting Started
