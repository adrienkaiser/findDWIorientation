#Find DWI Orientaion

Find the correct orientation of a DWI by testing all possible measurement frames and finding the longest average length of tracts from the full brain tractography

##Workflow

####For each possible measurement frame:

1. Create DWI header
2. Compute DTI from DWI (dtiestim)
3. Compute FA from DTI (dtiprocess)
4. Compute FA mask from FA (OtsuThresholdSegmentation)
5. Compute Full Brain Tractography from DTI + FA mask (TractographyLabelMapSeeding)
6. Compute average fiber length from Full Brain Tractography

=> The measurement frame that will have given the longest average fiber length is the right one!

##Possible measurement frames (48):
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
(-1,0,0) (0,1,0) (0,0,1)
(-1,0,0) (0,0,1) (0,1,0)
(0,-1,0) (1,0,0) (0,0,1)
(0,-1,0) (0,0,1) (1,0,0)
(0,0,-1) (1,0,0) (0,1,0)
(0,0,-1) (0,1,0) (1,0,0)
(-1,0,0) (0,1,0) (0,0,-1)
(-1,0,0) (0,0,1) (0,-1,0)
(0,-1,0) (1,0,0) (0,0,-1)
(0,-1,0) (0,0,1) (-1,0,0)
(0,0,-1) (1,0,0) (0,-1,0)
(0,0,-1) (0,1,0) (-1,0,0)
(-1,0,0) (0,-1,0) (0,0,1)
(-1,0,0) (0,0,-1) (0,1,0)
(0,-1,0) (-1,0,0) (0,0,1)
(0,-1,0) (0,0,-1) (1,0,0)
(0,0,-1) (-1,0,0) (0,1,0)
(0,0,-1) (0,-1,0) (1,0,0)
(-1,0,0) (0,-1,0) (0,0,-1)
(-1,0,0) (0,0,-1) (0,-1,0)
(0,-1,0) (-1,0,0) (0,0,-1)
(0,-1,0) (0,0,-1) (-1,0,0)
(0,0,-1) (-1,0,0) (0,-1,0)
(0,0,-1) (0,-1,0) (-1,0,0)
