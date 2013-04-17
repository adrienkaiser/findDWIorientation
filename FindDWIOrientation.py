#!/usr/bin/python

import os # .access .path .rename .remove .mkdir
import sys # .exit .argv
import subprocess # .call
import time # .time()
import getopt # .getopt() : to parse the cmd line args
#import shutil # .copyfile()

# DWI
# /NIRAL/work/akaiser/Networking/NFG/nfg_1.1.1/generated_collections/130325112527/DWI/dwi.nhdr  => !! --NoBrainmask
# /rodent/SherylMoy/processing/dwi.nhdr
# /rodent/FAS_sulik/DTI2013/Processing/N50320/1-Converted/N50320_dwi.nhdr
# /rodent/FAS_sulik/DTI08/PN45ChallengeGrant/4K-02/4K-02_dwi.nhdr
# /home/akaiser/Networking/from_Utah/Data/b1000.nhdr
# TempFolder
# /NIRAL/work/akaiser/MF_FAS_Sulik2

############################################
#             Args & Usage                 #
############################################
def DisplayUsage () :
  print '> USAGE : $ FindDWIOrientation.py -i <DWI> -o <OutputFolder> [Options]'
  print '> -h --help                       : Display usage'
  print '> -i --inputDWI <string>          : Input DWI image (.nhdr or .nrrd)'
  print '> -o --OutputFolder <string>      : Output folder'
  print '> -t --TempFolder <string>        : Folder for temporary files (if no TempFolder given, it will be set to the OutputFolder)'
  print '> -n --NoBrainmask                : If the image has not much noise, you do not need the brain mask'
  print '> -f --UseFullBrainMaskForTracto  : Compute tractography in the full brain'
  print '> -d --DownsampleImage <int>      : Downsample the input image to have faster processing'

# parse args into lists 'opts' and 'args'
try:
  opts, args = getopt.getopt(sys.argv[1:],'hi:o:t:nfd:',['help','inputDWI=','OutputFolder=','TempFolder=','NoBrainmask','UseFullBrainMaskForTracto','DownsampleImage='])
except getopt.GetoptError:
  print '> Error parsing aruments'
  DisplayUsage()
  sys.exit(1)

if not opts :
  DisplayUsage()
  sys.exit(0)

if args : # if args list non empty # the 'args' list contains the non parsed args
  print '> These args have not been parsed:',args
  DisplayUsage()
  sys.exit(1)

DWI = ''
OutputFolder = ''
TempFolder = ''
ComputeBrainmask = 1
UseFullBrainMaskForTracto = 0
DownsamplingFactor = -1

for opt, arg in opts:
  if opt in ("-h", "--help"):
    DisplayUsage()
    sys.exit(0)
  elif opt in ("-i", "--inputDWI"):
    DWI = arg
  elif opt in ("-o", "--OutputFolder"):
    OutputFolder = arg
  elif opt in ("-t", "--TempFolder"):
    TempFolder = arg
  elif opt in ("-n", "--NoBrainmask"):
    ComputeBrainmask = 0
  elif opt in ("-f", "--UseFullBrainMaskForTracto"):
    UseFullBrainMaskForTracto = 1
  elif opt in ("-d", "--DownsampleImage"):
    DownsamplingFactor = int(arg)

if not DWI or not OutputFolder :
  print 'Please give an input DWI image (.nhdr or .nrrd) and an output folder.'
  DisplayUsage()
  sys.exit(1)

if not TempFolder :
  TempFolder = OutputFolder

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
    try:
      os.makedirs(folder) # recursive directory creation function
    except: # exception if leaf directory already exists or cannot be created
      print '> Error while creating the given output folder (check the write permissions on the parent folders):',folder
      print '> ABORT'
      sys.exit(1)

CheckFolder(TempFolder)
CheckFolder(OutputFolder)

if not os.access(DWI, os.R_OK):
  print '> The given DWI is not readable:',DWI
  print '> ABORT'
  sys.exit(1)

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

ResampleVolume2Cmd=['/tools/bin_linux64/ResampleVolume2']
CheckTool(ResampleVolume2Cmd + ['--help'])
unuCmd=['/tools/bin_linux64/unu']
CheckTool(unuCmd + ['--help'])
dtiestimCmd=['/tools/bin_linux64/dtiestim']
CheckTool(dtiestimCmd + ['--help'])
BrainMaskCmd=['/NIRAL/work/akaiser/MaskComputationWithThresholding-build/MaskComputationWithThresholding'] # ['/rodent/bin_linux64/toolsMarch2013/MaskComputationWithThresholding']
CheckTool(BrainMaskCmd + ['--help'])
dtiprocessCmd=['/tools/bin_linux64/dtiprocess']
CheckTool(dtiprocessCmd + ['--help'])
ImageMathCmd=['/tools/bin_linux64/ImageMath']
CheckTool(ImageMathCmd + ['-help'])
OtsuThresholdCmd=['/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/Slicer', '--launcher-no-splash', '--launch', '/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/lib/Slicer-4.2/cli-modules/OtsuThresholdSegmentation']
CheckTool(OtsuThresholdCmd + ['--help'])
tractoCmd=['/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/Slicer', '--launcher-no-splash', '--launch', '/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/lib/Slicer-4.2/cli-modules/TractographyLabelMapSeeding']
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
  print '> Running:',' '.join(Command)
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

## Convert input DWI to nhdr if nrrd
DWIPathParsed = os.path.split(DWI)[1].split('.')
if DWIPathParsed[ len(DWIPathParsed)-1 ] == 'nrrd' : # get last extension
  ConvertedDWI = TempFolder + '/' + DWIPathParsed[0] + '.nhdr'
  ConvertDWICmdTable = ResampleVolume2Cmd + [DWI, ConvertedDWI]
  if not os.path.isfile(ConvertedDWI): # NO auto overwrite => if willing to overwrite, rm files
    ExecuteCommand(ConvertDWICmdTable)
  DWI = ConvertedDWI

## Downsample image if asked
if DownsamplingFactor > 1 : # if 1 or below: no interest
  # Get DWI size and divide it
  for line in open(DWI):
    if 'sizes' in line :
      SizesTable = line.replace('\n','').split(' ')[1:5] # remove \n from the array before splitting
    if 'kinds' in line : # kinds: space space space list => needs to find where list is
      WhereIsList = line.replace('\n','').replace('vector','list').split(' ').index('list') - 1 # index of 'list' (or 'vector') in SizesTable (-1 because 'kinds:' is not in the table)
  SizesTable[WhereIsList] = int(SizesTable[WhereIsList]) * DownsamplingFactor # Multiply the nb of dirs so then we can divide the whole SizesTable
  SizesTable = [ str(int(x)/DownsamplingFactor) for x in SizesTable ] # divide whole list 

  # Downsample image
  ResampledDWI = TempFolder + '/' + os.path.split(DWI)[1].split('.')[0] + '_Downsampled' + str(DownsamplingFactor) + '.nhdr'
  DownsampleCmdTable = unuCmd + ['resample', '-i', DWI, '--size', SizesTable[0], SizesTable[1], SizesTable[2], SizesTable[3], '-o', ResampledDWI]
  if not os.path.isfile(ResampledDWI): # NO auto overwrite => if willing to overwrite, rm files
    ExecuteCommand(DownsampleCmdTable)

  # Update new DWI header
  TempNhdr =  TempFolder + '/tempfile.nhdr'
  TempFile = open(TempNhdr,'w')
  for line in open(ResampledDWI):
    line = line.replace('???','list')
    TempFile.write(line)
  TempFile.close()
  os.remove(ResampledDWI)
  os.rename(TempNhdr,ResampledDWI)
  UsedDWI = ResampledDWI
else :
  UsedDWI = DWI

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
    for line in open(UsedDWI): # read all lines and replace line containing 'measurement frame' by the new MF
      if 'measurement frame' in line :
        MFDWIfile.write('measurement frame: ' + MF + '\n')
      elif 'data file' in line : # if not full path (not begin by '/'), need to give the full path to the date file(s)
        DataFile = line.split(' ')[2]
        if DataFile[0] != '/': # not full path
          UsedDWIPath = os.path.dirname(UsedDWI)
          if UsedDWIPath == '' :
            UsedDWIPath = '.'
          NewDataFile = os.path.abspath(UsedDWIPath + '/' + DataFile)
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
    AplpyMasktoFACmdTable = ImageMathCmd + [FA, '-outfile', FAmasked, '-mul', BrainMask, '-type', 'float']
    if not os.path.isfile(FAmasked): # NO auto overwrite => if willing to overwrite, rm files
      ExecuteCommand(AplpyMasktoFACmdTable)
    # Apply mask to DTI to avoid tracking outside of the brain
    (DTIfilename, extension) = os.path.splitext(DTI)
    DTImasked = DTIfilename + '_masked.nrrd'
    ApplyMasktoDTICmdTable = ImageMathCmd + [DTI, '-outfile', DTImasked, '-mask', BrainMask]
    if not os.path.isfile(DTImasked): # NO auto overwrite => if willing to overwrite, rm files
      ExecuteCommand(ApplyMasktoDTICmdTable)
    DTI = DTImasked
  else :
    FAmasked = FA

  # Compute mask by OTSU thresholding FA # !! Mask needs to be computed only once because same for all MFs
  if not ComputeBrainmask or not UseFullBrainMaskForTracto :
    Mask = TempFolder + '/mask.nrrd'
    ComputeMaskCmdTable = OtsuThresholdCmd + [FAmasked, Mask, '--minimumObjectSize', '10', '--brightObjects'] # brightObjects= bright = fa = 1 # --minimumObjectSize 10 => to avoid 1-voxel artefacts
    if not os.path.isfile(Mask): # NO auto overwrite => if willing to overwrite, rm files
      ExecuteCommand(ComputeMaskCmdTable)
  else : # ComputeBrainmask and UseFullBrainMaskForTracto
    Mask = BrainMask

  # Compute Tractography #  
  Tracts = TempFolder + '/MF' + str(MFindex) + '_tracts.vtk'
  ComputeTractsCmdTable = tractoCmd + [DTI, Tracts, '--inputroi', Mask, '--seedspacing', '.5', '--clthreshold', '0.3', '--stoppingvalue', '0.25', '--stoppingcurvature', '0.7', '--integrationsteplength', '.5'] # if 'Mask' contains several labels: By default, the seeding region is the label 1
  if not os.path.isfile(Tracts): # NO auto overwrite => if willing to overwrite, rm files
    ExecuteCommand(ComputeTractsCmdTable)

  # Compute Average Fiber Length
  FiberStatsOutputFile = TempFolder + '/MF' + str(MFindex) + '_fiberstats.txt'
  ComputeAvgFibLenCmdTable = fiberstatsCmd + ['--fiber_file', Tracts]
  if not os.path.isfile(FiberStatsOutputFile): # NO auto overwrite => if willing to overwrite, rm files
    print '> Running:',' '.join(ComputeAvgFibLenCmdTable)
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
if os.path.isfile(ScriptFolder + '/PlotLengthValues.m') : # If matlab script found, otherwise no plot image
  PlotLenValuesCmdTable = MatlabCmd + ['-nodisplay', '-r', 'addpath(\'' + ScriptFolder + '\'); PlotLengthValues(\'' + TempFolder + '\')']
  if not os.path.isfile(TempFolder + '/FiberLengths.png'): # NO auto overwrite => if willing to overwrite, rm files
    print '> If stays blocked after running the matlab command,'
    print '> it probably means that the script has crashed and matlab is waiting for a command from the user:'
    print '> You should run the matlab command manually.'
    ExecuteCommand(PlotLenValuesCmdTable)

############################################
#      Write final DWI to output folder    #
############################################
# Create corrected DWI header to then create nrrd for output folder
CorrectedDWI = TempFolder + '/' + os.path.split(DWI)[1].split('.')[0] + '_MFcorrected.nhdr' # os.path.split() gives the name of the file without path
CorrectedDWIfile = open(CorrectedDWI,'w')
for line in open(DWI): # read all lines and replace line containing 'measurement frame' by the right MF
  if 'measurement frame' in line :
    CorrectedDWIfile.write('measurement frame: ' + AvgFibLenTupleTable[0][0] + '\n')
  elif 'data file' in line : # if not full path (not begin by '/'), need to give the full path to the date file(s)
    DataFile = line.split(' ')[2]
    if DataFile[0] != '/': # not full path
      NewDataFile = os.path.abspath(os.path.dirname(DWI) + '/' + DataFile)
    else: # full path: keep as is
      NewDataFile = DataFile
    CorrectedDWIfile.write( line.replace(DataFile,NewDataFile) )
  else :
    CorrectedDWIfile.write(line)
CorrectedDWIfile.close()
print '> The MF corrected DWI header has been written:',CorrectedDWI

# Convert nhdr to nrrd and put it in output folder
CorrectedDWInrrd = OutputFolder + '/' + os.path.split(DWI)[1].split('.')[0] + '_MFcorrected.nrrd'
ConvertDWInrrdCmdTable = ResampleVolume2Cmd + [CorrectedDWI, CorrectedDWInrrd]
if not os.path.isfile(CorrectedDWInrrd): # NO auto overwrite => if willing to overwrite, rm files
  ExecuteCommand(ConvertDWInrrdCmdTable)
print '> The MF corrected nrrd DWI has been written:',CorrectedDWInrrd

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

