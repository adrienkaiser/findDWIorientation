#!/usr/bin/python

import os # .access .path .rename .remove .mkdir
import sys # .exit
import subprocess # .call
import time # .time()
import shutil # .copyfile()

############################################
#             Define variables             #
############################################
def CheckFolder (folder):
  if os.path.isdir(folder):
    if not os.access(folder, os.W_OK):
      print '> The given output folder is not writable:',folder
      print '> ABORT'
      sys.exit(1)
  else:
    print '> The given output folder does not exist, it will be created:',folder
    print os.path.dirname(folder)
    if not os.access(os.path.dirname(folder), os.W_OK):
      print '> The parent of the given output folder is not writable:',os.path.dirname(folder)
      print '> ABORT'
      sys.exit(1)
    os.mkdir(folder)

DWI='/NIRAL/work/akaiser/Networking/NFG/nfg_1.1.1/generated_collections/130325112527/DWI/dwi.nhdr'
if not os.access(DWI, os.R_OK):
  print '> The given DWI is not readable:',DWI
  print '> ABORT'
  sys.exit(1)

OutputFolder='/NIRAL/work/akaiser/Networking/NFG/nfg_1.1.1/generated_collections/130325112527/DWI'
CheckFolder(OutputFolder)

TempFolder='/NIRAL/work/akaiser/Networking/NFG/nfg_1.1.1/generated_collections/130325112527/DWI/findDWIorientation'
CheckFolder(TempFolder)

############################################
#       Define and check tools             #
############################################
def CheckTool(Tool):
  ExceptionCaught=0
  try:
    ExitCode = subprocess.call( Tool + ['--help'], stdout=open(os.devnull, 'w') , stderr=open(os.devnull, 'w') ) # call command with no output
  except:
    ExceptionCaught=1
  if ExceptionCaught or ExitCode!=0 :
    print '> Error in:',Tool
    print '> ABORT'
    sys.exit(1)

dtiestimCmd=['/tools/bin_linux64/dtiestim']
CheckTool(dtiestimCmd)
dtiprocessCmd=['/tools/bin_linux64/dtiprocess']
CheckTool(dtiprocessCmd)
OtsuThresholdCmd=['/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/Slicer', '--launch', '/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/lib/Slicer-4.2/cli-modules/OtsuThresholdSegmentation']
CheckTool(OtsuThresholdCmd)
tractoCmd=['/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/Slicer', '--launch', '/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/lib/Slicer-4.2/cli-modules/TractographyLabelMapSeeding']
CheckTool(tractoCmd)
fiberstatsCmd=['/NIRAL/work/akaiser/Projects/dtiprocess-build/bin/fiberstats']
CheckTool(fiberstatsCmd)

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

  # Compute DTI
  DTI = TempFolder + '/MF' + str(MFindex) + '_dti.nrrd'
  ComputeDTICmdTable = dtiestimCmd + ['--dwi_image', MFDWI, '--tensor_output', DTI, '-m', 'wls']
  if not os.path.isfile(DTI): # NO auto overwrite => if willing to overwrite, rm files
    ExecuteCommand(ComputeDTICmdTable)

  # Compute FA # !! Fa needs to be computed only once because same for all MFs
  FA = TempFolder + '/fa.nrrd'
  ComputeFACmdTable = dtiprocessCmd + ['--dti_image', DTI, '-f', FA]
  if not os.path.isfile(FA): # NO auto overwrite => if willing to overwrite, rm files
    ExecuteCommand(ComputeFACmdTable)

  # Compute mask by OTSU thresholding FA # !! Mask needs to be computed only once because same for all MFs
  Mask = TempFolder + '/mask.nrrd'
  ComputeMaskCmdTable = OtsuThresholdCmd + [FA, Mask, '--minimumObjectSize', '10', '--brightObjects'] # brightObjects= bright = fa = 1 # --minimumObjectSize 10 => to avoid 1-voxel artefacts
  if not os.path.isfile(Mask): # NO auto overwrite => if willing to overwrite, rm files
    ExecuteCommand(ComputeMaskCmdTable)

  # Compute Tractography
  Tracts = TempFolder + '/MF' + str(MFindex) + '_tracts.vtk'
  ComputeTractsCmdTable = tractoCmd + [DTI, Tracts, '--inputroi', Mask]
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

  # Read file to get value
  for line in open(FiberStatsOutputFile):
    if 'Average Fiber Length' in line :
      AvgFibLenTupleTable.append( [MF,float( line.split(': ')[1] ) ] )

############################################
#   Find max MF: max average fiber length  #
############################################

## Sort Average Fiber Length table by AvgFibLen
AvgFibLenTupleTable = sorted(AvgFibLenTupleTable, key=lambda AvgFibLenTuple: AvgFibLenTuple[1], reverse=True) # reverse: higher in 1st position
print '> Results:'
for AvgFibLenTuple in AvgFibLenTupleTable:
  print '> MF', MFTable.index(AvgFibLenTuple[0])+1, '=', AvgFibLenTuple[0] + ' \t: Average Fiber Length = ' + str(AvgFibLenTuple[1])

## Keep max Average Fiber Length in table (= 1st value because sorted)
print '> The measurement frame MF', MFTable.index(AvgFibLenTupleTable[0][0])+1, ':', AvgFibLenTupleTable[0][0], '(AvgFibLen=' + str(AvgFibLenTupleTable[0][1]) + ') will be used.'

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

