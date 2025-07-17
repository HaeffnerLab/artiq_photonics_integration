import numpy as np
import matplotlib.pyplot as plt
import h5py

def plot_fft_polar(pmt_count, N_r, N_theta):
    num_beta = len(pmt_count)
    # Create beta values
    R = np.zeros((num_beta, num_beta))
    Theta = np.zeros((num_beta, num_beta))
    for i in range(num_beta):
        for j in range(num_beta):
            R[i][j] = (beta_range*(i+1.0)/num_beta)
            Theta[i][j] = (2*np.pi*j/num_beta)
    
    # Perform 2D FFT
    fft_data = np.zeros((N_r, N_theta), dtype=complex)

    for i in range(N_r):
        for j in range(N_theta):
            alpha_r = (i+1.0)/N_r/(beta_range/num_beta)
            alpha_theta = (2*np.pi*j/N_theta)
            fft_data[i][j] = 0
            for k in range(num_beta):
                for l in range(num_beta):
                    factor1 = alpha_r*R[k][l]*np.cos(Theta[k][l])*np.cos(alpha_theta)
                    factor2 = alpha_r*R[k][l]*np.sin(Theta[k][l])*np.sin(alpha_theta)
                    fft_data[i][j] += pmt_count[k][l]*np.exp(-1.0j*(factor1+factor2))
    
    magnitude_spectrum = np.abs(fft_data)
    return magnitude_spectrum

# Parameters
N_r = 100  
N_theta = 100  

# Load data from HDF5 file
with h5py.File('../results/2025-04-06/17/000068257-A6_VdP1mode_Wigner_AWG_Cam.h5', 'r') as f:
    print("Keys in file:", list(f.keys()))
    print("Keys in datasets:", list(f['datasets'].keys()))
    print("Keys in archive:", list(f['archive'].keys()))
    
    # Load the data
    beta_index = f['datasets']['beta_index'][:]
    pmt_counts_avg_thresholded = f['datasets']['pmt_counts_avg_thresholded'][:]
    
    eta=0.134
    Rabi_readout=0.0688*2*np.pi
    beta_time_range_us = 40
    beta_range = eta*beta_time_range_us*Rabi_readout # Total time range in microseconds

# Reshape the data into a square matrix
num_beta = int(np.sqrt(len(pmt_counts_avg_thresholded)))
pmt_count = pmt_counts_avg_thresholded.reshape((num_beta, num_beta))

pmt_count-=np.mean(pmt_count[-num_beta*4:])

# Create beta values for plotting
R = np.zeros((num_beta, num_beta))
Theta = np.zeros((num_beta, num_beta))
for i in range(num_beta):
    for j in range(num_beta):
        R[i][j] = (beta_range*(i+1.0)/num_beta)
        Theta[i][j] = (2*np.pi*j/num_beta)



# Create figure with subplots
fig = plt.figure(figsize=(15, 6))

# Original polar plot
ax1 = fig.add_subplot(121, projection='polar')
c1 = ax1.pcolormesh(Theta, R, pmt_count, cmap='viridis')
plt.colorbar(c1, ax=ax1, label='PMT Counts')
ax1.set_title('Original Data in Polar Coordinates')

# Compute FFT using custom polar FFT
magnitude_spectrum = plot_fft_polar(pmt_count, N_r, N_theta)

# Create frequency axes for polar FFT
k_r = [(i+1.0)/N_r/(beta_range/num_beta)/2/np.pi for i in range(N_r)]
k_theta = [(2*np.pi*j/N_theta) for j in range(N_theta)]

# Plot FFT magnitude spectrum in polar coordinates
ax2 = fig.add_subplot(122, projection='polar')
c2 = ax2.pcolormesh(k_theta, k_r, np.abs(magnitude_spectrum), cmap='viridis')
plt.colorbar(c2, ax=ax2, label='Log Magnitude')
ax2.set_title('FFT in Polar Coordinates')

plt.tight_layout()
plt.show()

# Print some statistics about the data and FFT
print("\nData Statistics:")
print(f"Maximum PMT count: {np.max(pmt_count):.2e}")
print(f"Minimum PMT count: {np.min(pmt_count):.2e}")
print(f"Mean PMT count: {np.mean(pmt_count):.2e}")
print(f"Beta range: {beta_range:.2e}")

print("\nFFT Statistics:")
print(f"Maximum magnitude: {np.max(magnitude_spectrum):.2e}")
print(f"Minimum magnitude: {np.min(magnitude_spectrum):.2e}")
print(f"Mean magnitude: {np.mean(magnitude_spectrum):.2e}") 