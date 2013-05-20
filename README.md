#Find DWI Orientation
Python script for linux:
Find the correct orientation of a DWI by testing all possible measurement frames and finding the longest average length of tracts from the full brain tractography.  
The only file that will be created in the output folder is the final MF corrected nrrd file.  

##Usage
```
USAGE : $ FindDWIOrientation.py -i <DWI> -o <OutputFolder> [Options]  
-h --help                          : Display usage  
-i --inputDWI <string>             : Input DWI image (.nhdr or .nrrd)  
-o --OutputFolder <string>         : Output folder  
-t --TempFolder <string>           : Folder for temporary files (if no TempFolder given, it will be set to the OutputFolder)  
-n --NoBrainmask                   : If the image has not much noise, you do not need the brain mask  
-f --UseFullBrainMaskForTracto     : Compute tractography in the full brain  
-d --DownsampleImage <int>         : Downsample the input image to have faster processing  
-s --FAStartValue <float>          : Start value for tractography  
-p --FAStopValue <float>           : Stopping value for tractography  
-m --MinimumFiberLength <float>    : Minimum fiber length for tractography  
-l --IntegrationStepLength <float> : Integration step length for tractography  
```
`--NoBrainmask`: A brainmask will be computed (step 3) and applied (step 5) to remove noise outside the brain.  
This brainmask computation can fail for some images, so if your image does not have a lot of noise you can use this option.  
`--UseFullBrainMaskForTracto`: If the WM mask computed by OtsuThresholdSegmentation is bad, this option allows you to use the full brain mask computed with MaskComputationWithThresholding as seed for the tractography.  

##Workflow

####For each possible measurement frame:

1. Create DWI header (python)
2. Compute DTI and iDWI from DWI (dtiestim)
3. Compute Brain mask from iDWI (MaskComputationWithThresholding)
4. Compute FA from DTI (dtiprocess)
5. Apply Brain mask to FA (ImageMath)
6. Compute WM mask from masked FA (OtsuThresholdSegmentation)
7. Compute Full Brain Tractography from DTI + WM mask (TractographyLabelMapSeeding)
8. Compute average fiber length and other measures from Full Brain Tractography (fiberstats)
9. Write out plot image of fiber length mesures (matlab)

=&gt; The measurement frame that will have given the longest average fiber length is the right one!

##Output
```
$ python FindDWIOrientation.py  
> Running: ['unu', 'resample', '-i', 'dwi.nhdr', '--size', '128', '64', '64', '7', '-o', 'dwi_Downsampled4.nhdr']  
> Testing 24 measurement frames...  
> Testing MF 1 : (1,0,0) (0,1,0) (0,0,1)  
> Running: ['dtiestim', '--dwi_image', 'MF1_dwi.nhdr', '--tensor_output', 'MF1_dti.nrrd', '--idwi', 'MF1_idwi.nrrd', '-m', 'wls']  
> Running: ['MaskComputationWithThresholding', 'MF1_idwi.nrrd', '--output', 'brainmask.nrrd', '--autoThreshold', '-e', '0']  
> Running: ['dtiprocess', '--dti_image', 'MF1_dti.nrrd', '--fa_output', 'fa.nrrd', '--scalar_float']  
> Running: ['ImageMath', 'fa.nrrd', '-outfile', 'famasked.nrrd', '-mul', 'brainmask.nrrd', '-type', 'float']  
> Running: ['Slicer', '--launcher-no-splash', '--launch', 'OtsuThresholdSegmentation', 'fa.nrrd', 'mask.nrrd', '--minimumObjectSize', '10', '--brightObjects']  
> Running: ['Slicer', '--launcher-no-splash', '--launch', 'TractographyLabelMapSeeding', 'MF1_dti.nrrd', 'MF1_tracts.vtk', '--inputroi', 'mask.nrrd']  
> Running: ['fiberstats', '--fiber_file', 'MF1_tracts.vtk']  
> Testing MF 2 : (1,0,0) (0,0,1) (0,1,0)  
> Running: ['dtiestim', '--dwi_image', 'MF2_dwi.nhdr', '--tensor_output', '/MF2_dti.nrrd', '-m', 'wls']  
> Running: ['Slicer', '--launcher-no-splash', '--launch', 'TractographyLabelMapSeeding', 'MF2_dti.nrrd', 'MF2_tracts.vtk', '--inputroi', 'mask.nrrd']  
> Running: ['fiberstats', '--fiber_file', 'MF2_tracts.vtk']  
> Testing MF 3 : (0,1,0) (1,0,0) (0,0,1)  
> Running: ['dtiestim', '--dwi_image', 'MF3_dwi.nhdr', '--tensor_output', '/MF3_dti.nrrd', '-m', 'wls']  
> Running: ['Slicer', '--launcher-no-splash', '--launch', 'TractographyLabelMapSeeding', 'MF3_dti.nrrd', 'MF3_tracts.vtk', '--inputroi', 'mask.nrrd']  
> Running: ['fiberstats', '--fiber_file', 'MF3_tracts.vtk']  
...  
> Testing MF 24 : (0,0,-1) (0,-1,0) (-1,0,0)  
> Running: ['dtiestim', '--dwi_image', 'MF24_dwi.nhdr', '--tensor_output', '/MF24_dti.nrrd', '-m', 'wls']  
> Running: ['Slicer', '--launcher-no-splash', '--launch', 'TractographyLabelMapSeeding', 'MF24_dti.nrrd', 'MF24_tracts.vtk', '--inputroi', 'mask.nrrd']  
> Running: ['fiberstats', '--fiber_file', 'MF24_tracts.vtk']  
> Results:                              | Average Fiber Length  75 percentile Fiber Length   Average 75 percentile Fiber Length  
> MF 13 = (1,0,0) (0,-1,0) (0,0,1)      | 1.52304               1.98928                      2.17827  
> MF 15 = (0,1,0) (-1,0,0) (0,0,1)      | 0.842786              1.07967                      1.41568  
...  
> MF 11 = (0,0,-1) (-1,0,0) (0,1,0)     | 0.624954              0.719616                     0.89726  
> The measurement frame MF 13 : (1,0,0) (0,-1,0) (0,0,1) (AvgFibLen=1.52304) will be used.  
> Running: ['matlab', '-nodisplay', '-r', "addpath('/path/to/ScriptFolder'); PlotLengthValues('/path/to/OutputFolder')"]  
> The MF corrected DWI header has been written: TempFolder/dwi_MFcorrected.nhdr  
> The MF corrected nrrd DWI has been written: OutputFolder/dwi_MFcorrected.nrrd  
> Execution time = 699 s = 11 m 39 s  
```

<img width="70%" src="http://www.adrienkaiser.fr/FiberLengths.png"/>

##Possible measurement frames (24)
```
1 : (1,0,0)   2 : (1,0,0)   3 : (0,1,0)    4 : (0,1,0)    5 : (0,0,1)    6 : (0,0,1)    7 : (1,0, 0)   8 : (1, 0,0)  
    (0,1,0)       (0,0,1)       (1,0,0)        (0,0,1)        (1,0,0)        (0,1,0)        (0,1, 0)       (0, 0,1)  
    (0,0,1)       (0,1,0)       (0,0,1)        (1,0,0)        (0,1,0)        (1,0,0)        (0,0,-1)       (0,-1,0)  
  
9 : (0,1, 0)  10: ( 0,1,0)  11: (0, 0,1)   12: ( 0,0,1)   13: (1, 0,0)   14: (1,0, 0)   15: ( 0,1,0)   16: (0,1, 0)  
    (1,0, 0)      ( 0,0,1)      (1, 0,0)       ( 0,1,0)       (0,-1,0)       (0,0,-1)       (-1,0,0)       (0,0,-1)  
    (0,0,-1)      (-1,0,0)      (0,-1,0)       (-1,0,0)       (0, 0,1)       (0,1, 0)       ( 0,0,1)       (1,0, 0)  
  
17: ( 0,0,1)  18: (0, 0,1)  19: (1, 0, 0)  20: (1, 0, 0)  21: ( 0,1, 0)  22: ( 0,1, 0)  23: ( 0, 0,1)  24: ( 0, 0,1)  
    (-1,0,0)      (0,-1,0)      (0,-1, 0)      (0, 0,-1)      (-1,0, 0)      ( 0,0,-1)      (-1, 0,0)      ( 0,-1,0)  
    ( 0,1,0)      (1, 0,0)      (0, 0,-1)      (0,-1, 0)      ( 0,0,-1)      (-1,0, 0)      ( 0,-1,0)      (-1, 0,0)  
```
