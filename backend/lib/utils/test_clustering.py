import sys
import os

# Add the parent directory to Python path
lib_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# Try importing the required modules
print("Testing imports...")
try:
    from colormath.color_objects import sRGBColor, LabColor
    print("✓ colormath imported successfully")
except ImportError as e:
    print(f"✗ Error importing colormath: {e}")

try:
    import pandas as pd
    print("✓ pandas imported successfully")
except ImportError as e:
    print(f"✗ Error importing pandas: {e}")

try:
    import seaborn as sns
    print("✓ seaborn imported successfully")
except ImportError as e:
    print(f"✗ Error importing seaborn: {e}")

try:
    import matplotlib.pyplot as plt
    print("✓ matplotlib imported successfully")
except ImportError as e:
    print(f"✗ Error importing matplotlib: {e}")

try:
    from sklearn.preprocessing import StandardScaler
    print("✓ scikit-learn imported successfully")
except ImportError as e:
    print(f"✗ Error importing scikit-learn: {e}")

try:
    import hdbscan
    print("✓ hdbscan imported successfully")
except ImportError as e:
    print(f"✗ Error importing hdbscan: {e}")

try:
    import numpy as np
    print("✓ numpy imported successfully")
except ImportError as e:
    print(f"✗ Error importing numpy: {e}")

try:
    import umap
    print("✓ umap-learn imported successfully")
except ImportError as e:
    print(f"✗ Error importing umap-learn: {e}")

try:
    import dbcv
    print("✓ dbcv imported successfully")
except ImportError as e:
    print(f"✗ Error importing dbcv: {e}")

# Try importing the clustering module
print("\nTesting clustering module...")
try:
    from utils.clustering import process_clustering
    print("✓ clustering module imported successfully")
except ImportError as e:
    print(f"✗ Error importing clustering module: {e}")

# Test with sample data
print("\nTesting process_clustering function...")
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

try:
    result = process_clustering(sample_data)
    print("✓ process_clustering executed successfully")
    print(f"Number of clusters found: {len(result)}")
    for i, cluster in enumerate(result):
        print(f"Cluster {i+1} size: {len(cluster)}")
except Exception as e:
    print(f"✗ Error in process_clustering: {e}")

# Test DBCV functionality
print("\nTesting DBCV functionality...")
try:
    # Create some sample data with clear clusters
    np.random.seed(42)  # For reproducibility
    n_samples = 100
    n_features = 2
    
    # Generate three distinct clusters
    cluster1 = np.random.randn(n_samples//3, n_features) + np.array([0, 0])
    cluster2 = np.random.randn(n_samples//3, n_features) + np.array([5, 5])
    cluster3 = np.random.randn(n_samples//3, n_features) + np.array([-5, 5])
    
    X = np.vstack([cluster1, cluster2, cluster3])
    labels = np.array([0] * (n_samples//3) + [1] * (n_samples//3) + [2] * (n_samples//3))
    
    # Calculate DBCV score
    score = dbcv.dbcv(X, labels)
    print(f"✓ DBCV score calculated successfully: {score}")
    
    # Test clustering on the synthetic data
    synthetic_data = {
        "attribute_values": [
            ["feature1", [[str(x[0]), [str(i)]] for i, x in enumerate(X)]],
            ["feature2", [[str(x[1]), [str(i)]] for i, x in enumerate(X)]]
        ]
    }
    
    try:
        result = process_clustering(synthetic_data)
        print("\nTesting clustering on synthetic data:")
        print(f"Number of clusters found: {len(result)}")
        for i, cluster in enumerate(result):
            print(f"Cluster {i+1} size: {len(cluster)}")
    except Exception as e:
        print(f"✗ Error in synthetic data clustering: {e}")
        
except Exception as e:
    print(f"✗ Error in DBCV calculation: {e}") 