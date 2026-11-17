# FlexfMRI
*FlexfMRI* is a python-based pipeline to preprocess rs-fMRI images and perform Quality Control (QC) of the preprocessed images. It handles different subjects and different sessions.


## Overview of the repository
FlexfMRI consists of two main steps: Preprocessing and Quality Control.

### The Preprocessing
The preprocessing includes:  
1.   Slice-timing correction
2.   Motion correction
3.   Temporal filtering
4.   Confound regression

### The Quality Control
Quality Control is performed after the preprocessing to ensure the quality of the output images.
The QC includes:
1. Automatic QC: automatic rejection of subjects with gross segmentation errors or excessive subject movement.
2. Visual QC: web-based application to cehck for registration and periodic errors.


## Repository structure
The repository is organized in the following directories:
### [preprocessing](preprocessing)
This folder provides the main script to perform a flexible preprocessing pipeline and the functions folder where the functions used in the main script are saved.
- `main_qc.py`: main script to run
- `config.yaml`: configuration file to set preprocessing options
- `functions / fun_defs.py`: defines core functions for the pipeline
- `functions / fun_defs_slice_timing.py`: defines functions to handle slice-timing corrections
- `functions / logwrapper.py` : manages logging functionality to ensure all processes are porperly logged for debugging and reproducibility

### [quality_control](quality_control)
This folder provides the main script to assess the quality of the images previously preprocessed.  
- `main_qc.py`: main script to run quality control
- `config_qc.yaml` configuration file to set quality control variables
- `functions` directory where all the functions needed for the quality control are saved


## Input data structure
The input images must be organized following a BIDS-like directory structure. The pipeline expects the functional images and their associated metadata to be organized by subject and session.

### Preprocessing input list
The input list must be a .csv file with columns:
- **subject**: sub-BID of the subject (example: sub-B001)
- **session**: session of the subject (example: ses-001)
- **inter_leaved** (True/False): boolean indicating if the acquisition is interleaved (True) or not (False)
- **start_value** (int): number of the time the first slice was acquired (0 if it was at time 0, or TR/2 if it was in the middle) *TR = time repetition

### Quality Control input list
The input list must be a .csv with columns:
- **subject**: sub-BXXX of the subjects
- **session**: ses-XX of the acquisition
- **rspreproc_path**: path of the final image obtained in the preprocessing pipeline (/BIDS_directory/derivatives/rs_preproc/sub-BXXX/ses-XXX/sub-BXXX_ses-XXX_task-rest_bold_desc-ts-mc-cleaned-highpass-final-reg-template.nii.gz)

