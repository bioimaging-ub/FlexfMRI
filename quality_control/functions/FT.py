#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 10:14:48 2026

@author: marina
"""
import numpy as np
import os
import nibabel as nib
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks, peak_widths
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def normalize_rows(arr):
    """Normalizes each row of a 2D array to [0, 1]."""
    rmin = np.min(arr, axis=1, keepdims=True)
    rmax = np.max(arr, axis=1, keepdims=True)
    return (arr - rmin) / (rmax - rmin + 1e-8)

# =============================================================================
# Function generate the images for the QC Report
# =============================================================================

def process_subject(subject, session, output_folder, path_filename):
    """
    Process one subject in the given folder for
    correlation and Fourier-based analysis, and generate unified plots.
    """
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)


    ratios = []
    correlations = []
    max_correlation = []

    try:
        # 1. Load NIfTI
        if not os.path.isfile(path_filename):
            print(f"File not found for subject {subject}: {path_filename}")

    
        img = nib.load(path_filename)
        data = img.get_fdata()
        if data.ndim != 4:
            print(f"Data for {subject} does not have 4 dimensions. Skipping.")

        X, Y, Z, T = data.shape

        # 2. Correlation analysis
        all_mean_correlations = []
        correlation_matrices = []

        for t in range(T):
            volume = data[..., t]
            slices_flat = []
            for x_idx in range(volume.shape[0]):
                slice_2d = volume[x_idx, :, :]
                min_val, max_val = slice_2d.min(), slice_2d.max()
                normalized_slice = (slice_2d - min_val) / (max_val - min_val) if max_val > min_val else slice_2d
                slices_flat.append(normalized_slice.ravel())
            slices_flat = np.array(slices_flat)
            corr_matrix = np.corrcoef(slices_flat)
            correlation_matrices.append(corr_matrix)
            mask = ~np.eye(corr_matrix.shape[0], dtype=bool)
            all_mean_correlations.append(np.nanmean(np.abs(corr_matrix[mask])))

        max_correlation.append(np.max(all_mean_correlations))
        overall_mean_corr = np.mean(all_mean_correlations)
        best_idx = np.argmax(all_mean_correlations)
        best_corr_matrix = correlation_matrices[best_idx]
        mean_corr_matrix = np.mean(correlation_matrices, axis=0)

        # 3. Fourier-based analysis
        ft_data = np.fft.fftn(data, axes=(0,1,2))
        ft_data = np.fft.fftshift(ft_data, axes=(0,1,2))
        magnitude_ft = np.abs(ft_data)
        magnitude_ft = (magnitude_ft - magnitude_ft.min()) / (magnitude_ft.max() - magnitude_ft.min() + 1e-8)

        thresholds0 = np.percentile(magnitude_ft, 99.5, axis=(1,2)).reshape(X,1,1,T)
        vals0 = np.sum(np.where(magnitude_ft >= thresholds0, magnitude_ft, 0), axis=(1,2)).T
        thresholds1 = np.percentile(magnitude_ft, 99.5, axis=(0,2)).reshape(1,Y,1,T)
        vals1 = np.sum(np.where(magnitude_ft >= thresholds1, magnitude_ft, 0), axis=(0,2)).T
        thresholds2 = np.percentile(magnitude_ft, 99.5, axis=(0,1)).reshape(1,1,Z,T)
        vals2 = np.sum(np.where(magnitude_ft >= thresholds2, magnitude_ft, 0), axis=(0,1)).T

        norm_vals0 = normalize_rows(vals0)
        norm_vals1 = normalize_rows(vals1)
        norm_vals2 = normalize_rows(vals2)

        mean_profile0 = np.mean(norm_vals0, axis=0)
        mean_profile1 = np.mean(norm_vals1, axis=0)
        mean_profile2 = np.mean(norm_vals2, axis=0)
        smoothed_vals0 = normalize_rows(gaussian_filter1d(mean_profile0, sigma=0.7).reshape(1,-1)).flatten()
        smoothed_vals1 = normalize_rows(gaussian_filter1d(mean_profile1, sigma=0.7).reshape(1,-1)).flatten()
        smoothed_vals2 = normalize_rows(gaussian_filter1d(mean_profile2, sigma=0.7).reshape(1,-1)).flatten()

        peaks_axis0, _ = find_peaks(smoothed_vals0, prominence=0.05)
        peaks_axis1, _ = find_peaks(smoothed_vals1, prominence=0.05)
        peaks_axis2, _ = find_peaks(smoothed_vals2, prominence=0.05)

        peak_ratio_1 = ((smoothed_vals1[peaks_axis1[0]] + smoothed_vals1[peaks_axis1[2]]) / 2) / smoothed_vals1[peaks_axis1[1]] if peaks_axis1.size == 3 else 0
        peak_ratio_2 = ((smoothed_vals1[peaks_axis2[0]] + smoothed_vals1[peaks_axis2[2]]) / 2) / smoothed_vals1[peaks_axis2[1]] if peaks_axis2.size == 3 else 0
        ratios.append((peak_ratio_1 + peak_ratio_2)/2)
        correlations.append(overall_mean_corr)

        # 4. Plotting
        fig = plt.figure(figsize=(20,12))
        fig.suptitle(f"Subject: {subject} - Correlation & Fourier Analysis", fontsize=20, fontweight='bold')
        gs = GridSpec(1, 2, width_ratios=[2,1], figure=fig)
        gs_left = gs[0,0].subgridspec(2,2, wspace=0.25, hspace=0.3)
        ax_corr_1 = fig.add_subplot(gs_left[0,0])
        ax_corr_2 = fig.add_subplot(gs_left[0,1])
        ax_corr_3 = fig.add_subplot(gs_left[1,0])
        ax_corr_4 = fig.add_subplot(gs_left[1,1])
        gs_right = gs[0,1].subgridspec(3,1, hspace=0.4)
        ax_ft_1 = fig.add_subplot(gs_right[0,0])
        ax_ft_2 = fig.add_subplot(gs_right[1,0])
        ax_ft_3 = fig.add_subplot(gs_right[2,0])

        # Correlation plots
        if 32 < Y:
            example_image = data[:,32,:,best_idx]
            im0 = ax_corr_1.imshow(example_image.T, cmap="gray", origin="lower")
            ax_corr_1.set_title(f"Slice [:,32,:] - Time {best_idx}", fontsize=14)
            fig.colorbar(im0, ax=ax_corr_1, fraction=0.046, pad=0.04)
        else:
            ax_corr_1.text(0.5, 0.5, "y=32 out of range", ha='center', va='center')
            ax_corr_1.set_title("Example slice not available")

        im1 = ax_corr_2.imshow(best_corr_matrix, cmap="cividis", origin="lower", aspect="auto")
        ax_corr_2.set_title(f"Correlation matrix - Time {best_idx}", fontsize=14)
        ax_corr_2.set_xlim(5,51)
        ax_corr_2.set_ylim(5,51)
        fig.colorbar(im1, ax=ax_corr_2, fraction=0.046, pad=0.04)

        ax_corr_3.scatter(range(T), all_mean_correlations, marker='o', color='tab:blue', label='Mean Corr')
        ax_corr_3.axhline(y=overall_mean_corr, color='red', linestyle='--', label='Global Mean')
        ax_corr_3.set_xlabel("Time Point", fontsize=14)
        ax_corr_3.set_ylabel("Mean Corr", fontsize=14)
        ax_corr_3.set_ylim(0,0.5)
        ax_corr_3.set_title("Corr Evolution", fontsize=14)
        ax_corr_3.grid(True, linestyle='--', alpha=0.6)
        ax_corr_3.legend()

        im3 = ax_corr_4.imshow(mean_corr_matrix, cmap="cividis", origin="lower", aspect="auto")
        ax_corr_4.set_title("Mean Corr Matrix", fontsize=14)
        ax_corr_4.set_xlim(5,50)
        ax_corr_4.set_ylim(5,50)
        fig.colorbar(im3, ax=ax_corr_4, fraction=0.046, pad=0.04)

        # Fourier plots
        ax_ft_1.plot(smoothed_vals0, color='r', linewidth=3)
        ax_ft_1.scatter(peaks_axis0, smoothed_vals0[peaks_axis0], color='k', s=60, zorder=5)
        ax_ft_1.set_title("Fourier YZ (axis=0)", fontsize=16)
        ax_ft_1.set_ylabel("Norm. Sum", fontsize=14)
        ax_ft_1.grid(True)

        ax_ft_2.plot(smoothed_vals1, color='g', linewidth=3)
        ax_ft_2.scatter(peaks_axis1, smoothed_vals1[peaks_axis1], color='k', s=60, zorder=5)
        ax_ft_2.set_title("Fourier XZ (axis=1)", fontsize=16)
        ax_ft_2.set_ylabel("Norm. Sum", fontsize=14)
        ax_ft_2.grid(True)

        ax_ft_3.plot(smoothed_vals2, color='b', linewidth=3)
        ax_ft_3.scatter(peaks_axis2, smoothed_vals2[peaks_axis2], color='k', s=60, zorder=5)
        ax_ft_3.set_title("Fourier XY (axis=2)", fontsize=16)
        ax_ft_3.set_xlabel("Spatial Index", fontsize=14)
        ax_ft_3.set_ylabel("Norm. Sum", fontsize=14)
        ax_ft_3.grid(True)

        plt.tight_layout(rect=[0,0,1,0.95])
        
        fig_path = os.path.join(output_folder, f"{subject}_{session}_correlation_fourier_analysis_highpass.png")
        fig.savefig(fig_path, bbox_inches='tight', dpi=150)
        print(f"Figura guardada en: {fig_path}")
        
        plt.show()

        print(f"All unified plots generated for subject {subject}.\n")

    except Exception as e:
        print(f"Error processing {subject}: {e}")
            
# =========================================================
# Function extract 99.5% of the percentile 
# =========================================================
def compute_sum_percentile_vectorized(magnitude_ft, axis):
    arr = np.moveaxis(magnitude_ft, axis, 0)
    thresholds = np.percentile(arr, 99.5, axis=(1, 2), keepdims=True)
    mask = arr >= thresholds
    summed = np.sum(arr * mask, axis=(1, 2))
    max_val = np.max(summed)
    return summed / (max_val + 1e-8)

# =========================================================
# Function extract features of the images
# =========================================================
def process_time_series(subject, path_func):

    img = nib.load(path_func)
    data = img.get_fdata()
    time_points = data.shape[-1]

    ratios = []
    widths_all = []

    for t in range(time_points):
        slice_3d = data[..., t]
       
        # FFT 3D y normalización
        ft_3d = np.fft.fftshift(np.fft.fftn(slice_3d))
        magnitude_ft = np.abs(ft_3d)
        magnitude_ft = (magnitude_ft - magnitude_ft.min()) / (magnitude_ft.max() - magnitude_ft.min() + 1e-8)
        
        # Máscara del 99.5 percentil
        threshold = np.percentile(magnitude_ft, 99.5)
        mask = (magnitude_ft >= threshold).astype(np.uint8)
        filtered_magnitude_ft = magnitude_ft * mask
        
        # Sumar perfiles en cada eje
        sum_axis0 = compute_sum_percentile_vectorized(filtered_magnitude_ft, axis=0)
        sum_axis1 = compute_sum_percentile_vectorized(filtered_magnitude_ft, axis=1)
        sum_axis2 = compute_sum_percentile_vectorized(filtered_magnitude_ft, axis=2)
        
        # Suavizado
        sigma = 1.3
        s0 = gaussian_filter1d(sum_axis0, sigma)
        s1 = gaussian_filter1d(sum_axis1, sigma)
        s2 = gaussian_filter1d(sum_axis2, sigma)
        s0 /= (s0.max() + 1e-8)
        s1 /= (s1.max() + 1e-8)
        s2 /= (s2.max() + 1e-8)
        
        # Detección de picos
        peaks0, _ = find_peaks(s0, prominence=0.1)
        peaks1, _ = find_peaks(s1, prominence=0.1)
        peaks2, _ = find_peaks(s2, prominence=0.1)
        
        # Cálculo de ratios y anchos
        if len(peaks1) == 3 and len(peaks2) in (3, 5) or (len(peaks1), len(peaks2)) in [(1,3),(1,5)]:
            # Ratio basado en primeros dos picos relevantes
            if len(peaks1) >= 2:
                r1 = s1[peaks1[0]] / s1[peaks1[1]]
            if len(peaks2) >= 3:
                idx2 = peaks2[1] if len(peaks2)==3 else peaks2[2]
                r2 = s2[peaks2[0]] / s2[idx2]
            ratio = (r1 + r2) / 2 if 'r1' in locals() else (r2 / 2)
            widths = []
            w1 = peak_widths(s1, peaks1, rel_height=0.5)[0]
            w2 = peak_widths(s2, peaks2, rel_height=0.5)[0]
            # seleccionamos anchos correspondientes
            widths.extend([w1[0], w1[1]] if len(peaks1)>=2 else [])
            widths.extend([w2[0], w2[1] if len(peaks2)==3 else w2[2]])
            ratios.append(ratio)
            widths_all.extend(widths)

    return ratios, widths_all, len(peaks0), len(peaks1), len(peaks2)


# =============================================================================
# Function to compute correlation
# =============================================================================

def compute_slice_correlation_stats(path_filename):

    img = nib.load(path_filename)
    data = img.get_fdata()
    if data.ndim != 4:
        raise ValueError(f"Se esperaba 4D, se obtuvo {data.ndim}D")
    X, Y, Z, T = data.shape

    stats = {'YZ': [], 'XZ': [], 'XY': []}
    for axis, key in zip(range(3), stats.keys()):
        per_time = []
        for t in range(T):
            vol = data[..., t]
            # obtener slices normalizadas y aplanadas
            flats = []
            for idx in range(vol.shape[axis]):
                sl = vol[idx, :, :] if axis==0 else (vol[:, idx, :] if axis==1 else vol[:, :, idx])
                mn, mx = sl.min(), sl.max()
                flats.append(((sl - mn)/(mx-mn)) if mx>mn else sl)
            C = np.corrcoef(np.stack([f.ravel() for f in flats]))
            mask = ~np.eye(C.shape[0], dtype=bool)
            per_time.append(np.nanmean(np.abs(C[mask])))
        stats[key] = {
            'mean': np.mean(per_time),
            'std': np.std(per_time)
        }
    return stats
    
   
