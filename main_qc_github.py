#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 10:35:18 2026

@author: marina

Main code for QC

"""


# =============================================================================
# IMPORTS
# =============================================================================
import sys
sys.path.append('/pool/home/AD_Multimodal/Estudio_A4/codes_marina/qc_reports_final')

from functions.qc_extract_voxels_data import create_directory, QCmetrics, integrate_dataframe
from functions.qQC import compute_automatic_thresholds, reject_subjects
from functions.FT import process_subject, process_time_series, compute_slice_correlation_stats, compute_sum_percentile_vectorized
from functions.reports import *
from functions.review_html import *

import os
import pandas as pd
import numpy as np
import json

# =============================================================================
# CONFIG
# =============================================================================
path_pool = '/pool/home/AD_Multimodal/Estudio_A4'

path_csv = os.path.join(path_pool, 'CSVs/longitudinal/6781_subjects_to_qc_1directory.csv')
path_missing = '/pool/home/AD_Multimodal/Estudio_A4/CSVs/longitudinal/missing_subjects_qc.csv'

path_BIDS = os.path.join(path_pool, '0_A4/A4_BIDS')
path_derivatives = os.path.join(path_BIDS, 'fmri_slicetiming_outputderivatives_v2')

path_template = os.path.join(path_pool, 'templates/MNI152_T1_3.3mm_brain.nii.gz')

path_gwd = '/pool/home/AD_Multimodal/Estudio_A4/codes_marina/qc_reports_final'

os.chdir(os.path.join(path_derivatives,'rs_preproc'))

path_files = os.getcwd()

save = True
save_threshold = True


thres = True

problematic_subjects = None


df_subjects = pd.read_csv(path_csv) 
df_missing = pd.read_csv(path_missing)

thresholds = {"FD_mean": 0.458, "FD_max": 2.599, "GM_lower": 0.171, "GM_upper": 0.312,
                "WM_lower": 0.341, "WM_upper": 0.463, "CSF_lower": 0.31,
                "CSF_upper": 0.402, "Total_lower": 719936, "Total_upper": 1320292}

# =============================================================================
# MAIN PIPELINE
# =============================================================================
def compute_qc_metrics(df_subjects):
    
    paths_rspreproc = df_subjects['rspreproc_path']
    

    # A. EXTRACT QC METRICS: VOXEL AND MOTION DATA
    for row in df_subjects.itertuples():
        subject = row.subject
        session = row.session
        path_func = row.rspreproc_path
        
        path_derivatives = path_func.split('rs_preproc')[0]
        path_to_func = os.path.join(path_derivatives,'rs_preproc')
        path_to_anat = os.path.join(path_derivatives,'anat')
        path_save_qc_outputs = os.path.join(path_to_func, 'qc_outputs')

        
        if os.path.exists(path_func):
            report_dir = os.path.join(path_derivatives,'rs_preproc',subject, session, 'report')
            create_directory(report_dir)
            QCmetrics(subject, session,report_dir, path_to_func, path_to_anat)

        else:
            print(f"Error: Preprocessing for subject '{subject}' not found. Please, check.")
            

            
    # B. MERGE VOXEL AND MOTION DATA FROM THE TXT files saved
    df = integrate_dataframe(paths_rspreproc)
    
    df['GM_voxels_perc'] = df['GM_voxels'] / df['Total_voxels']
    df['WM_voxels_perc'] = df['WM_voxels'] / df['Total_voxels']
    df['CSF_voxels_perc'] = df['CSF_voxels'] / df['Total_voxels']

    # Save the dataframe as a csv
    file_name = 'motion_voxel_data.csv'
    print(df)
    df.to_csv(os.path.join(path_to_func, file_name), index=False)
    df.describe().to_csv(os.path.join(path_to_func, 'motion_voxel_data_summary.csv'))
    
    return df


def run_qQC(df, automatic_thresholds):
    
    if automatic_thresholds:
        thresholds, df_thresholds = compute_automatic_thresholds(df)
        
        
    df_rejections = reject_subjects(df, thresholds)

    # df_subjects = df_subjects.merge(df_rejections[['BID','PASS']], on='BID', how = 'inner').rename(columns={'PASS':'qQC'})
    
    # Save the rejected subjects in a csv file
    if save:
        # path_save_automatic_rejections = os.path.join(path_save_qc_outputs,'automatic_rejections.csv')
        df_rejections[df_rejections['Pass'] == False].to_csv('automatic_rejections.csv', index=False)

    if save_threshold:
        with open('automatic_thresholds.json', 'w') as f:
            json.dump(thresholds, f)
        
            
    return df_rejections
    

def run_FT(df):
    rows = []
    
    for row in df.itertuples():
        
        subject = row.subject
        path_func = row.rspreproc_path
        session = row.session
        path_derivatives = path_func.split('/rs_preproc')[0]
        
        
        # filename_qc = f'{subject}_{session}_task-rest_bold_desc-ts-mc-cleaned-final-reg-template.nii.gz'
  
        output_folder = os.path.join(path_derivatives,'rs_preproc', subject,session,'report')  
        
        print(f"Procesando sujeto: {subject}")
        print(f"Output folder: {output_folder}")
        os.makedirs(output_folder, exist_ok=True)

        try:
            fig_path = os.path.join(output_folder, f"{subject}_{session}_correlation_fourier_analysis_highpass.png")
            if os.path.exists(fig_path):
                continue
            else:
                process_subject(subject,session, output_folder, path_func) #????? I'M HERE
    
                ratios, widths, peaks0, peaks1, peaks2 = process_time_series(subject, path_func)
                corr_stats = compute_slice_correlation_stats(path_func)
                rows.append({
                    'Subject': subject,
                    'n_valid_timepoints': len(ratios),
                    'n_peaks0': peaks0,
                    'n_peaks1': peaks1,
                    'n_peaks2': peaks2,
                    'mean_ratio': np.nanmean(ratios) if ratios else np.nan,
                    'mean_width': np.nanmean(widths) if widths else np.nan,
                    'mean_corr_YZ': corr_stats['YZ']['mean'],
                    'std_corr_YZ': corr_stats['YZ']['std'],
                    'mean_corr_XZ': corr_stats['XZ']['mean'],
                    'std_corr_XZ': corr_stats['XZ']['std'],
                    'mean_corr_XY': corr_stats['XY']['mean'],
                    'std_corr_XY': corr_stats['XY']['std'],
                })
                
        except Exception as e:
            print(f"Error procesando {subject}: {e}")

    # Guardar Excel final
    df = pd.DataFrame(rows)
    out_file = os.path.join(path_derivatives,'rs_preproc', 'feature_excel_with_dispersion_4.xlsx')
    df.to_excel(out_file, index=False)
    print(f"Se guardó el análisis con dispersión en: {out_file}")
    
    return df


def create_reports(df_qQC, path_template):
    
    
    for row in df_qQC.itertuples():
        subject = row.subject
        session = row.session
        path_func = row.rspreproc_path.split('/sub')[0]
        # path_func = '/Users/marina/Library/CloudStorage/OneDrive-UniversitatdeBarcelona/curs_2025_26/technical_report_preprocessing/github/BIDS/fmri_slicetiming_outputderivatives/rs_preproc'
        path_filename_qc = row.rspreproc_path
        
        path_anat = path_func.replace('rs_preproc', 'anat')
        
        if os.path.exists(path_filename_qc):
            report_dir = os.path.join(path_func, subject, session, 'report')
            
            try:

                get_slices(subject, session, path_anat, path_func,path_filename_qc, path_template, report_dir)
                generate_html(subject, session, report_dir, path_func)
                
                print(f'HTMl file created in: {report_dir}')
                
            except:
                print(f"Error: Creating report for subject '{subject}' not found. Please, check.")
                
        else:
             print(f"Error: Preprocessing for subject '{subject}' not found. Please, check.")

# =============================================================================
# FUNCTIONS
# =============================================================================

def main():
    
    # df_subjects = pd.read_csv(path_csv)
    df_subjects = df_subjects.merge(
    df_missing[['subject', 'session']],
    on=['subject', 'session'],
    how='inner'
    )
    
    paths_rspreproc = df_subjects['rspreproc_path']
    
    
    # A. QC METRICS
    df_qcmetrics = compute_qc_metrics(df_subjects)

    
    automatic_thresholds = True
    
    # #B. qQC: Threshold study
    df_rejections = run_qQC(df_qcmetrics,automatic_thresholds)

    
    df_subjects['qQC'] = df_rejections['Pass']

    
    # # # If using directly the csv already saved
    df_rejections = pd.read_csv('automatic_rejections.csv')
    df_subjects['qQC'] = ~df_subjects['subject'].isin(df_rejections['subject'])
    

    df_subjects_qQC_pass = df_subjects[df_subjects['qQC'] == True]

    
    #C. Fourier Transform, feature extraction: highpass
    df_ft = run_FT(df_subjects_qQC_pass)

   
    #D. CREATE REPORTS 
    df_subjects_qQC_pass = df_subjects.copy()
    
    
    create_reports(df_subjects_qQC_pass, path_template)
    
    
    
    #E. CREATE GENERAL HTML FILE
    create_html_file(path_gwd)
    
    # df_qcmetrics = None
    # df_rejections = None
    # df_subjects_qQC_pass = None
    # df_ft = None
     
                 
    return df_qcmetrics, df_rejections, df_subjects_qQC_pass,df_ft
                 
if __name__ == "__main__":
    df_qcmetrics, df_rejections, df_subjects_qQC_pass, df_ft = main()
