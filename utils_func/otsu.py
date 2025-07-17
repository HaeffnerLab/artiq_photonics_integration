"""
Thresholding algorithms for image processing and data analysis.
This module provides implementations of Otsu's method and Kapur's entropy thresholding
for finding optimal threshold values in data distributions.
"""

from typing import Optional, Union, List
import numpy as np
import numpy.typing as npt


def otsu_threshold_manual(data: Union[List[float], npt.ArrayLike], mid: Optional[float] = None) -> float:
    """
    Compute the Otsu threshold manually for a given 1D array of data.
    
    Otsu's method finds the threshold that maximizes the inter-class variance
    between two classes formed by the threshold.
    
    Parameters:
    -----------
    data : array-like
        Input 1D array of numerical data.
    mid : float, optional
        Midpoint value for threshold calculation (not used in current implementation).
        
    Returns:
    --------
    float
        Optimal threshold value that maximizes inter-class variance.
        
    Notes:
    ------
    - The function uses 512 bins for histogram calculation
    - Handles edge cases where probabilities sum to zero
    """
    # Convert to NumPy array if not already
    data = np.array(data, dtype=np.float32)
    
    # Number of bins for histogram
    bins_num = 512
    
    # Compute histogram and probabilities
    hist, bin_edges = np.histogram(data, bins=bins_num, range=(data.min(), data.max()))
    probabilities = hist / hist.sum()  # Normalize to probabilities
    
    # Compute bin midpoints
    bin_mids = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # Initialize variables for tracking the optimal threshold
    max_variance = 0
    optimal_threshold = 0
    
    # Iterate over possible thresholds
    for threshold in bin_mids:
        # Class 1 (below threshold)
        weight1 = probabilities[bin_mids <= threshold].sum()
        if weight1 == 0:  # Avoid division by zero
            continue
        mean1 = (bin_mids[bin_mids <= threshold] * probabilities[bin_mids <= threshold]).sum() / weight1
        
        # Class 2 (above threshold)
        weight2 = probabilities[bin_mids > threshold].sum()
        if weight2 == 0:  # Avoid division by zero
            continue
        mean2 = (bin_mids[bin_mids > threshold] * probabilities[bin_mids > threshold]).sum() / weight2
        
        # Inter-class variance
        variance_between = weight1 * weight2 * (mean1 - mean2) ** 2
        
        # Update the maximum variance and threshold
        if variance_between > max_variance:
            max_variance = variance_between
            optimal_threshold = threshold
    
    return optimal_threshold


def kapur_entropy_thresholding(data: Union[List[float], npt.ArrayLike], nbins: int = 256) -> Optional[float]:
    """
    Perform Kapur's entropy thresholding on 1D data.
    
    Kapur's method finds the threshold that maximizes the sum of entropies
    of the two classes formed by the threshold.
    
    Parameters:
    -----------
    data : array-like
        Input array of intensity values (e.g., pixel intensities of an image).
    nbins : int, optional
        Number of histogram bins to use. Default is 256.
        
    Returns:
    --------
    float or None
        The threshold value that maximizes the entropy criterion.
        Returns None if no valid threshold is found.
        
    Notes:
    ------
    - Uses a small epsilon (1e-12) to avoid numerical issues with log(0)
    - Handles edge cases where probabilities are too close to zero
    """
    # Convert to NumPy array if not already
    data = np.array(data, dtype=np.float32)
    
    # Compute histogram and bin edges
    hist, bin_edges = np.histogram(data, bins=nbins, range=(np.min(data), np.max(data)))
    
    # Convert histogram to probability distribution
    hist = hist.astype(float)
    p = hist / hist.sum()
    
    # Compute cumulative sums
    cdf = np.cumsum(p)
    
    # Small epsilon to avoid numerical issues
    eps = 1e-12
    
    # Precompute partial sums for efficiency
    p_log_p = p * np.log(p + eps)  # p*log(p)
    
    # Initialize variables for finding optimal threshold
    max_entropy = -np.inf
    optimal_threshold = None
    
    # Try every bin as a potential threshold
    for t in range(nbins - 1):
        # Background class: [0, t]
        # Foreground class: [t+1, nbins-1]
        
        # Probability of background and foreground classes
        pb = cdf[t]
        pf = 1 - pb
        
        # Skip invalid thresholds
        if pb < eps or pf < eps:
            continue
        
        # Calculate background entropy
        background_entropy = (p_log_p[:t+1].sum() / pb) - np.log(pb + eps)
        
        # Calculate foreground entropy
        foreground_entropy = (p_log_p[t+1:].sum() / pf) - np.log(pf + eps)
        
        # Total entropy is the sum of both class entropies
        total_entropy = background_entropy + foreground_entropy
        
        # Update max entropy and threshold
        if total_entropy > max_entropy:
            max_entropy = total_entropy
            # Use midpoint of bin edges for threshold value
            optimal_threshold = 0.5 * (bin_edges[t] + bin_edges[t+1])
    
    return optimal_threshold