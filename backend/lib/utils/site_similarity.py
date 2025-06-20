import numpy as np
import pandas as pd
import itertools
from scipy.optimize import linear_sum_assignment
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

SMOOTH = 1e-6

def clean_sequence(seq):
    """Clean sequence by removing consecutive duplicates and A-B-A patterns."""
    if not seq:
        return []

    cleaned = [seq[0]]
    for i in range(1, len(seq)):
        if seq[i] == cleaned[-1]:
            continue  # Skip consecutive duplicates
        if len(cleaned) >= 2 and seq[i] == cleaned[-2]:
            continue  # Skip A–B–A alternation
        cleaned.append(seq[i])
    return cleaned

def compute_transition_matrix(seq):
    """Compute smoothed transition probability matrix."""
    labels = list(dict.fromkeys(seq))
    k = len(labels)
    idx = {lab: i for i, lab in enumerate(labels)}
    counts = np.zeros((k, k))

    for a, b in zip(seq, seq[1:]):
        if a == b:
            continue  # Skip self-transitions
        i, j = idx[a], idx[b]
        # Symmetric update: both directions count as the same
        counts[i, j] += 1
        counts[j, i] += 1

    counts += SMOOTH
    # Normalize each row
    return counts / counts.sum(axis=1, keepdims=True), labels

def js_divergence(p, q):
    """Jensen-Shannon divergence between probability vectors."""
    p = np.clip(p, SMOOTH, None)
    q = np.clip(q, SMOOTH, None)
    m = 0.5 * (p + q)
    def kl(x, y): return np.sum(x * np.log(x / y))
    return np.sqrt(0.5 * kl(p, m) + 0.5 * kl(q, m))

def align_matrices(P, Q):
    """Align matrices using Hungarian algorithm."""
    k = max(P.shape[0], Q.shape[0])
    def pad(M):
        M2 = np.zeros((k, k))
        M2[:M.shape[0], :M.shape[1]] = M
        for i in range(k):
            if M2[i].sum() == 0:
                M2[i] = np.ones(k) / k
        return M2
    Pp, Qp = pad(P), pad(Q)
    cost = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            cost[i, j] = js_divergence(Pp[i], Qp[j]) + js_divergence(Pp[:, i], Qp[:, j])
    _, col_ind = linear_sum_assignment(cost)
    return col_ind, k

def compare_sites_cosine(P, Q):
    """Compare sites and return only cosine similarity."""
    perm, k = align_matrices(P, Q)
    def pad(M):
        M2 = np.zeros((k, k))
        M2[:M.shape[0], :M.shape[1]] = M
        for i in range(k):
            if M2[i].sum() == 0:
                M2[i] = np.ones(k) / k
        return M2
    Pp = pad(P)
    Qp = pad(Q)
    Qp = Qp[np.ix_(perm, perm)]
    p = Pp.flatten(); q = Qp.flatten()
    p /= p.sum(); q /= q.sum()
    cos = cosine_similarity([p], [q])[0][0]
    return cos

def compute_site_cosine_similarity(sites_data):
    """
    Compute cosine similarity matrix for sites data using the original algorithm.
    
    Args:
        sites_data (dict): Dictionary with site URLs as keys and cluster ID lists as values
        
    Returns:
        dict: Contains similarity matrix data and metadata
    """
    try:
        # Return empty result if no sites data
        if not sites_data:
            return {
                "status": "success",
                "message": "No sites data provided",
                "data": {
                    "matrix": {},
                    "sites": [],
                    "raw_matrix": [],
                    "summary": {
                        "total_sites": 0,
                        "average_similarity": 0,
                        "max_similarity": 0,
                        "min_similarity": 0
                    }
                }
            }

        # Clean sequences using original algorithm logic
        cleaned_sites = {k: clean_sequence(v) for k, v in sites_data.items()}
        
        # Compute transition matrices for sites with valid sequences
        matrices = {}
        labels_map = {}
        
        for name, seq in cleaned_sites.items():
            if len(seq) > 1:  # Need at least 2 elements for transitions
                P, labels = compute_transition_matrix(seq)
                matrices[name] = P
                labels_map[name] = labels

        # Get sites with valid matrices
        names = list(matrices.keys())
        n = len(names)
        
        # Handle case with insufficient data for comparison
        if n == 0:
            return {
                "status": "success", 
                "message": "No sites with sufficient data for transition matrix computation",
                "data": {
                    "matrix": {},
                    "sites": [],
                    "raw_matrix": [],
                    "summary": {
                        "total_sites": 0,
                        "average_similarity": 0,
                        "max_similarity": 0,
                        "min_similarity": 0
                    }
                }
            }
        
        if n == 1:
            # Single site case - return 100% self-similarity
            site_name = names[0]
            return {
                "status": "success",
                "message": f"Single site analysis completed",
                "data": {
                    "matrix": {site_name: {site_name: 100.0}},
                    "sites": names,
                    "raw_matrix": [[100.0]],
                    "summary": {
                        "total_sites": 1,
                        "average_similarity": 100.0,
                        "max_similarity": 100.0,
                        "min_similarity": 100.0
                    }
                }
            }

        # Original algorithm for multiple sites
        dist_cos = np.zeros((n, n))
        
        # Pairwise comparisons using original algorithm
        for i, j in itertools.combinations(range(n), 2):
            P = matrices[names[i]]
            Q = matrices[names[j]]
            cos_sim = compare_sites_cosine(P, Q)
            dist_cos[i, j] = dist_cos[j, i] = cos_sim

        # Convert to similarity percentages (original algorithm approach)
        sim_cos = np.clip(dist_cos, 0, 1) * 100
        
        # Fill diagonal with 100% (self-similarity)
        np.fill_diagonal(sim_cos, 100.0)
        
        # Create DataFrame as in original
        df_cos = pd.DataFrame(sim_cos, index=names, columns=names).round(2)
        
        # Calculate summary statistics
        upper_triangle = sim_cos[np.triu_indices(n, k=1)]
        
        similarity_data = {
            "matrix": df_cos.to_dict('index'),
            "sites": names,
            "raw_matrix": sim_cos.tolist(),
            "summary": {
                "total_sites": n,
                "average_similarity": float(np.mean(upper_triangle)) if len(upper_triangle) > 0 else 100.0,
                "max_similarity": float(np.max(upper_triangle)) if len(upper_triangle) > 0 else 100.0,
                "min_similarity": float(np.min(upper_triangle)) if len(upper_triangle) > 0 else 100.0
            }
        }
        
        return {
            "status": "success",
            "message": f"Cosine similarity computed for {n} sites",
            "data": similarity_data
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"Error computing site similarity: {str(e)}",
            "data": None,
            "traceback": traceback.format_exc()
        } 