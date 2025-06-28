import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from jinja2 import Environment, FileSystemLoader
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from scipy.spatial.distance import cdist

SMOOTH = 1e-6

def collapse_sequence(seq):
    """Collapse consecutive duplicates and repeated patterns."""
    if not seq:
        return []
    
    # First, collapse consecutive duplicates
    collapsed = [seq[0]]
    for c in seq[1:]:
        if c != collapsed[-1]:
            collapsed.append(c)
    
    # Then, collapse repeated patterns
    i = 0
    final = []
    while i < len(collapsed):
        found = False
        for window in range(1, (len(collapsed) - i) // 2 + 1):
            pattern = collapsed[i:i + window]
            repeat = collapsed[i + window:i + 2 * window]
            if pattern == repeat:
                j = i + window
                while collapsed[j:j + window] == pattern:
                    j += window
                final.extend(pattern)
                i = j
                found = True
                break
        if not found:
            final.append(collapsed[i])
            i += 1
    return final

def compute_role_vectors(sites):
    """Compute role vectors for each site using frequency, transitions, and positional information."""
    # Identify all clusters across all sites
    all_clusters = sorted(set(c for seq in sites.values() for c in seq))
    cluster_index = {cid: idx for idx, cid in enumerate(all_clusters)}
    n_clusters = len(all_clusters)
    
    role_vectors = {}
    
    for site, seq in sites.items():
        n = len(seq)
        positions = defaultdict(list)
        transitions = np.zeros((n_clusters, n_clusters), dtype=int)
        freq = Counter(seq)
        
        # Compute positional information
        for idx, c in enumerate(seq):
            positions[c].append(idx / max(n - 1, 1))
        
        # Compute transition matrix
        for a, b in zip(seq, seq[1:]):
            i, j = cluster_index[a], cluster_index[b]
            transitions[i, j] += 1
        
        # Build role vectors for each cluster
        vectors = []
        for cid in all_clusters:
            idx = cluster_index[cid]
            freq_val = freq[cid]
            out_vec = transitions[idx, :]
            in_vec = transitions[:, idx]
            pos_list = positions[cid]
            
            if pos_list:
                mean_pos = np.mean(pos_list)
                std_pos = np.std(pos_list)
                min_pos = np.min(pos_list)
                max_pos = np.max(pos_list)
            else:
                mean_pos = std_pos = min_pos = max_pos = 0.0
            
            role_vec = [freq_val] + list(out_vec) + list(in_vec) + [mean_pos, std_pos, min_pos, max_pos]
            vectors.append(role_vec)
        
        columns = (
            ["Frequency"] +
            [f"Out_{cid}" for cid in all_clusters] +
            [f"In_{cid}" for cid in all_clusters] +
            ["MeanPos", "StdPos", "MinPos", "MaxPos"]
        )
        
        df = pd.DataFrame(vectors, index=all_clusters, columns=columns)
        role_vectors[site] = df
    
    return role_vectors

def compute_site_cosine_similarity(sites):
    """
    Compute cosine similarity matrix for sites data using role vector approach.
    
    Args:
        sites (dict): Dictionary with site identifiers as keys and cluster ID lists as values
                     (keys can be URLs or domain-based identifiers like 'domain_1', 'domain_2')
        
    Returns:
        pandas.DataFrame: Similarity matrix with site names as index and columns (values as percentages 0-100)
    """
    # Return empty DataFrame if no sites data
    if not sites:
        return pd.DataFrame()
    
    # Handle single site case
    if len(sites) == 1:
        site_name = list(sites.keys())[0]
        return pd.DataFrame({site_name: [100.0]}, index=[site_name])

    # ------------------- STEP 1: Identify All Clusters -------------------
    all_clusters = sorted(set(c for seq in sites.values() for c in seq))
    cluster_index = {cid: idx for idx, cid in enumerate(all_clusters)}
    n_clusters = len(all_clusters)

    # ------------------- STEP 2: Compute Role Vectors -------------------
    role_vectors = {}

    for site, seq in sites.items():
        n = len(seq)
        positions = defaultdict(list)
        transitions = np.zeros((n_clusters, n_clusters), dtype=int)
        freq = Counter(seq)

        for idx, c in enumerate(seq):
            positions[c].append(idx / max(n - 1, 1))

        for a, b in zip(seq, seq[1:]):
            i, j = cluster_index[a], cluster_index[b]
            transitions[i, j] += 1

        vectors = []
        for cid in all_clusters:
            idx = cluster_index[cid]
            freq_val = freq[cid]
            out_vec = transitions[idx, :]
            in_vec = transitions[:, idx]
            pos_list = positions[cid]
            if pos_list:
                mean_pos = np.mean(pos_list)
                std_pos = np.std(pos_list)
                min_pos = np.min(pos_list)
                max_pos = np.max(pos_list)
            else:
                mean_pos = std_pos = min_pos = max_pos = 0.0
            role_vec = [freq_val] + list(out_vec) + list(in_vec) + [mean_pos, std_pos, min_pos, max_pos]
            vectors.append(role_vec)

        columns = (
            ["Frequency"] +
            [f"Out_{cid}" for cid in all_clusters] +
            [f"In_{cid}" for cid in all_clusters] +
            ["MeanPos", "StdPos", "MinPos", "MaxPos"]
        )

        df = pd.DataFrame(vectors, index=all_clusters, columns=columns)
        role_vectors[site] = df

    # ------------------- STEP 3: Domain-Level Averages -------------------
    grouped_sites = defaultdict(list)
    for site in sites:
        domain = site.split('_')[0]
        grouped_sites[domain].append(site)

    domain_roles = {}
    for domain, site_list in grouped_sites.items():
        role_sum = None
        for site in site_list:
            df = role_vectors[site]
            if role_sum is None:
                role_sum = df.copy()
            else:
                role_sum += df
        domain_roles[domain] = (role_sum / len(site_list)).fillna(0)

    # ------------------- STEP 4: Domain Similarities -------------------
    domain_names = list(domain_roles.keys())
    domain_avg_vectors = pd.DataFrame({
        domain: df.mean(axis=0) for domain, df in domain_roles.items()
    }).T

    sim_cosine = pd.DataFrame(
        cosine_similarity(domain_avg_vectors),
        index=domain_names,
        columns=domain_names
    ).round(3)

    sim_emd = pd.DataFrame(index=domain_names, columns=domain_names, dtype=float)
    sim_haus = pd.DataFrame(index=domain_names, columns=domain_names, dtype=float)

    for i, d1 in enumerate(domain_names):
        for j, d2 in enumerate(domain_names):
            if i == j:
                sim_emd.loc[d1, d2] = sim_haus.loc[d1, d2] = 1.0
                continue

            a = domain_roles[d1].values
            b = domain_roles[d2].values

            # Handle empty or all-zero role vectors
            if not np.any(np.isfinite(a)) or np.all(a == 0):
                a = np.zeros((1, a.shape[1] if a.ndim > 1 else len(all_clusters)*2+4))
            if not np.any(np.isfinite(b)) or np.all(b == 0):
                b = np.zeros((1, b.shape[1] if b.ndim > 1 else len(all_clusters)*2+4))

            dist = cdist(a, b, metric='cosine')
            dist2 = cdist(b, a, metric='cosine')

            if np.isnan(dist).all():
                sim_emd.loc[d1, d2] = 0.0
                sim_haus.loc[d1, d2] = 0.0
            else:
                sim_emd.loc[d1, d2] = sim_emd.loc[d2, d1] = ((1 - np.nanmean(np.nanmin(dist, axis=1))) + (1 - np.nanmean(np.nanmin(dist2, axis=1)))) / 2
                sim_haus.loc[d1, d2] = sim_haus.loc[d2, d1] = ((1 - np.nanmax(np.nanmin(dist, axis=1))) + (1 - np.nanmax(np.nanmin(dist2, axis=1)))) / 2

    sim_emd = sim_emd.round(3)
    sim_haus = sim_haus.round(3)
    
    # Combined similarity using geometric mean
    sim_combined = (sim_cosine * sim_emd * sim_haus)**(1/3)
    
    # Convert to percentage (0-100) and clip to valid range
    sim_combined = np.clip(sim_combined, 0, 1) * 100
    
    return sim_combined.round(2) 