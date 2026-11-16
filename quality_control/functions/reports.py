#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 12:02:18 2026

@author: marina
"""


import os
import subprocess
import numpy as np
import nibabel as nib
import re
import matplotlib.pyplot as plt
from PIL import Image
import matplotlib.colors as mcolors
import base64

def get_slices(subject, session,path_anat, path_func, path_filename_qc,path_template, report_dir):
    


    ''' Get slices from the different images and save them as PNG files '''
    
    

    # try changing the subprocess for the python fsl version
    # anat segmentation 
    nii_in = os.path.join(path_anat, subject, session, 'segmentation', f'{subject}_{session}_run-02_T1w_fast_seg_pveseg.nii.gz')
    
    if not os.path.exists(nii_in):
        nii_in = os.path.join(path_anat, subject, session, 'segmentation', f'{subject}_{session}_T1w_fast_seg_pveseg.nii.gz')

        



    png_out= report_dir + '/T1_segmentation.png'
    slicer_run = subprocess.run(['slicer', nii_in, 
                                '-l render2',
                                 '-a', png_out])

    # registration anat to template 
    nii_in = os.path.join(path_anat, subject, session, f'{subject}_{session}_run-02_T1w_seg-brain-hdbet_desc-reg2-template.nii.gz')
    if not os.path.exists(nii_in):
        nii_in = os.path.join(path_anat, subject, session, f'{subject}_{session}_T1w_seg-brain-hdbet_desc-reg2-template.nii.gz')
        

    png_out= report_dir + '/T1_2template.png'
    slicer_run = subprocess.run(['slicer', nii_in, 
                                 '-a', png_out])
    
    # functional BET mask 
    nii_in = os.path.join(path_func, subject, session, f'{subject}_{session}_run-02_task-rest_bold_desc-reference-rs_seg-brain-bet_mask.nii.gz')
    if not os.path.exists(nii_in):
        nii_in = os.path.join(path_func, subject, session, f'{subject}_{session}_task-rest_bold_desc-reference-rs_seg-brain-bet_mask.nii.gz')
    

    png_out= report_dir + '/func_bet_mask.png'
    slicer_run = subprocess.run(['slicer', nii_in, 
                                 '-a', png_out])

    # functional data registered to T1
    nii_in = os.path.join(path_func, subject, session, f'{subject}_{session}_run-02_task-rest_bold_desc-rs-ref-reg-2-t1.nii.gz')
    if not os.path.exists(nii_in):
        nii_in = os.path.join(path_func, subject, session, f'{subject}_{session}_task-rest_bold_desc-rs-ref-reg-2-t1.nii.gz')
        
    png_out= report_dir + '/func_2T1.png'
    slicer_run = subprocess.run(['slicer', nii_in, 
                                 '-a', png_out])
    
    # anatomical data regsitered to template GIF
    create_gif_registration(subject,session, report_dir, path_anat, path_template, num_slices=15, axis=2)

    create_gif_registration2(subject, session, report_dir, path_anat, path_template, num_slices=15, axis=2)

    # functional data registered to anatomical data GIF
    create_gif_segmentation(subject, report_dir, path_anat, num_slices=15)

    # final cleaned data registered to template
    
    #nii_vol0 = path_to_func + '/' + subject + '/' + subject +'_task-rest_bold_desc-ts-mc-cleaned-final-reg-template_vol0.nii.gz'
    #roi_run = subprocess.run(['fslroi', nii_in, nii_vol0, '0 1'])
    
    nii_in = path_filename_qc
    
    
    png_out= report_dir + '/func_final_cleaned_2template.png'
    temp_nii_path = os.path.join(report_dir, 'temp_first_vol.nii.gz')
    extract_ten_volume_and_save(nii_in, temp_nii_path)
    slicer_run = subprocess.run(['slicer', temp_nii_path, '-a', png_out])
    os.remove(temp_nii_path)






def generate_html(subject, session,report_dir, path_to_func):

    ''' Integrate all the images and metrics into an HTML file '''
    
    # Convert image paths to data URLs
    anat_segmentation = image_to_data_url(os.path.join(report_dir, 'T1_segmentation.png'))
    anat_to_template = image_to_data_url(os.path.join(report_dir, 'T1_2template.png'))
    func_bet_mask = image_to_data_url(os.path.join(report_dir, 'func_bet_mask.png'))
    func_to_T1 = image_to_data_url(os.path.join(report_dir, 'func_2T1.png'))
    func_final_cleaned_to_template = image_to_data_url(os.path.join(report_dir, 'func_final_cleaned_2template.png'))
    gif_path_anat = image_to_data_url(os.path.join(report_dir, 'T1_template_slices.gif'))
    gif_path_anat2 = image_to_data_url(os.path.join(report_dir, 'T1_template_slices_overlay.gif'))
    gif_path_seg = image_to_data_url(os.path.join(report_dir, 'T1_segmented_slices.gif'))
    mc_summary = image_to_data_url(os.path.join(report_dir, 'output_mc_summary.png'))
    fourier_img = image_to_data_url(os.path.join(report_dir, f'{subject}_{session}_correlation_fourier_analysis_highpass.png'))

    seg_warning_path = os.path.join(report_dir, 'output_T1seg_Warning.txt')
    mc_warning_path = os.path.join(report_dir, 'output_mc_Warning.txt')

    t1seg_metrics_warning = ''
    mc_metrics_warning = ''

    if os.path.exists(seg_warning_path):
        with open(seg_warning_path, 'r') as file:
            t1seg_metrics_warning = file.read()

    if os.path.exists(mc_warning_path):
        with open(mc_warning_path, 'r') as file:
            mc_metrics_warning = file.read()


    seg_names = ['GM', 'WM', 'CSF', 'Total']
    seg_voxels = []

    pattern = re.compile(r'Sum of GM voxels: (\d+)|Sum of WM voxels: (\d+)|Sum of CSF voxels: (\d+)|Total number of voxels: (\d+)')

    with open(os.path.join(report_dir, 'output_T1seg.txt'), 'r') as file:
        for line in file:
            match = pattern.search(line)
            if match:
                # Extract the numbers from the matched groups, ignoring None values
                numbers = [int(num) for num in match.groups() if num is not None]
                seg_voxels.extend(numbers)



    mc_names = ['Xrot', 'Yrot', 'Zrot', 'Xtrans', 'Ytrans', 'Ztrans', 'FD']
    y_names = ['rad', 'rad', 'rad', 'mm', 'mm', 'mm', 'mm']

    

    # Initialize empty lists to store the values
    max_all = []
    mean_all = []
    std_all = []

    # Regular expression to match the values in the file
    pattern = re.compile(r'MC param \w+ \(max, mean, std\): ([\d\.\-e]+), ([\d\.\-e]+), ([\d\.\-e]+)')

    # Read the file and extract the values
    with open(os.path.join(report_dir, 'output_mc.txt'), 'r') as file:
        for line in file:
            match = pattern.search(line)
            if match:
                max_val, mean_val, std_val = match.groups()
                max_all.append(float(max_val))
                mean_all.append(float(mean_val))
                std_all.append(float(std_val))

    # HTML content construction
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Report for Subject {subject}</title>
        <style>
            body {{ font-family: 'Calibri', sans-serif; }}
            img {{ width: 450px; height: auto; }} /* Adjusted width to be 1.5 times bigger */
            .metrics-text {{ background: #f4f4f4; padding: 10px; border-radius: 5px; }}
            .warning-text {{ color: red; font-size: 24px; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #f2f2f2; }}
            .image-row {{
                    display: flex;
                    justify-content: left;
                    align-items: left;
                    gap: 10px; /* spacing between images */
                }}
            .image-container{{text-align:center;}}
            .image-container img {{width: 100; height: auto;}}

            .image-container h4 {{
                margin-top: 8px;
                font-size: 16px;
                color: #333;
            }}

            .table-row {{
                display: flex;
                justify-content: center;      /* centers both tables */
                align-items: flex-start;
                gap: 70px;                    /* space between tables */
                margin-top: 20px;
                flex: 3
            }}

            .table-container {{
                text-align: center;
                width: 48%;                   /* each table takes ~half of the width */
                flex: 1;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th, td {{
                border: 1px solid #ccc;
                padding: 8px;
            }}

            th {{
                background-color: #f2f2f2;
            }}

            .motion-wrapper {{
                display: flex;
                justify-content: flex-start;
                align-items: flex-start;
                gap: 20px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <h1>Processing Report for Subject {subject}</h1>
        <h2>A. Anatomical Processing</h2>

        <h3>T1-weighted Image to MNI Template</h3>
        <img src="{anat_to_template}" alt="T1 to MNI Template">

        
        <h3>Comparison of T1 slices in GIF format</h3>
        <img src="{gif_path_anat2}" alt="GIF of T1 Slices" style="width: 250px;"> <!-- Adjusted width to be 1.5 times bigger -->
        
        <div class="image-row">
            <div class="image-container">
                <h4>Segmentation of T1-weighted Image</h4>
                <img src="{anat_segmentation}" alt="T1 Segmentation">
            </div>
            
             <div class="image-container">
                <h4>Comparison of Segmented T1 slices in GIF format</h4>
                <img src="{gif_path_seg}" alt="GIF of Segmented T1 Slices" style="width: 675px;"> <!-- Adjusted width to be 1.5 times bigger -->
            </div>
        </div>

        <h2>B. Functional Processing</h2>
        <h3>Functional BET Mask</h3>
        <img src="{func_bet_mask}" alt="Functional BET Mask">
        <h3>Functional Data Registered to T1-weighted Image</h3>
        <img src="{func_to_T1}" alt="Functional Data to T1">
        <h3>Cleaned Functional Data to Template</h3>
        <img src="{func_final_cleaned_to_template}" alt="Cleaned Functional Data to Template">

        <h2>C. Correlation and Fourier Analysis</h2>
        <img src="{fourier_img}" style="width: 45%; height: auto;">



        <h2>D. Motion Correction Summary</h2>
        
        
        <div class ="motion-wrapper">

            <div class="image-container">
                <img src="{mc_summary}" alt="Motion Correction Summary">
            </div>

            <div class="table-row">
                <div class = "table-container">
                    <h4>Motion Correction Metrics</h4>
                    <table>
                        <tr>
                            <th>Parameter</th>
                            <th>Max</th>
                            <th>Mean</th>
                            <th>Std</th>
                            <th>Unit</th>
                        </tr>
                        {"".join([f"<tr><td>{mc_names[i]}</td><td>{max_all[i]}</td><td>{mean_all[i]}</td><td>{std_all[i]}</td><td>{y_names[i]}</td></tr>" for i in range(len(mc_names)-1)])}
                        <tr><th>{mc_names[-1]}</th><th>{max_all[-1]}</th><th>{mean_all[-1]}</th><th>{std_all[-1]}</th><th>{y_names[-1]}</th></tr>
                    </table>
                </div>

                <div class = "table-container">
                    <h4>T1 Segmentation Metrics</h4>
                    <table>
                        <tr>
                            <th>Region</th>
                            <th>Number of Voxels</th>
                        </tr>
                        {"".join([f"<tr><td>{seg_names[i]}</td><td>{seg_voxels[i]}</td><tr>" for i in range(len(seg_names))])}
                    </table>
                </div>
            </div>

        </div>

        {'<h2 class="warning-text">Motion Correction Issues Detected!</h2>' if mc_metrics_warning else ''}
        <pre class="warning-text">{mc_metrics_warning}</pre>

    
        {'<h2 class="warning-text">T1 Segmentation Issues Detected!</h2>' if t1seg_metrics_warning else ''}
        <pre class="warning-text">{t1seg_metrics_warning}</pre>
    </body>
    </html>
    """


    # Writing the HTML file
    html_file_path = os.path.join(report_dir, f'report_{subject}.html')
    # If the file already exists, overwrite it
    with open(html_file_path, 'w') as html_file:
        html_file.write(html_content)

def create_gif_registration(subject, session, report_dir, path_to_anat, path_template,num_slices=10, axis=2):

    ''' Create a GIF showing the registration of the T1-weighted image to the MNI template. The two images are shown side by side. '''

    mni_path = path_template
    t1_path = os.path.join(path_to_anat, subject, session, f'{subject}_{session}_run-02_T1w_seg-brain-hdbet_desc-reg2-template.nii.gz')
    if not os.path.exists(t1_path):
        t1_path = os.path.join(path_to_anat, subject, session, f'{subject}_{session}_T1w_seg-brain-hdbet_desc-reg2-template.nii.gz')


    # Get the data
    mni_data = load_first_volume(mni_path)
    t1_data = load_first_volume(t1_path)

    # Preparing the GIF generation
    slice_indices = np.linspace(0, mni_data.shape[axis]-1, num_slices, dtype=int)
    frames = []

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    for slice_index in slice_indices:
        if axis == 0:  # sagittal
            mni_slice = mni_data[slice_index, :, :]
            t1_slice = t1_data[slice_index, :, :]
        elif axis == 1:  # coronal
            mni_slice = mni_data[:, slice_index, :]
            t1_slice = t1_data[:, slice_index, :]
        else:  # axial
            mni_slice = mni_data[:, :, slice_index]
            t1_slice = t1_data[:, :, slice_index]

        axes[0].clear()
        axes[1].clear()
        axes[0].imshow(mni_slice.T, cmap='gray', origin='lower')
        axes[0].set_title('MNI')
        axes[0].axis('off')
        axes[1].imshow(t1_slice.T, cmap='gray', origin='lower')
        axes[1].set_title('T1')
        axes[1].axis('off')
        fig.suptitle(f'Slice {slice_index}', fontsize=35)
        fig.canvas.draw()

        # Save the current figure state to a PIL image
        image = Image.frombytes('RGBA', fig.canvas.get_width_height(), fig.canvas.buffer_rgba().tobytes())
        frames.append(image.convert('RGB'))

    plt.close(fig)

    # Save the images as a gif file
    gif_path = report_dir + '/T1_template_slices.gif'
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=500, loop=0)

def create_colored_overlay(mni_slice, t1_slice, alpha=0.5):

    ''' Create a colored overlay image with the MNI template in red and the T1-weighted image in green '''

    # Normalize the slices to range [0, 1]
    mni_slice_norm = mni_slice / mni_slice.max() if mni_slice.max() != 0 else mni_slice
    t1_slice_norm = t1_slice / t1_slice.max() if t1_slice.max() != 0 else t1_slice

    # Create RGB images: MNI in red and T1 in green
    mni_rgb = np.zeros((mni_slice.shape[0], mni_slice.shape[1], 3), dtype=np.float32)
    t1_rgb = np.zeros((t1_slice.shape[0], t1_slice.shape[1], 3), dtype=np.float32)

    mni_rgb[..., 0] = mni_slice_norm  # Red channel
    t1_rgb[..., 1] = t1_slice_norm    # Green channel

    # Blend the images
    blended = (1 - alpha) * mni_rgb + alpha * t1_rgb
    blended = (blended * 255).astype(np.uint8)

    return blended

def create_gif_registration2(subject,session, report_dir, path_to_anat, path_template, num_slices=10, axis=2):

    ''' Create a GIF showing the registration of the T1-weighted image to the MNI template. The two images are shown one on top of the other. '''

    mni_path = path_template
    t1_path = os.path.join(path_to_anat, subject, session, f'{subject}_{session}_run-02_T1w_seg-brain-hdbet_desc-reg2-template.nii.gz')
    if not os.path.exists(t1_path):
        t1_path = os.path.join(path_to_anat, subject, session, f'{subject}_{session}_T1w_seg-brain-hdbet_desc-reg2-template.nii.gz')


    # Get the data
    mni_data = load_first_volume(mni_path)
    t1_data = load_first_volume(t1_path)

    # Preparing the GIF generation
    slice_indices = np.linspace(0, mni_data.shape[axis]-1, num_slices, dtype=int)
    frames = []

    for slice_index in slice_indices:
        if axis == 0:  # sagittal
            mni_slice = mni_data[slice_index, :, :]
            t1_slice = t1_data[slice_index, :, :]
        elif axis == 1:  # coronal
            mni_slice = mni_data[:, slice_index, :]
            t1_slice = t1_data[:, slice_index, :]
        else:  # axial
            mni_slice = mni_data[:, :, slice_index]
            t1_slice = t1_data[:, :, slice_index]

        # Create the blended image with transparencies
        blended_image = create_colored_overlay(mni_slice.T, t1_slice.T, alpha=0.5)

        # Rotate the image 180 degrees to match the orientation of the MNI template
        blended_image = np.rot90(blended_image, k=2)

        # Increase the size of the output image
        pil_image = Image.fromarray(blended_image).resize((blended_image.shape[1] * 6, blended_image.shape[0] * 6), Image.NEAREST)
        frames.append(pil_image)

    # Save the images as a gif file
    gif_path = report_dir + '/T1_template_slices_overlay.gif'
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=500, loop=0)

def create_custom_cmap():

    ''' Create a custom colormap with 4 levels for the segmentation: black, orange, green, and vivid green '''

    # Define a colormap with 4 levels: black, orange, green, and vivid green
    vivid_green = '#00FF00'
    colors = ["black", "orange", 'green', vivid_green]
    cmap = mcolors.LinearSegmentedColormap.from_list("custom_cmap", colors, N=4)
    return cmap

def create_gif_segmentation(subject, report_dir, path_to_anat,num_slices=15):

    ''' Create a GIF showing the segmented T1-weighted image in the axial, sagittal, and coronal planes '''

    #path_to_anat = '/pool/home/AD_Multimodal/Estudio_A4/fmri_slicetiming_outputderivatives/anat'
    seg_path = f'{path_to_anat}/{subject}/ses-01/segmentation/{subject}_ses-01_T1w_fast_seg_pveseg.nii.gz'

    if not os.path.exists(seg_path):
        seg_path = f'{path_to_anat}/{subject}/ses-01/segmentation/{subject}_ses-01_run-02_T1w_fast_seg_pveseg.nii.gz'

    seg_data = load_first_volume(seg_path)

    # Create colormap
    cmap = create_custom_cmap()

    # Create a list to store images for the GIF
    images = []

    # Determine starting slice dynamically based on the shape of the segmented image
    start_slice = min(min(seg_data.shape), 20)

    # Iterate over slices of each plane
    slices = np.linspace(start_slice, min(seg_data.shape), num_slices, endpoint=False).astype(int)

    for slice_index in slices:
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        # Plot segmented image for each plane
        axial_img = np.rot90(seg_data[:, :, slice_index])
        sagittal_img = np.rot90(seg_data[:, slice_index, :])
        coronal_img = np.rot90(seg_data[slice_index, :, :])

        axes[0].imshow(coronal_img, cmap=cmap, vmin=0, vmax=3, aspect='auto')
        axes[0].set_title('Coronal plane')
        axes[0].axis('off')

        axes[1].imshow(sagittal_img, cmap=cmap, vmin=0, vmax=3, aspect='auto')
        axes[1].set_title('Sagittal plane')
        axes[1].axis('off')

        axes[2].imshow(axial_img, cmap=cmap, vmin=0, vmax=3, aspect='auto')
        axes[2].set_title('Axial plane')
        axes[2].axis('off')

        fig.suptitle(f'Slice {slice_index}', fontsize=35)

        # Save the current figure as an image in memory
        fig.canvas.draw()
        image = Image.frombytes('RGBA', fig.canvas.get_width_height(), fig.canvas.buffer_rgba().tobytes())
        images.append(image.convert('RGB'))

        plt.close(fig)

    # Save images as a GIF
    gif_path = report_dir + '/T1_segmented_slices.gif'
    images[0].save(gif_path, save_all=True, append_images=images[1:], duration=500, loop=0)
    
    
def extract_ten_volume_and_save(nii_path, output_path):
    ''' Extract the 10th volume of a 4D NIfTI file and save it to a new file '''
    volume = 10
    img = nib.load(nii_path)
    ten_vol_data = img.slicer[..., volume].get_fdata(caching='unchanged')  # Extract the 10th volume
    nib.save(nib.Nifti1Image(ten_vol_data, img.affine), output_path)


def image_to_data_url(image_path):
    """ Convert an image file to a data URL """
    # Determine the image type based on the file extension
    file_type = image_path.split('.')[-1]
    if file_type.lower() == 'png':
        mime_type = 'image/png'
    elif file_type.lower() == 'gif':
        mime_type = 'image/gif'
    else:
        raise ValueError("Unsupported file type")

    with open(image_path, "rb") as img_file:
        return f"data:{mime_type};base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
    
def load_first_volume(nii_path):
    ''' Load the first volume of a 4D NIfTI file '''
    img = nib.load(nii_path)
    if img.ndim == 4:
        volume_fmri = 10
        return img.slicer[..., volume_fmri].get_fdata(caching='unchanged')  # Select 10th volume if 4D
    return img.get_fdata(caching='unchanged')
