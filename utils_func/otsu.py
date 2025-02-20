import numpy as np
def otsu_threshold_manual(data, mid=None):
    """
    Compute the Otsu threshold manually for a given 1D array of data.
    
    Parameters:
        data (array-like): Input 1D array of numerical data.
        
    Returns:
        float: Optimal threshold value.
    """
    # Convert to NumPy array if not already
    data = np.array(data, dtype=np.float32)

    bins_num=512
    
    # Compute histogram and probabilities
    hist, bin_edges = np.histogram(data, bins=bins_num, range=(data.min(), data.max()))
    probabilities = hist / hist.sum()  # Normalize to probabilities

    # Compute bin midpoints
    bin_mids = (bin_edges[:-1] + bin_edges[1:]) / 2  # Midpoints of bins


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

def kapur_entropy_thresholding(data, nbins=256):
    """
    Perform Kapur's entropy thresholding on 1D data.
    
    Parameters:
    -----------
    data : array-like
        Input array of intensity values (e.g., pixel intensities of an image).
    nbins : int
        Number of histogram bins to use. This should be appropriate for the range of data.
    
    Returns:
    --------
    threshold : float
        The threshold value that maximizes the entropy criterion.
    """
    # Compute histogram and bin edges
    hist, bin_edges = np.histogram(data, bins=nbins, range=(np.min(data), np.max(data)))
    # Convert histogram to probability distribution
    hist = hist.astype(float)
    p = hist / hist.sum()

    # Compute cumulative sums
    cdf = np.cumsum(p)
    # To avoid division by zero, ensure no zero probabilities in denominators
    # We'll handle cases where cdf[i] = 0 or 1 by skipping invalid thresholds.
    
    # Precompute partial sums for efficiency
    # We will use log with a small epsilon to avoid log(0)
    eps = 1e-12
    p_log_p = p * np.log(p + eps)  # p*log(p)

    # We'll try every bin as a potential threshold.
    # Threshold t separates classes into [0, t] and [t+1, end]
    max_entropy = -np.inf
    optimal_threshold = None
    
    for t in range(nbins - 1):
        # Background class: [0, t]
        # Foreground class: [t+1, nbins-1]
        
        # Probability of background class
        pb = cdf[t]
        # Probability of foreground class
        pf = 1 - pb
        
        # If pb = 0 or pf = 0, this threshold can't split data meaningfully
        if pb < eps or pf < eps:
            continue
        
        # Background entropy
        # Sum over [0, t]: p[i]/pb * log(p[i]/pb)
        # This can be written as: (sum of p[i]*log(p[i]))/pb - log(pb)
        background_entropy = (p_log_p[:t+1].sum() / pb) - np.log(pb + eps)
        
        # Foreground entropy
        # Sum over [t+1, end]: p[i]/pf * log(p[i]/pf)
        foreground_entropy = (p_log_p[t+1:].sum() / pf) - np.log(pf + eps)
        
        total_entropy = background_entropy + foreground_entropy
        
        # Update max entropy and threshold
        if total_entropy > max_entropy:
            max_entropy = total_entropy
            # The threshold value will be the midpoint of the bin edges at t and t+1
            # because t is an index in histogram bins.
            threshold = 0.5 * (bin_edges[t] + bin_edges[t+1])
            optimal_threshold = threshold
    
    return optimal_threshold