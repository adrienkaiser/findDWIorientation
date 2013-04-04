#Find DWI Orientaion

Find the correct orientation of a DWI by testing all possible measurement frames and finding the longest average length of tracts from the full brain tractography

##Workflow

####For each possible measurement frame:

1. Create DWI header (python)
2. Compute DTI and iDWI from DWI (dtiestim)
3. Compute Brain mask from iDWI (MaskComputationWithThresholding)
4. Compute FA from DTI (dtiprocess)
5. Apply Brain mask to FA (ImageMath)
6. Compute WM mask from masked FA (OtsuThresholdSegmentation)
7. Compute Full Brain Tractography from DTI + WM mask (TractographyLabelMapSeeding)
8. Compute average fiber length from Full Brain Tractography (fiberstats)

=&gt; The measurement frame that will have given the longest average fiber length is the right one!

##Output

$ python FindDWIOrientation.py  
&gt; Testing 24 measurement frames...  
&gt; Testing MF 1 : (1,0,0) (0,1,0) (0,0,1)  
&gt; Running: ['dtiestim', '--dwi_image', 'MF1_dwi.nhdr', '--tensor_output', 'MF1_dti.nrrd', '--idwi', 'MF1_idwi.nrrd', '-m', 'wls']  
&gt; Running: ['MaskComputationWithThresholding', 'MF1_idwi.nrrd', '--output', 'brainmask.nrrd', '--autoThreshold', '-e', '0']  
&gt; Running: ['dtiprocess', '--dti_image', 'MF1_dti.nrrd', '-f', 'fa.nrrd']  
&gt; Running: ['ImageMath', 'fa.nrrd', '-outfile', 'famasked.nrrd', '-mul', 'brainmask.nrrd']  
&gt; Running: ['Slicer', '--launch', 'OtsuThresholdSegmentation', 'fa.nrrd', 'mask.nrrd', '--minimumObjectSize', '10', '--brightObjects']  
&gt; Running: ['Slicer', '--launch', 'TractographyLabelMapSeeding', 'MF1_dti.nrrd', 'MF1_tracts.vtk', '--inputroi', 'mask.nrrd']  
&gt; Running: ['fiberstats', '--fiber_file', 'MF1_tracts.vtk']  
&gt; Testing MF 2 : (1,0,0) (0,0,1) (0,1,0)  
&gt; Running: ['dtiestim', '--dwi_image', 'MF2_dwi.nhdr', '--tensor_output', '/MF2_dti.nrrd', '-m', 'wls']  
&gt; Running: ['Slicer', '--launch', 'TractographyLabelMapSeeding', 'MF2_dti.nrrd', 'MF2_tracts.vtk', '--inputroi', 'mask.nrrd']  
&gt; Running: ['fiberstats', '--fiber_file', 'MF2_tracts.vtk']  
&gt; Testing MF 3 : (0,1,0) (1,0,0) (0,0,1)  
&gt; Running: ['dtiestim', '--dwi_image', 'MF3_dwi.nhdr', '--tensor_output', '/MF3_dti.nrrd', '-m', 'wls']  
&gt; Running: ['Slicer', '--launch', 'TractographyLabelMapSeeding', 'MF3_dti.nrrd', 'MF3_tracts.vtk', '--inputroi', 'mask.nrrd']  
&gt; Running: ['fiberstats', '--fiber_file', 'MF3_tracts.vtk']  
...  
&gt; Testing MF 24 : (0,0,-1) (0,-1,0) (-1,0,0)  
&gt; Running: ['dtiestim', '--dwi_image', 'MF24_dwi.nhdr', '--tensor_output', '/MF24_dti.nrrd', '-m', 'wls']  
&gt; Running: ['Slicer', '--launch', 'TractographyLabelMapSeeding', 'MF24_dti.nrrd', 'MF24_tracts.vtk', '--inputroi', 'mask.nrrd']  
&gt; Running: ['fiberstats', '--fiber_file', 'MF24_tracts.vtk']  
&gt; Results:  
&gt; MF 13 = (1,0,0) (0,-1,0) (0,0,1) 	: Average Fiber Length = 1.52304  
&gt; MF 15 = (0,1,0) (-1,0,0) (0,0,1) 	: Average Fiber Length = 0.842786  
...  
&gt; MF 11 = (0,0,-1) (-1,0,0) (0,1,0) 	: Average Fiber Length = 0.624954  
&gt; The measurement frame MF 13 : (1,0,0) (0,-1,0) (0,0,1) (AvgFibLen=1.52304) will be used.  
&gt; Execution time = 842 s = 14 m 2 s  

##Possible measurement frames (24)
(1,0,0) (0,1,0) (0,0,1)  
(1,0,0) (0,0,1) (0,1,0)  
(0,1,0) (1,0,0) (0,0,1)  
(0,1,0) (0,0,1) (1,0,0)  
(0,0,1) (1,0,0) (0,1,0)  
(0,0,1) (0,1,0) (1,0,0)  
(1,0,0) (0,1,0) (0,0,-1)  
(1,0,0) (0,0,1) (0,-1,0)  
(0,1,0) (1,0,0) (0,0,-1)  
(0,1,0) (0,0,1) (-1,0,0)  
(0,0,1) (1,0,0) (0,-1,0)  
(0,0,1) (0,1,0) (-1,0,0)  
(1,0,0) (0,-1,0) (0,0,1)  
(1,0,0) (0,0,-1) (0,1,0)  
(0,1,0) (-1,0,0) (0,0,1)  
(0,1,0) (0,0,-1) (1,0,0)  
(0,0,1) (-1,0,0) (0,1,0)  
(0,0,1) (0,-1,0) (1,0,0)  
(1,0,0) (0,-1,0) (0,0,-1)  
(1,0,0) (0,0,-1) (0,-1,0)  
(0,1,0) (-1,0,0) (0,0,-1)  
(0,1,0) (0,0,-1) (-1,0,0)  
(0,0,1) (-1,0,0) (0,-1,0)  
(0,0,1) (0,-1,0) (-1,0,0)  

