import json
from collections import Counter
import re
from colormath.color_objects import sRGBColor, LabColor
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import to_rgba
from colormath.color_conversions import convert_color
import colorsys
import numpy as np
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics.pairwise import cosine_distances
from sklearn.metrics import davies_bouldin_score
from sklearn.neighbors import KNeighborsClassifier
import hdbscan
from scipy.sparse import csr_matrix
from scipy.spatial.distance import cdist
from sklearn.metrics.pairwise import euclidean_distances
import dbcv
from scipy.spatial.distance import mahalanobis
from scipy.linalg import inv
from sklearn.decomposition import TruncatedSVD
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import math
import sys
import umap
import statistics
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Function to convert color string to rgba format
def convert_to_rgba(color_str):
    match = re.match(r'rgba?\(([^)]+)\)', color_str)
    if match:
        rgba_values = [float(val) if '.' in val else int(val) for val in match.group(1).split(',')]
        # Normalize the alpha value if present
        if len(rgba_values) == 4 and 0 <= rgba_values[3] <= 1:
            rgba_values[3] = round(rgba_values[3], 2)
        # Convert RGB values to 0-1 range
        rgba_values[:3] = [val / 255.0 for val in rgba_values[:3]]
        return tuple(rgba_values)
    return None

def wef(color_dict):
    # Convert hex color strings to rgba format
    rgba_colors = [convert_to_rgba(color.replace('"', '')) for color in color_dict.keys()]

    # Assign equal weight to all colors
    weights = [1] * len(rgba_colors)

    # Create a bar plot fnormalized RGBA values
    fig, ax = plt.subplots(figsize=(10, 2))
    bar_width = 1
    for i, (color, weight) in enumerate(zip(rgba_colors, weights)):
        ax.add_patch(mpatches.Rectangle((i, 0), bar_width, 1, color=color))

    # Set x-axis labels
    ax.set_xticks(np.arange(len(rgba_colors)) + bar_width / 2)
    ax.set_xticklabels([])  # Remove x-axis labels for better appearance

    # Create legend with color patches using normalized RGBA values
    legend_handles = [mpatches.Patch(color=color, label='1 occurrence') for color in rgba_colors]
    ax.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(0, 1), fancybox=True, shadow=True)

    ax.set_axis_off()
    plt.title('Color Gradient Plot')
    plt.show()

# Function to convert RGB/RGBA string to HSL tuple
def rgb_to_lab(rgb_values):
    r, g, b, *_ = rgb_values
    rgb_color = sRGBColor(r / 255.0, g / 255.0, b / 255.0)
    lab_color = convert_color(rgb_color, LabColor)
    return lab_color.lab_l, lab_color.lab_a, lab_color.lab_b

# Function to convert RGB/RGBA values to HSL format
def extract_lab_values(color_str):
    rgb_values = tuple(map(int, re.findall(r'\d+', color_str)))
    return rgb_to_lab(rgb_values)
    
# Function to convert RGB/RGBA string to HSL tuple
def rgb_to_hsl(rgb_values):
    r, g, b, *_ = rgb_values
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    return h, l, s

# Function to convert RGB/RGBA values to HSL format
def extract_hsl_values(color_str):
    rgb_values = tuple(map(int, re.findall(r'\d+', color_str)))
    return rgb_to_hsl(rgb_values)
    
# Function to convert RGB/RGBA values to HSV format
def extract_hsv_values(color_str):
    rgb_values = tuple(map(int, re.findall(r'\d+', color_str)))
    h, s, v = colorsys.rgb_to_hsv(rgb_values[0] / 255.0, rgb_values[1] / 255.0, rgb_values[2] / 255.0)
    return h, s, v

def process_clustering(data):
    """
    Process clustering data using the original algorithm's logic.
    The input data should have the same structure as the original computed_styles JSON file.
    """
    print("\n=== Starting process_clustering ===")
    print(f"Input data type: {type(data)}")
    print(f"Input data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
    
    useful_attributes = []
    useless_attributes = []
    attribute_values = data["attribute_values"]
    print(f"\nNumber of attribute values: {len(attribute_values)}")
    
    attributes_elements = {}
    print("\nProcessing attribute elements...")
    for t in attribute_values:
        attributes_elements[t[0]] = 0
        for k in t[1]:
            attributes_elements[t[0]] += len(k[1])

    num_unique_elements = Counter(attributes_elements.values())
    numberOfUniqueElements, _ = num_unique_elements.most_common(1)[0]
    print(f"\nNumber of unique elements: {numberOfUniqueElements}")
    
    filtered_attributes = [key for key, value in attributes_elements.items() if value == numberOfUniqueElements]
    print(f"Number of filtered attributes: {len(filtered_attributes)}")
    
    filtered_att_el = {key: value for key, value in attributes_elements.items() if key in filtered_attributes}
    print(f"Number of filtered attribute elements: {len(filtered_att_el)}")

    sumTopPer = 0.0
    countAtts = 0
    avgTopPer = 0.0
    str_VSM = []

    print("\nFirst pass - identifying useful and useless attributes...")
    # First pass - identify useful and useless attributes
    for t in attribute_values:
        if t[0] in filtered_att_el:
            if filtered_att_el[t[0]] == numberOfUniqueElements:
                att_histograms_values = {}
                attributes_elements[t[0]] = 0
                pFlag = 0
                elTypeFlag = 0
                sumOfInternalElements = 0
                for k in t[1]:
                    att_histograms_values[str(k[0])] = str(len(k[1]))
                    if len(k[1]) == numberOfUniqueElements:
                        pFlag = 1
                if pFlag == 0:
                    frstKey, frstVal = next(iter(att_histograms_values.items()))
                    if isinstance(frstKey, str):
                        frstKey = frstKey.strip('"')
                        if re.match(r'rgba?\(\d+, \d+, \d+(, \d+(\.\d+)?)?\)', frstKey):
                            continue  # skip colors
                        elif re.match(r'\d+(\.\d+)?px$', frstKey):
                            for key in att_histograms_values:
                                nkey = key.strip('"')
                                try:
                                    if nkey == 'auto':
                                        nkey = '-1px'
                                    if '%' in nkey:
                                        nperc = nkey.split('%')[0]
                                        nnum = (-1)*float(nperc)/100.0
                                        ntot = nnum 
                                        nkey = str(ntot) + 'px'
                                    px_value = float(nkey.split('px')[0])
                                except:
                                    nkey = '-1px'
                                    px_value = float(nkey.split('px')[0])
                                att_histograms_values[key] = {'value': att_histograms_values[key], 'px': px_value}
                            sorted_att_histograms_values = dict(sorted(att_histograms_values.items(), key=lambda x: x[1]['px']))
                            sorted_att_histograms_values_strings = {key: value['value'] for key, value in sorted_att_histograms_values.items()}
                        elif re.match(r'\d+(\.\d+)?px \d+(\.\d+)?px$', frstKey):
                            elTypeFlag = 1
                        elif re.match(r'\d+(\.\d+)?$', frstKey):
                            for key in att_histograms_values:
                                nkey = key.strip('"')
                                if nkey == 'auto':
                                    nkey = '-1'
                                num_value = float(nkey)
                                att_histograms_values[key] = {'value': att_histograms_values[key], 'num': num_value}
                            sorted_att_histograms_values = dict(sorted(att_histograms_values.items(), key=lambda x: x[1]['num']))
                            sorted_att_histograms_values_strings = {key: value['value'] for key, value in sorted_att_histograms_values.items()}
                        elif re.match(r'.*rgb\(\d+, \d+, \d+\)', frstKey):
                            elTypeFlag = 1
                        else:
                            for k in t[1]:
                                if k[0] not in str_VSM:
                                    str_VSM.append(k[0])
                            elTypeFlag = 1
                    else:
                        print(f'Unknown type: {type(frstKey).__name__}')
                    numOfElements = []
                    valOfElements = []
                    if elTypeFlag == 1:
                        for i in att_histograms_values.items():
                            numOfElements.append(float(int(i[1])/numberOfUniqueElements)*100)
                            valOfElements.append(i[0])
                    else:
                        for i in sorted_att_histograms_values_strings.items():
                            numOfElements.append(float(int(i[1])/numberOfUniqueElements)*100)
                            valOfElements.append(i[0])
                            
                    countAtts += 1
                    sumTopPer += max(numOfElements)
                    if max(numOfElements) <= 95:
                        if t[0] in ["font-size", "font-weight", "font-style", "font-variant", "font-feature-settings", "text-align", "text-decoration", "letter-spacing", "line-height", "white-space", "word-spacing", "word-wrap", "word-break", "text-size", "width", "height", "min-width", "min-height", "max-width", "max-height", "cursor"]:
                            useful_attributes.append(t[0])
                    else:
                        useless_attributes.append(t[0])

    avgTopPer = sumTopPer / countAtts
    print(f"\nUseful attributes: {useful_attributes}")
    print(f"Useless attributes: {useless_attributes}")
    print(f"Average top percentage: {avgTopPer}")

    print("\nSecond pass - processing useful attributes...")
    # Second pass - process useful attributes
    pageVectors = {}
    pageElementsVisited = {}

    for t in attribute_values:
        if t[0] in useful_attributes:
            for k in t[1]:
                for el_id in k[1]:
                    if el_id not in pageElementsVisited:
                        pageElementsVisited[el_id] = 0

    print(f"\nNumber of page elements: {len(pageElementsVisited)}")

    flag_new_vec = 0
    str_new_vec = ''
    for t in attribute_values:
        if flag_new_vec == 0:
            str_new_vec = ''
        if t[0] in useful_attributes:
            for k in t[1]:
                for el_id in k[1]:
                    pageElementsVisited[el_id] = 0
            frstKey = t[1][0][0]
            count_els = 0
            for k in t[1]:
                for el_id in k[1]:
                    count_els += 1
                if isinstance(frstKey, str):
                    frstKey = frstKey.strip('"').strip("'")
                    if re.match(r'rgba?\(\d+, \d+, \d+(, \d+(\.\d+)?)?\)', frstKey):
                        elTypeFlag = 1
                    elif re.match(r'\d+(\.\d+)?px$', frstKey):
                        for el_id in k[1]:
                            pixel_k_value = k[0].strip('"')
                            try:
                                if pixel_k_value == 'auto':
                                    pixel_k_value = '-1'
                                if '%' in pixel_k_value:
                                    nperc = pixel_k_value.split('%')[0]
                                    nnum = (-1)*float(nperc)/100.0
                                    ntot = nnum
                                    pixel_k_value = str(ntot)
                                pixel_k_value = float(pixel_k_value.split('px')[0])
                            except:
                                pixel_k_value = '-1'
                            if el_id not in pageVectors:
                                pageVectors[el_id] = []
                            if pageElementsVisited[el_id] == 0:
                                pageVectors[el_id].append(float(pixel_k_value))
                            pageElementsVisited[el_id] = len(pageVectors[el_id])
                    elif re.match(r'\d+(\.\d+)?px \d+(\.\d+)?px$', frstKey):
                        for el_id in k[1]:
                            pixel_k_values = k[0].strip('"').split(' ')
                            try:
                                pixel_k_value_X = pixel_k_values[0]
                                pixel_k_value_Y = pixel_k_values[1]
                                if 'auto' in k[0]:
                                    pixel_k_value_X = '-1'
                                    pixel_k_value_Y = '-1'
                                if '%' in k[0]:
                                    npercX = pixel_k_values[0].split('%')[0]
                                    nnumX = (-1)*float(npercX)/100.0
                                    ntotX = nnumX
                                    pixel_k_value_X = str(ntotX)
                                    npercY = pixel_k_values[1].split('%')[0]
                                    nnumY = (-1)*float(npercY)/100.0
                                    ntotY = nnumY
                                    pixel_k_value_Y = str(ntotY)
                                pixel_k_value_X = float(pixel_k_value_X.split('px')[0])
                                pixel_k_value_Y = float(pixel_k_value_Y.split('px')[0])
                            except:
                                pixel_k_value_X = '-1'
                                pixel_k_value_Y = '-1'
                            if pixel_k_value_X < pixel_k_value_Y:
                                pixel_k_value_X = pixel_k_value_X * (-1)
                                pixel_k_value_Y = pixel_k_value_Y * (-1)
                            if el_id not in pageVectors:
                                pageVectors[el_id] = []
                            if pageElementsVisited[el_id] == 0:
                                pageVectors[el_id].append(float(pixel_k_value_X))
                                pageVectors[el_id].append(float(pixel_k_value_Y))
                            pageElementsVisited[el_id] = len(pageVectors[el_id])
                        elTypeFlag = 1
                    elif re.match(r'\d+(\.\d+)?$', frstKey):
                        for el_id in k[1]:
                            if el_id not in pageVectors:
                                pageVectors[el_id] = []
                            if pageElementsVisited[el_id] == 0:
                                pageVectors[el_id].append(float(str(k[0]).strip('"')))
                            pageElementsVisited[el_id] = len(pageVectors[el_id])
                    elif re.match(r'.*rgb\(\d+, \d+, \d+\)', frstKey):
                        elTypeFlag = 1
                    else:
                        for el_id in k[1]:
                            if el_id not in pageVectors:
                                pageVectors[el_id] = []
                            if pageElementsVisited[el_id] == 0:
                                pageVectors[el_id].append(float(str_VSM.index(k[0])))
                            pageElementsVisited[el_id] = len(pageVectors[el_id])
                else:
                    print(f'Unknown type: {type(frstKey).__name__}')

    print(f"\nNumber of page vectors: {len(pageVectors)}")

    # Convert pageVectors to arrays
    pageVectorsIDs = []
    pageVectorsValues = []

    for key, value in pageVectors.items():
        pageVectorsIDs.append(key)
        pageVectorsValues.append(value)

    print(f"\nNumber of vector IDs: {len(pageVectorsIDs)}")
    print(f"Number of vector values: {len(pageVectorsValues)}")

    # Convert pageVectorsValues into a NumPy array
    arr_2B_red = np.array(pageVectorsValues)
    print(f"\nArray shape: {arr_2B_red.shape}")

    # Standardize and Normalize Data
    print("\nStandardizing and normalizing data...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(arr_2B_red)
    X_normalized = X_scaled
    print(f"Scaled data shape: {X_scaled.shape}")

    # Define ranges for parameter search
    min_cluster_size_range = range(5, 21, 1)
    cluster_selection_epsilon = 0.0

    # Store best configuration for each min_cluster_size
    best_configs = {}

    print("\nStarting grid search for clustering parameters...")
    # Grid search over min_cluster_size and cluster_selection_epsilon
    for min_cluster_size in min_cluster_size_range:
        print(f"\nTrying min_cluster_size: {min_cluster_size}")
        cluster_selection_epsilon = 0  
        while cluster_selection_epsilon <= 1:
            # Apply HDBSCAN clustering
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size,
                cluster_selection_epsilon=cluster_selection_epsilon
            )
            labels = clusterer.fit_predict(X_normalized)
            
            # Step 1: Ensure at least one valid cluster (not just outliers)
            if len(set(labels)) > 1:  # Ensure there are at least two clusters (valid clusters)
                dbcv_score = dbcv.dbcv(X_normalized, labels, check_duplicates=False)
                print(f"  epsilon: {cluster_selection_epsilon:.1f}, DBCV score: {dbcv_score:.3f}")
                
                if min_cluster_size not in best_configs or dbcv_score > best_configs[min_cluster_size][0] or dbcv_score > 0.5:
                    best_configs[min_cluster_size] = (dbcv_score, min_cluster_size, cluster_selection_epsilon, labels)
            
            # Step 2: Identify outliers (label == -1)
            outliers = np.where(labels == -1)[0]
            
            # Step 3: Compute centroids of clusters (excluding outliers)
            cluster_centroids = {}
            for cluster_id in set(labels):
                if cluster_id != -1:  # Skip outliers
                    cluster_points = X_normalized[labels == cluster_id]
                    cluster_centroids[cluster_id] = np.mean(cluster_points, axis=0)
            
            # Step 4: Assign outliers to the closest cluster based on Euclidean distance
            for outlier in outliers:
                outlier_point = X_normalized[outlier]
                distances = {cluster_id: euclidean_distances([outlier_point], [centroid])[0][0]
                             for cluster_id, centroid in cluster_centroids.items()}
                nearest_cluster = min(distances, key=distances.get)
                labels[outlier] = nearest_cluster
            
                # Recalculate centroids including the newly assigned outliers
                for cluster_id in set(labels):
                    if cluster_id != -1:
                        cluster_points = X_normalized[labels == cluster_id]
                        cluster_centroids[cluster_id] = np.mean(cluster_points, axis=0)
            
            # Reassign outliers to the closest cluster based on Euclidean distance
            for outlier in outliers:
                outlier_point = X_normalized[outlier]
                distances = {cluster_id: euclidean_distances([outlier_point], [centroid])[0][0]
                             for cluster_id, centroid in cluster_centroids.items()}
                nearest_cluster = min(distances, key=distances.get)
                labels[outlier] = nearest_cluster
                
            cluster_selection_epsilon += 0.1

    # Convert best configurations to a sorted list (top 10 based on DBCV score)
    top_k_configs = sorted(best_configs.values(), reverse=True, key=lambda x: x[0])[:10]
    print(f"\nFound {len(top_k_configs)} best configurations")

    # Return the final clusters
    if top_k_configs:
        _, _, _, labels = top_k_configs[0]  # Get the best configuration
        print(f"\nUsing best configuration with DBCV score: {top_k_configs[0][0]:.3f}")
        cluster_dict = {}
        
        for idx, cluster_id in enumerate(labels):
            if cluster_id != -1:  # Ignore outliers
                cluster_dict.setdefault(cluster_id, []).append(str(pageVectorsIDs[idx]))

        final_clusters = [members for members in cluster_dict.values()]
        print(f"\nFinal number of clusters: {len(final_clusters)}")
        print("=== End process_clustering ===\n")
        return final_clusters
    
    print("\nNo valid clusters found!")
    print("=== End process_clustering ===\n")
    return [] 