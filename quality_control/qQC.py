#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 15:33:24 2026

@author: marina
"""
import numpy as np
import pandas as pd

def threshold_qc(df,parameter,times=3):
    mean_param = df[f'{parameter}'].tolist()
    threshold_param_plus = np.mean(mean_param) + times*np.std(mean_param)
    threshold_param_minus = np.mean(mean_param) - times*np.std(mean_param)
    
    return mean_param, threshold_param_plus, threshold_param_minus


def compute_automatic_thresholds(df_motion_voxel_data):

    thresholds = {}

    mean_fd, fd_threshold, _ = threshold_qc(df_motion_voxel_data, 'FD_mean')
    mean_fdmax, fdmax_threshold, _ = threshold_qc(df_motion_voxel_data, 'FD_max')

    thresholds['FD_mean'] = fd_threshold
    thresholds['FD_max'] = fdmax_threshold

    threshold_rows = [
        {
            'Parameter': 'FD_mean',
            'Mean': mean_fd,
            'Lower_threshold': fd_threshold,
            'Upper_threshold': np.nan
        },
        {
            'Parameter': 'FD_max',
            'Mean': mean_fdmax,
            'Lower_threshold': np.nan,
            'Upper_threshold': fdmax_threshold
        }
    ]

    tissue_params = ['GM', 'WM', 'CSF', 'Total_voxels']

    for param in tissue_params:

        if param != 'Total_voxels':
            col = f'{param}_voxels_perc'
            key = param
        else:
            col = param
            key = 'Total'

        mean_val, upper_thr, lower_thr = threshold_qc(
            df_motion_voxel_data,
            col
        )

        thresholds[f'{key}_lower'] = lower_thr
        thresholds[f'{key}_upper'] = upper_thr

        threshold_rows.append({
            'Parameter': col,
            'Mean': mean_val,
            'Lower_threshold': lower_thr,
            'Upper_threshold': upper_thr
        })

    df_thresholds = pd.DataFrame(threshold_rows)

    return thresholds, df_thresholds

    
def reject_subjects(df_motion_voxel_data, thresholds):

    subjects = df_motion_voxel_data['subject']

    print(df_motion_voxel_data)
    
    tissue_params = ['GM', 'WM', 'CSF', 'Total']
    # -----------------------------
    # Evaluate subjects
    # -----------------------------
    results = []

    for row in df_motion_voxel_data.itertuples():
        subject = row.subject
        session = row.session
        
        df_sub = df_motion_voxel_data[
            df_motion_voxel_data['subject'] == subject
        ]

        row = {'subject': subject,
               'session': session}

        # FD checks
        row['FD_Pass'] = not np.any(
            df_sub['FD_mean'] > thresholds['FD_mean']
        )

        row['FD_max_Pass'] = not np.any(
            df_sub['FD_max'] > thresholds['FD_max']
        )
        
        
        # Tissue checks
        for param in tissue_params:
            print(param)
            
            if param in ['GM', 'WM', 'CSF']:
                values = df_sub[f'{param}_voxels_perc']
            else:
                values = df_sub[f'{param}_voxels']




            row[f'{param}_lower_Pass'] = not np.any(
                values < thresholds[f'{param}_lower']
            )

            row[f'{param}_upper_Pass'] = not np.any(
                values > thresholds[f'{param}_upper']
            )

        results.append(row)

    df_rejections = pd.DataFrame(results)

    # Overall pass
    pass_cols = [c for c in df_rejections.columns if c.endswith('_Pass')]

    df_rejections['Pass'] = df_rejections[pass_cols].all(axis=1)

    return df_rejections