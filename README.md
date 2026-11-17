# FlexfMRI
*FlexfMRI* is a python-based pipeline to preprocess rs-fMRI images and perform Quality Control (QC) of the preprocessed images.  


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
### [preprocessing](docs/preprocessing)



## Input data structure
The input images must be organized following a BIDS-like directory structure. The pipeline expects the functional images and their associated metadata to be organized by subject and session.

