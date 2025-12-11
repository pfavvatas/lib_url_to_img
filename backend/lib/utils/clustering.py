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
import time
import umap
import statistics
import warnings

# Control warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)  # This will suppress the scikit-learn deprecation warnings

# If you want to see the warnings, comment out the line above and uncomment the line below:
# warnings.filterwarnings("default", category=FutureWarning)

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

    # Create a bar plot with normalized RGBA values
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

def perform_clustering_analysis(data, enable_early_stop=False, early_stop_threshold=0.25, 
                                 enable_final_threshold=False, final_threshold=0.5):
    """
    Perform clustering analysis on the provided data.
    
    Args:
        data: Dictionary containing the JSON data with 'attribute_values' key
        enable_early_stop: Boolean to enable early stopping when DBCV score is below threshold (default: False)
        early_stop_threshold: DBCV score threshold for early stopping (default: 0.25)
        enable_final_threshold: Boolean to enable final threshold filtering (default: False)
        final_threshold: DBCV score threshold for final cluster selection (default: 0.5)
        
    Returns:
        Dictionary containing:
        - 'success': Boolean indicating if clustering was successful
        - 'clusters': List of clusters (if successful)
        - 'cluster_info': Dictionary with clustering parameters and metrics
        - 'message': Status message
    """
    try:
        print(f"  📊 Starting clustering analysis...")
        analysis_start_time = time.time()
        useful_attributes = []
        useless_attributes = []

        attribute_values = data["attribute_values"]

        attributes_elements = {}

        for t in attribute_values:
            attributes_elements[t[0]] = 0
            for k in t[1]:
                attributes_elements[t[0]] += len(k[1])

        num_unique_elements = Counter(attributes_elements.values())

        numberOfUniqueElements, _ = num_unique_elements.most_common(1)[0]

        filtered_attributes = [key for key, value in attributes_elements.items() if value == numberOfUniqueElements]

        filtered_att_el = {key: value for key, value in attributes_elements.items() if key in filtered_attributes}

        sumTopPer = 0.0
        countAtts = 0
        avgTopPer = 0.0
        str_VSM = []

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
                            # Remove quotes from the input value
                            frstKey = frstKey.strip('"')
                            # Case for strings
                            if re.match(r'rgba?\(\d+, \d+, \d+(, \d+(\.\d+)?)?\)', frstKey):
                                continue #skip colors
                                for key in att_histograms_values:
                                    hsv_values = extract_hsv_values(key)
                                    att_histograms_values[key] = {'value': att_histograms_values[key], 'hsv': hsv_values}
                                sorted_att_histograms_values = dict(sorted(att_histograms_values.items(), key=lambda x: (x[1]['hsv'][0], x[1]['hsv'][1], x[1]['hsv'][2])))
                                # Create a new dictionary with only the string values
                                sorted_att_histograms_values_strings = {key: value['value'] for key, value in sorted_att_histograms_values.items()}
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
                                # Default case for other string values
                                for k in t[1]:
                                    if k[0] not in str_VSM:
                                        if k[0] == '"start"':
                                            str_VSM.append('"left"') #bootstrap start-->left
                                        else:
                                            if k[0] == '"end"':
                                                str_VSM.append('"right"')
                                            else:
                                                if t[0] == 'text-decoration-line' or t[0] == 'text-decoration-style':
                                                    print(k[0])
                                                str_VSM.append(k[0])
                                elTypeFlag = 1
                        else:
                            # Default case for other types
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
                        if max(numOfElements) <= 100:
                            #if t[0] in ["font-size", "font-weight", "font-style", "font-variant", "font-feature-settings", "text-align", "text-decoration", "line-height", "word-wrap", "word-break", "text-size", "width", "height", "min-width", "min-height", "max-width", "max-height", "cursor"]:
                            if t[0] in ["font-size", "font-weight", "font-style", "text-align", "text-decoration-line", "text-decoration-style", "line-height", "word-break", "cursor"]:
                                useful_attributes.append(t[0])
                        else:
                            useless_attributes.append(t[0])

        avgTopPer = sumTopPer / countAtts

        for t in attribute_values:
            if t[0] in useful_attributes:
                if filtered_att_el[t[0]] == numberOfUniqueElements:
                    att_histograms_values = {}
                    attributes_elements[t[0]] = 0
                    pFlag = 0
                    elTypeFlag = 0
                    sumOfInternalElements = 0
                    for k in t[1]:
                        att_histograms_values[str(k[0])] = k[1]
                        if len(k[1]) == numberOfUniqueElements:
                            pFlag = 1
                    if pFlag == 0:
                        frstKey, frstVal = next(iter(att_histograms_values.items()))
                        if isinstance(frstKey, str):
                            # Remove quotes from the input value
                            frstKey = frstKey.strip('"')
                            # Case for strings
                            if re.match(r'rgba?\(\d+, \d+, \d+(, \d+(\.\d+)?)?\)', frstKey):
                                for key in att_histograms_values:
                                    hsv_values = extract_hsv_values(key)
                                    att_histograms_values[key] = {'value': att_histograms_values[key], 'hsv': hsv_values}
                                sorted_att_histograms_values = dict(sorted(att_histograms_values.items(), key=lambda x: (x[1]['hsv'][0], x[1]['hsv'][1], x[1]['hsv'][2])))
                                # Create a new dictionary with only the string values
                                sorted_att_histograms_values_strings = {key: value['value'] for key, value in sorted_att_histograms_values.items()}
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
                                # Default case for other string values
                                for k in t[1]:
                                    if k[0] not in str_VSM:
                                        if k[0] == '"start"':
                                            str_VSM.append('"left"') #bootstrap start-->left
                                        else:
                                            if k[0] == '"end"':
                                                str_VSM.append('"right"')
                                            else:
                                                print(k[0])
                                                str_VSM.append(k[0])
                                elTypeFlag = 1
                        else:
                            # Default case for other types
                            print(f'Unknown type: {type(frstKey).__name__}')
                        numOfElements = []
                        valOfElements = []

        pageVectors = {}
        pageElementsVisited = {}

        for t in attribute_values:
            if t[0] in useful_attributes:
                for k in t[1]:
                    for el_id in k[1]:
                        if el_id not in pageElementsVisited:
                            pageElementsVisited[el_id] = 0

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
                        # Remove quotes from the input value
                        frstKey = frstKey.strip('"').strip("'")
                        # Case for strings
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
                                    pixel_k_value_X = -1
                                    pixel_k_value_Y = -1
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
                                    if k[0] == '"start"':
                                        pageVectors[el_id].append(float(str_VSM.index('"left"')))
                                    elif k[0] == '"end"':
                                        pageVectors[el_id].append(float(str_VSM.index('"right"')))
                                    else:
                                        pageVectors[el_id].append(float(str_VSM.index(k[0])))
                                pageElementsVisited[el_id] = len(pageVectors[el_id])
                    else:
                        # Default case for other types
                        print(f'Unknown type: {type(frstKey).__name__}')
                        

        # Assuming pageVectors is your dictionary with vectors
        pageVectorsIDs = []
        pageVectorsValues = []

        # Convert pageVectors to arrays
        for key, value in pageVectors.items():
            pageVectorsIDs.append(key)
            pageVectorsValues.append(value)

        # Convert pageVectorsValues into a NumPy array
        arr_2B_red = np.array(pageVectorsValues)

        # --- Standardize and Normalize Data ---
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(arr_2B_red)
        X_normalized = X_scaled

        max_range_cl_size = int(len(pageVectorsIDs)*10/100)+1
        if max_range_cl_size <= 5:
            max_range_cl_size = 10

        # Define ranges for parameter search
        min_cluster_size_range = range(5, max_range_cl_size, 1)
        cluster_selection_epsilon = 0.0

        # Store best configuration for each min_cluster_size
        best_configs = {}

        early_stop = False

        # Grid search over min_cluster_size and cluster_selection_epsilon
        total_iterations = len(min_cluster_size_range) * 4  # Approximately 4 epsilon values per min_cluster_size
        current_iteration = 0
        
        for min_cluster_size in min_cluster_size_range:
            cluster_selection_epsilon = 0.0
            while cluster_selection_epsilon <= 1:
                current_iteration += 1
                # Progress logging every 10 iterations or at start
                if current_iteration % 10 == 1 or current_iteration == 1:
                    print(f"  🔄 Clustering progress: {current_iteration}/{total_iterations} iterations (min_cluster_size={min_cluster_size}, epsilon={cluster_selection_epsilon:.3f})")
                
                # Apply HDBSCAN clustering
                clusterer = hdbscan.HDBSCAN(
                    min_cluster_size=min_cluster_size,
                    cluster_selection_epsilon=cluster_selection_epsilon
                )
                labels = clusterer.fit_predict(X_normalized)
                
                # Step 1: Ensure at least one valid cluster (not just outliers)
                if len(set(labels)) > 1:  # Ensure there are at least two clusters (valid clusters)
                    dbcv_score = dbcv.dbcv(X_normalized, labels, check_duplicates=False)
                    
                    # Early stop check (only if enabled)
                    if enable_early_stop and dbcv_score < early_stop_threshold:
                        early_stop = True
                        break
                    
                    if min_cluster_size not in best_configs or dbcv_score > best_configs[min_cluster_size][0]:
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
                    # Compute Euclidean distance between the outlier and each centroid
                    distances = {cluster_id: euclidean_distances([outlier_point], [centroid])[0][0]
                                 for cluster_id, centroid in cluster_centroids.items()}
                    # Find the cluster with the smallest distance (closest centroid)
                    if distances:  # Only proceed if there are clusters
                        nearest_cluster = min(distances, key=distances.get)
                        labels[outlier] = nearest_cluster  # Reassign the outlier to the nearest cluster
                
                    # Repeat Step 3: Recalculate centroids including the newly assigned outliers
                    for cluster_id in set(labels):
                        if cluster_id != -1:  # Skip outliers
                            cluster_points = X_normalized[labels == cluster_id]
                            cluster_centroids[cluster_id] = np.mean(cluster_points, axis=0)
                
                # Repeat Step 4: Reassign outliers to the closest cluster based on Euclidean distance
                for outlier in outliers:
                    outlier_point = X_normalized[outlier]
                    # Compute Euclidean distance between the outlier and each centroid
                    distances = {cluster_id: euclidean_distances([outlier_point], [centroid])[0][0]
                                 for cluster_id, centroid in cluster_centroids.items()}
                    # Find the cluster with the smallest distance (closest centroid)
                    if distances:  # Only proceed if there are clusters
                        nearest_cluster = min(distances, key=distances.get)
                        labels[outlier] = nearest_cluster  # Reassign the outlier to the nearest cluster
                        
                cluster_selection_epsilon += 0.333 #0.1
            if early_stop == True:
                break
                
        # Convert best configurations to a sorted list (top 10 based on DBCV score)
        top_k_configs = sorted(best_configs.values(), reverse=True, key=lambda x: x[0])[:10]

        best_by_fewest_clusters = None

        # Determine the threshold to use for final selection
        final_threshold_value = final_threshold if enable_final_threshold else 0

        for dbcv_score, min_cluster_size, cluster_selection_epsilon, labels in best_configs.values():
            if dbcv_score > final_threshold_value:
                num_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                if best_by_fewest_clusters is None or num_clusters < best_by_fewest_clusters[0]:
                    best_by_fewest_clusters = (
                        num_clusters, dbcv_score, min_cluster_size, cluster_selection_epsilon, labels
                    )

        # Output the best setting with fewest clusters
        analysis_duration = time.time() - analysis_start_time
        print(f"  ✅ Clustering analysis completed in {analysis_duration:.2f}s")
        
        if best_by_fewest_clusters:
            num_clusters, dbcv_score, min_cluster_size, cluster_selection_epsilon, labels = best_by_fewest_clusters
            cluster_dict = {}
            for idx, cluster_id in enumerate(labels):
                if cluster_id != -1:
                    cluster_dict.setdefault(cluster_id, []).append(str(pageVectorsIDs[idx]))

            final_clusters = [members for members in cluster_dict.values()]
            
            print(f"  📈 Best configuration: {num_clusters} clusters, DBCV={dbcv_score:.3f}, min_cluster_size={min_cluster_size}, epsilon={cluster_selection_epsilon:.3f}")
            
            return {
                'success': True,
                'clusters': final_clusters,
                'cluster_info': {
                    'min_cluster_size': min_cluster_size,
                    'cluster_selection_epsilon': cluster_selection_epsilon,
                    'dbcv_score': dbcv_score,
                    'num_clusters': num_clusters,
                    'useful_attributes': useful_attributes
                },
                'message': f"Clustering successful with {num_clusters} clusters and DBCV score: {dbcv_score:.3f}"
            }
        else:
            threshold_msg = f"DBCV > {final_threshold_value}" if enable_final_threshold else "DBCV > 0"
            print(f"  ⚠️  No valid clustering configuration found with {threshold_msg}")
            return {
                'success': False,
                'clusters': [],
                'cluster_info': {},
                'message': f"No clustering configuration found with {threshold_msg}."
            }
            
    except Exception as e:
        return {
            'success': False,
            'clusters': [],
            'cluster_info': {},
            'message': f"Error during clustering analysis: {str(e)}"
        }

# Legacy function for backward compatibility - if you need to run from file
def run_clustering_from_file(filename='computed_styles_20250602192507.json'):
    """
    Legacy function to run clustering from a JSON file.
    """
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
        
        result = perform_clustering_analysis(data)
        
        if result['success']:
            threshold_msg = "≥0 DBCV"
            print(f"\nChosen clustering with fewest clusters ({threshold_msg}):")
            print(f"min_cl_size: {result['cluster_info']['min_cluster_size']}, cl_sel_epsilon: {result['cluster_info']['cluster_selection_epsilon']}, dbcv_score: {result['cluster_info']['dbcv_score']:.3f}, num_clusters: {result['cluster_info']['num_clusters']}")
            print(str(result['clusters']).replace("'", '"'))
        else:
            print(result['message'])
            
        return result
        
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return {
            'success': False,
            'clusters': [],
            'cluster_info': {},
            'message': f"Error: File '{filename}' not found."
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'success': False,
            'clusters': [],
            'cluster_info': {},
            'message': f"Error: {str(e)}"
        }

# If run directly as a script
if __name__ == "__main__":
    run_clustering_from_file()
