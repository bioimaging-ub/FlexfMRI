#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 15:25:27 2026

@author: marina
"""



import os
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import base64
import pandas as pd
import re
import subprocess

from scipy.signal import find_peaks, peak_widths
from scipy.ndimage import gaussian_filter1d
from tqdm import tqdm
from pathlib import Path

from scipy.signal import find_peaks
from matplotlib.gridspec import GridSpec


# GENERAL CONFIGURATION FOR PLOTS
plt.rcParams.update({
    'font.weight': 'bold',
    'axes.labelweight': 'bold',
    'axes.titleweight': 'bold',
    'axes.labelsize': 16,
    'axes.titlesize': 18,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14
})

def create_directory(directory_path):
    
    ''' 
    Create the report  directory if it does not exist 
    
    Parameters:
        - directory_path: the directory path which will be created where all the files created in the QC will be stored
        
    '''
    
    try:
        os.makedirs(directory_path, exist_ok = True)
        print(f'Report directory created: {directory_path}')
        
        
    except FileExistsError:
        print(f'Report directory already exists: {directory_path}')
        
        #Delete warning files if they exist:
        if os.path.exists(os.path.join(directory_path, 'output_T1seg_Warning.txt')):
            os.remove(os.path.join(directory_path, 'output_T1seg_Warning.txt'))
        
        if os.path.exists(os.path.join(directory_path, 'output_mc_Warning.txt')):
            os.remove(os.path.join(directory_path, 'output_mc_Warning.txt'))
            
def load_first_volume(nii_path):
    ''' Load the first volume of a 4D NIfTI file '''
    img = nib.load(nii_path)
    if img.ndim == 4:
        volume_fmri = 10
        return img.slicer[..., volume_fmri].get_fdata(caching='unchanged')  # Select 10th volume if 4D
    return img.get_fdata(caching='unchanged')

def extract_ten_volume_and_save(nii_path, output_path):
    ''' Extract the 10th volume of a 4D NIfTI file and save it to a new file '''
    volume = 10
    img = nib.load(nii_path)
    ten_vol_data = img.slicer[..., volume].get_fdata(caching='unchanged')  # Extract the 10th volume
    nib.save(nib.Nifti1Image(ten_vol_data, img.affine), output_path)
    
def plot_motion_correction(mc_data, mc_names, y_names, report_dir, mean_all):

    ''' Plot the motion correction summary figure '''

    num_tp, num_cols = mc_data.shape
    tp = np.arange(num_tp)
    plt.figure(figsize=(10, 15))
    for i in range(len(mc_names)):
        plt.subplot(len(mc_names), 1, i+1)
        plt.plot(tp, mc_data[:, i])
        plt.title(f'{mc_names[i]}, Mean = {mean_all[i]}', fontsize=10)
        plt.xlabel('Timepoints', fontsize=6)
        plt.ylabel(y_names[i], fontsize=6)
    plt.tight_layout()
    output_fig_path = os.path.join(report_dir, 'output_mc_summary.png')
    plt.savefig(output_fig_path)
    
def QCmetrics(subject, session, report_dir, path_to_func, path_to_anat):

    ''' 
    Calculate the motion correction metrics and segmentation metrics and generate txt files. 
    
    Lastly, plot the motion correction summary figure.
    
    Parameters:
        - Subject: the subject 
        - Session: the session
        - Report dir: the path of the report directory
        - Path_to_func: path of the rs after the preprocessing
        - Path_to_anat:  path of the anat directory in the output_derivatives
        
    Outputs:
        - output_T1seg.txt : segmentation numbers (num of GM voxels, WM voxels and CSF voxels)
        
    '''

    #Segmentation metrics
    nii_segs = []
    list_files = os.listdir(os.path.join(path_to_anat, subject, session, 'segmentation'))
    
    for file in list_files:
        if 'T1w_fast_seg_seg.nii.gz' in file:
            nii_segs.append(file)
            
    nii_in = os.path.join(path_to_anat, subject, session, 'segmentation', nii_segs[-1]) #??????
    
    data = load_first_volume(nii_in)

    # Calculate number of voxels for each segmentation
    num_vox_seg0 = np.sum(data == 1)  # GM voxels
    num_vox_seg1 = np.sum(data == 2)  # WM voxels
    num_vox_seg2 = np.sum(data == 3)  # CSF voxels
    total = num_vox_seg0 + num_vox_seg1 + num_vox_seg2
    
    # Create plain text report
    output_file_path = os.path.join(report_dir, 'output_T1seg.txt')
    with open(output_file_path, 'w') as output_file:
        output_file.write(f"Sum of GM voxels: {num_vox_seg0}\n")
        output_file.write(f"Sum of WM voxels: {num_vox_seg1}\n")
        output_file.write(f"Sum of CSF voxels: {num_vox_seg2}\n")
        output_file.write(f"Total number of voxels: {total}\n")


    #Motion correction metrics
    mc_names = ['Xrot', 'Yrot', 'Zrot', 'Xtrans', 'Ytrans', 'Ztrans', 'FD']
    y_names = ['rad', 'rad', 'rad', 'mm', 'mm', 'mm', 'mm']
    warnings = []
    
    # Summary values of motion correction
    mc_in = os.path.join(path_to_func, subject, session, f'{subject}_{session}_task-rest_bold_desc-mc.nii.gz.par')
    mc_data = np.loadtxt(mc_in)
    max_all = np.max(mc_data, axis=0)
    mean_all = np.mean(mc_data, axis=0)
    std_all = np.std(mc_data, axis=0)

    # ------------- FD CALCULATION -------------
    translations = mc_data[:, 3:6]  # Xtrans, Ytrans, Ztrans
    rotations = mc_data[:, 0:3]     # Xrot, Yrot, Zrot

    head_radius = 50.0
    rotations_mm = rotations * head_radius # Convert rotations from radians to millimeters on the surface of a sphere

    fd = np.zeros(translations.shape[0])
    for i in range(1, translations.shape[0]):
        # Compute differences in translations and rotations
        trans_diff = np.abs(translations[i] - translations[i-1])
        rot_diff = np.abs(rotations_mm[i] - rotations_mm[i-1])
        fd[i] = np.sum(trans_diff) + np.sum(rot_diff)


    mean_fd = np.mean(fd)
    max_fd = np.max(fd)
    std_fd = np.std(fd)

    # Append FD values to the motion correction summary
    mc_data = np.column_stack((mc_data, fd))
    max_all = np.append(max_all, max_fd)
    mean_all = np.append(mean_all, mean_fd)
    std_all = np.append(std_all, std_fd)

    # Round the values
    max_all = np.round(max_all, 4)
    mean_all = np.round(mean_all, 4)
    std_all = np.round(std_all, 4)

    output_file_path = os.path.join(report_dir, 'output_mc.txt')
    with open(output_file_path, 'w') as output_file:
        for i in range(len(mc_names)):
            output_file.write(f"MC param {mc_names[i]} (max, mean, std): {max_all[i]}, {mean_all[i]}, {std_all[i]} {y_names[i]}\n")



    # Plot the motion correction summary figure
    plot_motion_correction(mc_data, mc_names, y_names, report_dir, mean_all)
    
    
    
def get_data_directory(paths_rspreproc, mode = 'output_T1seg.txt'):
    directories = []

    for path in paths_rspreproc:
        
        p = Path(path)

        subject = p.parts[-3]  # sub-B10081264
        session = p.parts[-2]  # ses-01


        path_rs_preproc_base = path.split('sub-')[0]
        
        if subject.startswith('sub-'):
            report_folder = os.path.join(path_rs_preproc_base, subject, session, 'report')
            if os.path.exists(report_folder) and os.path.exists(os.path.join(report_folder, mode)):
                directories.append(os.path.join(report_folder, mode))
                
    return directories

def get_data(file_path, mode = 'output_T1seg.txt'):
    if mode == 'output_T1seg.txt':
        voxel_counts = {
            'GM': 0,
            'WM': 0,
            'CSF': 0,
            'Total': 0
        }
        with open(file_path, 'r') as file:
            for line in file:
                if 'Sum of GM voxels:' in line:
                    voxel_counts['GM'] = int(re.search(r'\d+', line).group())
                elif 'Sum of WM voxels:' in line:
                    voxel_counts['WM'] = int(re.search(r'\d+', line).group())
                elif 'Sum of CSF voxels:' in line:
                    voxel_counts['CSF'] = int(re.search(r'\d+', line).group())
                elif 'Total number of voxels:' in line:
                    voxel_counts['Total'] = int(re.search(r'\d+', line).group())
        return voxel_counts
    elif mode == 'output_mc.txt':
        mc_params = {
            'Xrot_max': 0, 'Xrot_mean': 0, 'Xrot_std': 0,
            'Yrot_max': 0, 'Yrot_mean': 0, 'Yrot_std': 0,
            'Zrot_max': 0, 'Zrot_mean': 0, 'Zrot_std': 0,
            'Xtrans_max': 0, 'Xtrans_mean': 0, 'Xtrans_std': 0,
            'Ytrans_max': 0, 'Ytrans_mean': 0, 'Ytrans_std': 0,
            'Ztrans_max': 0, 'Ztrans_mean': 0, 'Ztrans_std': 0,
            'FD_max': 0, 'FD_mean': 0, 'FD_std': 0
        }

        with open(file_path, 'r') as file:
            for line in file:
                match = re.search(r'MC param (\w+) \(max, mean, std\): ([\d.-]+), ([\d.-]+), ([\d.-]+)', line)
                if match:
                    param, max_val, mean_val, std_val = match.groups()
                    mc_params[f'{param}_max'] = float(max_val)
                    mc_params[f'{param}_mean'] = float(mean_val)
                    mc_params[f'{param}_std'] = float(std_val)
        
        return mc_params
    else:
        return None
    
    
    
def integrate_dataframe(paths_rspreproc):
    # First get the voxel counts
    directories = get_data_directory(paths_rspreproc, mode = 'output_T1seg.txt')
    data = {}

    for directory in directories:
        #Excract the subject id
        subject_id = directory.split('/')[-4]
        session_id = directory.split('/')[-3]
        
        data[subject_id] = get_data(directory, mode = 'output_T1seg.txt')
        data[subject_id]['session'] = session_id
        
        
    df_voxels = pd.DataFrame(data).T
    df_voxels.columns = ['GM_voxels', 'WM_voxels', 'CSF_voxels', 'Total_voxels','session']
    
    # Now get the motion correction parameters
    directories = get_data_directory(paths_rspreproc, mode = 'output_mc.txt')
    data = {}
    
    for directory in directories:
        #Excract the subject id
        subject_id = directory.split('/')[-4]
        data[subject_id] = get_data(directory, mode = 'output_mc.txt')
        
    df_mc = pd.DataFrame(data).T
    df_mc.columns = ['Xrot_max', 'Xrot_mean', 'Xrot_std',
            'Yrot_max', 'Yrot_mean', 'Yrot_std',
            'Zrot_max', 'Zrot_mean', 'Zrot_std',
            'Xtrans_max', 'Xtrans_mean', 'Xtrans_std',
            'Ytrans_max', 'Ytrans_mean', 'Ytrans_std',
            'Ztrans_max', 'Ztrans_mean', 'Ztrans_std',
            'FD_max', 'FD_mean', 'FD_std']

    # Merge the two dataframes
    df = pd.merge(df_voxels, df_mc, left_index=True, right_index=True, how='outer')

    # Make the subject_id a column
    df = df.reset_index()
    df = df.reset_index().rename(columns={'index': 'subject'})
    df.drop('level_0', axis=1, inplace=True)
    
    return df
    