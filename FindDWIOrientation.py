#!/usr/bin/python

import os # .access .path .rename .remove .mkdir
import sys # .exit .argv
import subprocess # .call
import time # .time()
import shutil # .copyfile()

############################################
#             Args & Usage                 #
############################################
ComputeBrainmask=1
OutputFolder=''
if len(sys.argv) < 3 : # sys.argv[0] = name of the script
  print '> Not enough arguments given!'
  print '> Usage (in this exact order): $ python ./findDWIOrientation.py DWIfile TempFolder [<OutputFolder>] [--NoBrainmask] [> <LogFile>]'
  print '> If no OutputFolder given, it will be set to the TempFolder.'
  print '> EXIT'
  sys.exit(0)
else:
  DWI=sys.argv[1]
  TempFolder = sys.argv[2]
  # 4 or more args
  if len(sys.argv) >= 4 :
    if sys.argv[3] == '--NoBrainmask' :
      ComputeBrainmask=0
    else :
      OutputFolder = sys.argv[3]
    # 5 args
    if len(sys.argv) > 4 :
      if sys.argv[4] == '--NoBrainmask' :
        ComputeBrainmask=0
      else :
        OutputFolder = sys.argv[4]

if OutputFolder == '' :
  OutputFolder = TempFolder

# DWI
# /NIRAL/work/akaiser/Networking/NFG/nfg_1.1.1/generated_collections/130325112527/DWI/dwi.nhdr  => !! --NoBrainmask
# /rodent/SherylMoy/processing/dwi.nhdr
# /rodent/FAS_sulik/DTI2013/Processing/N50320/1-Converted/N50320_dwi.nhdr
# /rodent/FAS_sulik/DTI08/PN45ChallengeGrant/4K-02/4K-02_dwi.nhdr
# /home/akaiser/Networking/from_Utah/Data/b1000.nhdr
# TempFolder
# /NIRAL/work/akaiser/MF_FAS_Sulik2

############################################
#              Check variables             #
############################################
def CheckFolder (folder):
  if os.path.isdir(folder):
    if not os.access(folder, os.W_OK):
      print '> The given output folder is not writable:',folder
      print '> ABORT'
      sys.exit(1)
  else:
    print '> The given output folder does not exist, it will be created:',folder
    if not os.access(os.path.dirname(folder), os.W_OK):
      print '> The parent of the given output folder is not writable:',os.path.dirname(folder)
      print '> ABORT'
      sys.exit(1)
    os.mkdir(folder)

if not os.access(DWI, os.R_OK):
  print '> The given DWI is not readable:',DWI
  print '> ABORT'
  sys.exit(1)

CheckFolder(TempFolder)
CheckFolder(OutputFolder)

############################################
#       Define and check tools             #
############################################
def CheckTool(TestCmd):
  ExceptionCaught=0
  try:
    ExitCode = subprocess.call( TestCmd, stdout=open(os.devnull, 'w') , stderr=open(os.devnull, 'w') ) # call command with no output
  except:
    ExceptionCaught=1
  if ExceptionCaught or ExitCode!=0 :
    print '> Error in:',TestCmd
    print '> ABORT'
    sys.exit(1)

dtiestimCmd=['/tools/bin_linux64/dtiestim']
CheckTool(dtiestimCmd + ['--help'])
BrainMaskCmd=['/home/akaiser/MaskComputationWithThresholding-build/MaskComputationWithThresholding'] # ['/rodent/bin_linux64/toolsMarch2013/MaskComputationWithThresholding']
CheckTool(BrainMaskCmd + ['--help'])
dtiprocessCmd=['/tools/bin_linux64/dtiprocess']
CheckTool(dtiprocessCmd + ['--help'])
ImageMathCmd=['/tools/bin_linux64/ImageMath']
CheckTool(ImageMathCmd + ['-help'])
OtsuThresholdCmd=['/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/Slicer', '--launch', '/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/lib/Slicer-4.2/cli-modules/OtsuThresholdSegmentation']
CheckTool(OtsuThresholdCmd + ['--help'])
tractoCmd=['/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/Slicer', '--launch', '/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/lib/Slicer-4.2/cli-modules/TractographyLabelMapSeeding']
CheckTool(tractoCmd + ['--help'])
fiberstatsCmd=['/NIRAL/work/akaiser/Projects/dtiprocess-build/bin/fiberstats']
CheckTool(fiberstatsCmd + ['--help'])
MatlabCmd=['/tools/Matlab2011a/bin/matlab']
CheckTool(MatlabCmd + ['-e']) # -e = env variables # -help returns 1

############################################
# Compute avg fib len for all possible MFs #
############################################

## Function to execute an external command with NO output+ test exit code
def ExecuteCommand (Command):
  print '> Running:',Command
  if subprocess.call( Command, stdout=open(os.devnull, 'w') , stderr=open(os.devnull, 'w') ) !=0 :
    print '> Error executing command'
    print '> ABORT'
    sys.exit(1)

## Write Measurement Frames in a table
MFTable=[]
triples=['(X,0,0)','(0,X,0)','(0,0,X)']
doubles=[1,-1]
for XYZ in [ (X,Y,Z) for X in [1] for Y in doubles for Z in doubles ]: # X is only '1': remove doubles: opposed matrices (multiplied by -1)
  for XYZtriple in [ (Xtriple,Ytriple,Ztriple) for Xtriple in triples for Ytriple in triples for Ztriple in triples ] :
    if XYZtriple[1] != XYZtriple[0] and XYZtriple[2] != XYZtriple[1] and XYZtriple[2] != XYZtriple[0]: # then OK
      MF = XYZtriple[0].replace('X',str(XYZ[0])) + ' ' + XYZtriple[1].replace('X',str(XYZ[1])) + ' ' + XYZtriple[2].replace('X',str(XYZ[2]))
      MFTable.append(MF)

## Compute Avg Fiber Length for all possible MFs
time1=time.time()
AvgFibLenTupleTable=[] # each element of the table is [MF,AvgFibLen]
print '> Testing',len(MFTable),'measurement frames...'
for MF in MFTable:
  MFindex=len(AvgFibLenTupleTable) + 1 # because values appended: size = index
  # Display Measurement Frame
  print '> Testing MF', MFindex, ':', MF

  # Update DWI header
  MFDWI = TempFolder + '/MF' + str(MFindex) + '_dwi.nhdr'
  if not os.path.isfile(MFDWI): # NO auto overwrite => if willing to overwrite, rm files
    MFDWIfile = open(MFDWI,'w')
    for line in open(DWI): # read all lines and replace line containing 'measurement frame' by the new MF
      if 'measurement frame' in line :
        MFDWIfile.write('measurement frame: ' + MF + '\n')
      elif 'data file' in line : # if not full path (not begin by '/'), need to give the full path to the date file(s)
        DataFile = line.split(' ')[2]
        if DataFile[0] != '/': # not full path
          NewDataFile = os.path.abspath(os.path.dirname(DWI) + '/' + DataFile)
        else: # full path: keep as is
          NewDataFile = DataFile
        MFDWIfile.write( line.replace(DataFile,NewDataFile) )
      else :
        MFDWIfile.write(line)
    MFDWIfile.close()

  # Compute DTI and iDWI
  DTI = TempFolder + '/MF' + str(MFindex) + '_dti.nrrd'
  iDWI = TempFolder + '/MF' + str(MFindex) + '_idwi.nrrd'
  ComputeDTICmdTable = dtiestimCmd + ['--dwi_image', MFDWI, '--tensor_output', DTI, '--idwi', iDWI, '-m', 'wls']
  if not os.path.isfile(DTI): # NO auto overwrite => if willing to overwrite, rm files
    ExecuteCommand(ComputeDTICmdTable)

  if ComputeBrainmask :
    # Compute brain mask # !! Brain mask needs to be computed only once because same for all MFs
    BrainMask = TempFolder + '/brainmask.nrrd'
    ComputeBrainMaskCmdTable = BrainMaskCmd + [iDWI, '--output', BrainMask, '--autoThreshold', '-e', '0'] # -e 0 : 0 erosion
    if not os.path.isfile(BrainMask): # NO auto overwrite => if willing to overwrite, rm files
      ExecuteCommand(ComputeBrainMaskCmdTable)

  # Compute FA # !! Fa needs to be computed only once because same for all MFs
  FA = TempFolder + '/fa.nrrd'
  ComputeFACmdTable = dtiprocessCmd + ['--dti_image', DTI, '--fa_output', FA, '--scalar_float']
  if not os.path.isfile(FA): # NO auto overwrite => if willing to overwrite, rm files
    ExecuteCommand(ComputeFACmdTable)

  if ComputeBrainmask :
    # Apply BrainMask to FA # !! Fa needs to be computed only once because same for all MFs
    FAmasked = TempFolder + '/famasked.nrrd'
    AplpyMasktoFACmdTable = ImageMathCmd + [FA, '-outfile', FAmasked, '-mul', BrainMask]
    if not os.path.isfile(FAmasked): # NO auto overwrite => if willing to overwrite, rm files
      ExecuteCommand(AplpyMasktoFACmdTable)
  else :
    FAmasked = FA

  # Compute mask by OTSU thresholding FA # !! Mask needs to be computed only once because same for all MFs
  Mask = TempFolder + '/mask.nrrd'
  ComputeMaskCmdTable = OtsuThresholdCmd + [FAmasked, Mask, '--minimumObjectSize', '10', '--brightObjects'] # brightObjects= bright = fa = 1 # --minimumObjectSize 10 => to avoid 1-voxel artefacts
  if not os.path.isfile(Mask): # NO auto overwrite => if willing to overwrite, rm files
    ExecuteCommand(ComputeMaskCmdTable)

  # Compute Tractography
  Tracts = TempFolder + '/MF' + str(MFindex) + '_tracts.vtk'
  ComputeTractsCmdTable = tractoCmd + [DTI, Tracts, '--inputroi', Mask] # if 'Mask' contains several labels: By default, the seeding region is the label 1
  if not os.path.isfile(Tracts): # NO auto overwrite => if willing to overwrite, rm files
    ExecuteCommand(ComputeTractsCmdTable)

  # Compute Average Fiber Length
  FiberStatsOutputFile = TempFolder + '/MF' + str(MFindex) + '_fiberstats.txt'
  ComputeAvgFibLenCmdTable = fiberstatsCmd + ['--fiber_file', Tracts]
  if not os.path.isfile(FiberStatsOutputFile): # NO auto overwrite => if willing to overwrite, rm files
    print '> Running:',ComputeAvgFibLenCmdTable
    if subprocess.call( ComputeAvgFibLenCmdTable, stdout=open(FiberStatsOutputFile, 'w') , stderr=open(os.devnull, 'w') ) !=0 :
      print '> Error executing command'
      print '> ABORT'
      sys.exit(1)

  # Read file to get value # 'Average Fiber Length' 'Minimum Fiber Length' 'Maximum Fiber Length' '75 percentile Fiber Length' '90 percentile Fiber Length' 'Average 75 Percentile Fiber Length'
  for line in open(FiberStatsOutputFile):
    if 'Average Fiber Length' in line :
      AvgFibLength = float( line.split(': ')[1] )
    elif '75 percentile Fiber Length' in line :
      PercFibLength = float( line.split(': ')[1] )
    elif 'Average 75 Percentile Fiber Length' in line :
      AvgPercFibLength = float( line.split(': ')[1] )
  AvgFibLenTupleTable.append( [MF,AvgFibLength,PercFibLength,AvgPercFibLength] )

############################################
#   Find max MF: max average fiber length  #
############################################

## Sort Average Fiber Length table by AvgFibLen
AvgFibLenTupleTable = sorted(AvgFibLenTupleTable, key=lambda AvgFibLenTuple: AvgFibLenTuple[1], reverse=True) # reverse: higher in 1st position

## Display and write out file with all fib length values to plot them afterwards
FibLengthTxt = TempFolder + '/FiberLengths.txt'
FibLengthTxtFile = open(FibLengthTxt,'w')
print '> Results: \t\t\t\t| Average Fiber Length \t75 percentile Fiber Length \tAverage 75 percentile Fiber Length'
for AvgFibLenTuple in AvgFibLenTupleTable:
  print '> MF', MFTable.index(AvgFibLenTuple[0])+1, '=', AvgFibLenTuple[0] + ' \t| ' + str(AvgFibLenTuple[1]) + '\t\t' + str(AvgFibLenTuple[2]) + ' \t\t\t' + str(AvgFibLenTuple[3])
  FibLengthTxtFile.write( str(MFTable.index(AvgFibLenTuple[0])+1) + ' ' + str(AvgFibLenTuple[1]) + ' ' + str(AvgFibLenTuple[2]) + ' ' + str(AvgFibLenTuple[3]) + '\n' )
FibLengthTxtFile.close()

## Keep max Average Fiber Length in table (= 1st value because sorted)
print '> The measurement frame MF', MFTable.index(AvgFibLenTupleTable[0][0])+1, ':', AvgFibLenTupleTable[0][0], '(AvgFibLen=' + str(AvgFibLenTupleTable[0][1]) + ') will be used.'

## Plot average/75% values and write out plot image with matlab
ScriptFolder = os.path.dirname(sys.argv[0])
if ScriptFolder == '' :
  ScriptFolder='.'
PlotLenValuesCmdTable = MatlabCmd + ['-nodisplay', '-r', 'addpath(\'' + ScriptFolder + '\'); PlotLengthValues(\'' + TempFolder + '\')']
if not os.path.isfile(TempFolder + '/FiberLengths.png'): # NO auto overwrite => if willing to overwrite, rm files
  print '> If stays blocked after running the matlab command,'
  print '> it probably means that the script has crashed and matlab is waiting for a command from the user:'
  print '> You should run the matlab command manually.'
  ExecuteCommand(PlotLenValuesCmdTable)

############################################
#    Write final images to output folder   #
############################################
# Copy corrected DWI header and DTI to output folder
CorrectedDWI = OutputFolder + '/' + os.path.split(DWI)[1].split('.')[0] + '_MFcorrected.nhdr' # os.path.split() gives the name of the file without path
shutil.copyfile(TempFolder + '/MF' + str(MFTable.index(AvgFibLenTupleTable[0][0])+1) + '_dwi.nhdr', CorrectedDWI)
CorrectedDTI = OutputFolder + '/' + os.path.split(DWI)[1].split('.')[0] + '_MFcorrected_dti.nrrd' # os.path.split() gives the name of the file without path
shutil.copyfile(TempFolder + '/MF' + str(MFTable.index(AvgFibLenTupleTable[0][0])+1) + '_dti.nrrd', CorrectedDTI)

## Display execution time
time2=time.time()
timeTot=time2-time1
if timeTot<60 :
  print '> Execution time =', str(int(timeTot)), 's'
elif timeTot<3600 :
  print '> Execution time =', str(int(timeTot)), 's =', str(int(timeTot/60)), 'm', str( int(timeTot) - (int(timeTot/60)*60) ), 's'
else :
  print '> Execution time =', str(int(timeTot)), 's =', str(int(timeTot/3600)), 'h', str( int( (int(timeTot) - int(timeTot/3600)*3600) /60) ), 'm', str( int(timeTot) - (int(timeTot/60)*60) ), 's'

## Exit OK
sys.exit(0)

