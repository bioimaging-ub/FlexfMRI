#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 10:29:25 2024

@author: rtudela
"""
from logwrapper import log_execution

# test para aplicar corrección de slice timing en el pre-procesado de resting
# usamos la libreria de Afni
from nipype.interfaces import afni

import os

import warnings
warnings.filterwarnings("ignore")


@log_execution
def afni_slice_timing(path_nii_in, tr, slice_timing_list, path_out):
    """
    https://nipype.readthedocs.io/en/1.1.8/interfaces/generated/interfaces.afni/preprocess.html
    https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTshift.html

    Parameters
    ----------
    nii_in : str
        DESCRIPTION. Ruta completa al nifti para hacer time slicing
    tr : float
        DESCRIPTION. reteirion time (in seconds)
    slice_timing_list : list of floats   
        DESCRIPTION. lista con los tiempos para cada slice
    path_out: str
        DESCRIPTION. Ruta del path donde grabar la imagen procesada con slice timing

    Returns
    -------
    name_out: str
        DESCRIPTION. Nombre del nifti de la imagen procesada por time slicing

    """
    # TR = 2.5
    tshift = afni.TShift()
    tshift.inputs.in_file = path_nii_in
    tshift.inputs.tzero = 0.0
    tshift.inputs.tr = '%.1fs' % tr # en segundos
    
    # ('Fourier' or 'linear' or 'cubic' or 'quintic' or 'heptic')
    # different interpolation methods (see 3dTshift for details) default = Fourier
    # tshift.inputs.interp = 'Fourier' 
    
    # slice_timing: (an existing file name or a list of items which are a float)
    #     time offsets from the volume acquisition onset for each slice
    #     argument: ``-tpattern @%s``
    #     mutually_exclusive: tpattern
    # tshift.inputs.slice_timing = list(np.arange(40) / TR)
    tshift.inputs.slice_timing = slice_timing_list
    
    # tpattern: ('alt+z' or 'altplus' or 'alt+z2' or 'alt-z' or 'altminus'
    #        or 'alt-z2' or 'seq+z' or 'seqplus' or 'seq-z' or 'seqminus' or a
    #        unicode string)
    #     use specified slice time pattern rather than one in header
    #     argument: ``-tpattern %s``
    #     mutually_exclusive: slice_timing
    # tshift.inputs.tpattern = 'alt+z'
    
    # slice_encoding_direction: ('k' or 'k-', nipype default value: k)
    #     Direction in which slice_timing is specified (default: k). If
    #     negative,slice_timing is defined in reverse order, that is, the
    #     first entry corresponds to the slice with the largest index, and the
    #     final entry corresponds to slice index zero. Only in effect when
    #     slice_timing is passed as list, not when it is passed as file.
    # tshift.inputs.slice_encoding_direction = 'k'
    
    path_out_temp = path_nii_in.split('.')[0]+'_slice-timing.nii.gz'
    name_out = path_out_temp.split('/')[-1]
    
    print(f'Slice timing path: {path_out + name_out}')
    if os.path.exists(path_out + name_out):
        os.remove(path_out + name_out)
    
    tshift.inputs.out_file = path_out + name_out
    tshift.inputs.outputtype = 'NIFTI_GZ'
    
    tshift.cmdline
    
    res = tshift.run()
    
   
    tshift.cmdline
    
    return name_out

import json
import numpy as np
import nibabel as nib

# json_file = '/mnt/D6E6B8EFE6B8D0CB/Raul_marte/Projects_2/ICAS_ADNI/tests/sub-ADNI002S0295_ses-m072/func/sub-ADNI002S0295_ses-m072_task-rest_bold.json'
# json_file = '/mnt/D6E6B8EFE6B8D0CB/Raul_marte/Projects_2/ICAS_ADNI/tests/sub-ADNI002S4213_ses-m072/func/sub-ADNI002S4213_ses-m072_task-rest_bold.json'
@log_execution
def return_tr_from_json(json_filename):
    """
    Function to return the repetion time fron the json files from the resting state acquisitions from ADNI   

    Parameters
    ----------
    json_filename : TYPE str
        DESCRIPTION. path for loading the json file of the resting state acquisition to process

    Returns
    -------
    tr : TYPE float
        DESCRIPTION. repetition time from the json file, units should be seconds.

    """    
    with open(json_filename, 'r') as f_in:
        json_in = json.load(f_in)
    
    if 'RepetitionTime' in json_in.keys():
        tr = json_in['RepetitionTime']
    else:
        tr = np.NaN
    
    return tr

@log_execution
def return_parameters_from_json(json_file):
    """
    

    Parameters
    ----------
    json_file : str
        DESCRIPTION. Ruta y nombre al archivo json de donde se lee el tiempo de repetición y el slice timing

    Returns
    -------
    tr : TYPE float
        DESCRIPTION. repetition time from json file 
    slicetiming : list
        DESCRIPTION. list of floats with time time for each slice from the json file (estaran??)

    """
    
    with open(json_file, 'r') as f_in:
        json_in = json.load(f_in)
    
    if 'RepetitionTime' in json_in.keys():
        tr = json_in['RepetitionTime']
    else:
        tr = np.NaN
        
    if 'SliceTiming' in json_in.keys():
        slicetiming = json_in['SliceTiming']
    else:
        slicetiming = np.NaN
    
    return tr, slicetiming    

#%% function to interleave list
def interleave_shift(lst):
    n = len(lst)
    half = n // 2

    # Split evenly if even, bias first half if odd
    if n % 2 == 0:
        first_half = lst[:half]
        second_half = lst[half:]
    else:
        first_half = lst[:half+1]
        second_half = lst[half+1:]

    # Interleave halves
    interleaved = []
    for x, y in zip(first_half, second_half):
        interleaved.extend([x, y])

    # If one half is longer, append the remaining element
    if len(first_half) > len(second_half):
        interleaved.append(first_half[-1])
    elif len(second_half) > len(first_half):
        interleaved.append(second_half[-1])
    
        # lo mismo pero empezando desde slice pares primera es la 1
    shifted = []
    for x, y in zip(second_half, first_half):
        shifted.extend([x, y])

    # If one half is longer, append the remaining element
    if len(second_half) > len(first_half):
        shifted.append(second_half[-1])
    elif len(first_half) > len(second_half):
        shifted.append(first_half[-1])

 
    return interleaved, shifted


## prueba
@log_execution
def aplica_time_slicing(name_path, name_nii_in, name_json_in, path_out, label_interleaved, first_slice):
    """
    

    Parameters
    ----------
    name_path : str
        DESCRIPTION. Path whith the nifti and json files, add / at the end
    name_nii_in : str
        DESCRIPTION. Name with the in nifti to make time slicing
    name_json_in : str
        DESCRIPTION. Name of the json file with the TR and slicing_time info
    path_out: str
        DESCRIPTION. Path to save the time slicing processing
    interleave: bool
        DESCRIPTION. True if the time slicing is interleaved (useful if not reading times from existing json list). FAlse if not interleaved
    first_slice int 0 or 1
        DESCRIPTION. If 1 the interleaed timing is starting in the second slice (number 1 when index starts in 0)

    Returns
    -------
    path_out : str
        DESCRIPTION. path and name with the time slicing image processed

    """
    # path_json_in = '/mnt/D6E6B8EFE6B8D0CB/Raul_marte/Projects_2/ICAS_ADNI/tests/sub-ADNI002S4213_ses-m072/func/'
    # name_json_in = 'sub-ADNI002S4213_ses-m072_task-rest_bold.json'
    # path_json_in = '/mnt/D6E6B8EFE6B8D0CB/Raul_marte/Projects_2/ICAS_ADNI/tests/sub-ADNI002S0295_ses-m072/func/'
    # name_json_in = 'sub-ADNI002S0295_ses-m072_task-rest_bold.json'
    # path_json_in = '/mnt/D6E6B8EFE6B8D0CB/Raul_marte/Projects_2/ICAS_ADNI/tests/sub-ADNI027S5288_ses-m096/func/'
    # name_json_in = 'sub-ADNI027S5288_ses-m096_task-rest_bold.json'
    
    path_json_in = name_path

    if os.path.isfile(path_json_in+name_json_in)==True:    
        tr, slice_timing_list  = return_parameters_from_json(path_json_in+name_json_in)
        tr_label = 'from json'
        slicetime_label = 'from json'
        str_slice_timing_log = 'slice timing correction done'
    else:
        tr = np.NaN
        slice_timing_list = np.NaN

    # path_nii_in = path_json_in+'sub-ADNI002S4213_ses-m072_task-rest_bold.nii.gz'
    # path_nii_in = path_json_in+'sub-ADNI002S0295_ses-m072_task-rest_bold.nii.gz'
    # path_nii_in = path_json_in+'sub-ADNI027S5288_ses-m096_task-rest_bold.nii.gz'
    path_nii_in = path_json_in+name_nii_in #'sub-ADNI002S4213_ses-m072_task-rest_bold.nii.gz'

    nii_in = nib.load(path_nii_in)

    pixdim_in = nii_in.header.get_zooms()

    nvoxels_in = nii_in.header.get_data_shape()



    if np.isnan(tr): # si del json no hay tr lo cogemos de la cabecera del nifti
        tr = pixdim_in[3]
        tr_label = 'from header'
        
    # interleaved = True #initiate variables for testing
    # first_slice=0
    
    # tr=3
    # nvoxels_in = [64, 64, 48 ]
    
    #si no hay lista de time en el slicing lo generamos a partir del nº de slices y el tr
    if np.isnan(slice_timing_list).any():
        slice_timing_list = list((np.arange(0,tr, tr/nvoxels_in[2]))) #el tiempo de adquisición de cada slice
        slicetime_label = 'from header'
        str_slice_timing_log = 'slice timing correction done'
        if label_interleaved == True:
            
            interleaved, shifted = interleave_shift(slice_timing_list)
            
            slice_timing_list = interleaved
            str_slice_timing_log = str_slice_timing_log+' interleaved'

            if first_slice == 1: #empezando desde cero, es decir empieza por slices pares
                
                slice_timing_list = shifted
                str_slice_timing_log = str_slice_timing_log+' shifted'
  
        

    name_out = afni_slice_timing(path_nii_in, tr, slice_timing_list, path_out)
    
    with open(path_out+'log_slice_timing.txt', 'w') as text_file:
        print('tr: {}'.format(tr), file=text_file)
        print('tr_label: {}'.format(tr_label), file=text_file)
        print('slice_timing_list: {}'.format(slice_timing_list), file=text_file)
        print('slice_time_label: {}'.format(slicetime_label), file=text_file)
        print(str_slice_timing_log, file=text_file)
        
    return name_out

#%%
# replicamos función de time slicing, pero corrección si leer archivo jsnon
# generamos los tiempos de slice desde el TR de la cabecera
## prueba
@log_execution
def aplica_time_slicing_from_tr(name_path, name_nii_in, path_out, label_interleaved, first_slice):
    """
    

    Parameters
    ----------
    name_path : str
        DESCRIPTION. Path whith the nifti and json files, add / at the end
    name_nii_in : str
        DESCRIPTION. Name with the in nifti to make time slicing
    path_out: str
        DESCRIPTION. Path to save the time slicing processing
    interleave: bool
        DESCRIPTION. True if the time slicing is interleaved (useful if not reading times from existing json list). FAlse if not interleaved
    first_slice int 0 or 1
        DESCRIPTION. If 1 the interleaed timing is starting in the second slice (number 1 when index starts in 0)

    Returns
    -------
    path_out : str
        DESCRIPTION. path and name with the time slicing image processed

    """
    # path_json_in = '/mnt/D6E6B8EFE6B8D0CB/Raul_marte/Projects_2/ICAS_ADNI/tests/sub-ADNI002S4213_ses-m072/func/'
    # name_json_in = 'sub-ADNI002S4213_ses-m072_task-rest_bold.json'
    # path_json_in = '/mnt/D6E6B8EFE6B8D0CB/Raul_marte/Projects_2/ICAS_ADNI/tests/sub-ADNI002S0295_ses-m072/func/'
    # name_json_in = 'sub-ADNI002S0295_ses-m072_task-rest_bold.json'
    # path_json_in = '/mnt/D6E6B8EFE6B8D0CB/Raul_marte/Projects_2/ICAS_ADNI/tests/sub-ADNI027S5288_ses-m096/func/'
    # name_json_in = 'sub-ADNI027S5288_ses-m096_task-rest_bold.json'
    
    path_json_in = name_path

    # if os.path.isfile(path_json_in+name_json_in)==True:    
    #     tr, slice_timing_list  = return_parameters_from_json(path_json_in+name_json_in)
    #     tr_label = 'from json'
    #     slicetime_label = 'from json'
    # else:
    #     tr = np.NaN
    #     slice_timing_list = np.NaN

    # path_nii_in = path_json_in+'sub-ADNI002S4213_ses-m072_task-rest_bold.nii.gz'
    # path_nii_in = path_json_in+'sub-ADNI002S0295_ses-m072_task-rest_bold.nii.gz'
    # path_nii_in = path_json_in+'sub-ADNI027S5288_ses-m096_task-rest_bold.nii.gz'
    path_nii_in = path_json_in+name_nii_in #'sub-ADNI002S4213_ses-m072_task-rest_bold.nii.gz'

    nii_in = nib.load(path_nii_in)

    pixdim_in = nii_in.header.get_zooms()

    nvoxels_in = nii_in.header.get_data_shape()



    # if np.isnan(tr): # si del json no hay tr lo cogemos de la cabecera del nifti
    #     tr = pixdim_in[3]
    #     tr_label = 'from header'
    
    tr = pixdim_in[3]
    tr_label = 'from header'
    # interleaved = True #initiate variables for testing
    # first_slice=0
    
    # tr=3
    # nvoxels_in = [64, 64, 48 ]
    
    #si no hay lista de time en el slicing lo generamos a partir del nº de slices y el tr
    # if np.isnan(slice_timing_list).any():
    slice_timing_list = list((np.arange(0,tr, tr/nvoxels_in[2]))) #el tiempo de adquisición de cada slice
    slicetime_label = 'from header'
    str_slice_timing_log = 'slice timing correction done'

    if label_interleaved == True:
        interleaved, shifted = interleave_shift(slice_timing_list)
        
        slice_timing_list2 = interleaved
        str_slice_timing_log = str_slice_timing_log+' interleaved'
        
        if first_slice == 1: #empezando desde cero, es decir empieza por slices pares
            
            slice_timing_list2 = shifted
            str_slice_timing_log = str_slice_timing_log+' shifted'
  
    

    name_out = afni_slice_timing(path_nii_in, tr, slice_timing_list2, path_out)
    
    with open(path_out+'log_slice_timing.txt', 'w') as text_file:
        print('tr: {}'.format(tr), file=text_file)
        print('tr_label: {}'.format(tr_label), file=text_file)
        print('slice_timing_list: {}'.format(slice_timing_list2), file=text_file)
        print('slice_time_label: {}'.format(slicetime_label), file=text_file)
        print(str_slice_timing_log, file=text_file)
        
    return name_out

#####################################################################
### fin bloque funciones ############################################
#####################################################################

# %%

if __name__ == "__main__":
    pass
