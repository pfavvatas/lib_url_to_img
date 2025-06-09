#!/usr/bin/env python3
import json
import sys
import os
from lib.utils.clustering import process_clustering

def main():
    # Example data structure
    sample_data = {
        "attribute_values": [
            ["color", [
                ["rgb(255, 0, 0)", ["1", "2", "3", "4", "5"]],
                ["rgb(0, 255, 0)", ["6", "7", "8", "9", "10"]],
                ["rgb(0, 0, 255)", ["11", "12", "13", "14", "15"]]
            ]],
            ["font-size", [
                ["12px", ["1", "2", "6", "7", "11", "12"]],
                ["14px", ["3", "4", "8", "9", "13", "14"]],
                ["16px", ["5", "10", "15"]]
            ]],
            ["margin", [
                ["10px", ["1", "3", "5", "7", "9", "11", "13", "15"]],
                ["20px", ["2", "4", "6", "8", "10", "12", "14"]]
            ]]
        ]
    }

    # If a file path is provided as argument, read from that file
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    else:
        # Use sample data if no file provided
        data = sample_data
        print("Using sample data. To use your own data, provide a JSON file path as argument.")
        print("Example: python run_clustering.py path/to/your/data.json")

    # Run clustering
    try:
        clusters = process_clustering(data)
        print("\nClustering Results:")
        print(f"Number of clusters found: {len(clusters)}")
        for i, cluster in enumerate(clusters):
            print(f"\nCluster {i+1} (size: {len(cluster)}):")
            print(f"Elements: {', '.join(cluster)}")
    except Exception as e:
        print(f"Error during clustering: {e}")

if __name__ == "__main__":
    main() 