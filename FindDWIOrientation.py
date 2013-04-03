#!/usr/bin/python

import os # .access .system
import sys # .exit
import subprocess # .call
import random

############################################
#             Define variables             #
############################################
DWI='/NIRAL/work/akaiser/Networking/NFG/nfg_1.1.1/generated_collections/130325112527/DWI/Testdwi.nhdr'
if not os.access(DWI, os.W_OK):
  print 'The given DWI is not writable:',DWI
  sys.exit(1)
TempDWI= os.path.split(DWI)[0] + '/TempDWI.nhdr'

OutputFolder='/NIRAL/work/akaiser/Networking/NFG/nfg_1.1.1/generated_collections/130325112527/DWI'
if not os.access(OutputFolder, os.W_OK):
  print 'The given output folder is not writable:',OutputFolder
  sys.exit(1)

############################################
#       Define and check tools             #
############################################
def CheckTool(Tool):
  ExceptionCaught=0
  try:
    ExitCode = subprocess.call( [Tool,"--help"] , stdout=open(os.devnull, "w") , stderr=open(os.devnull, "w") ) # call command with no output
  except:
    ExceptionCaught=1
  if ExceptionCaught or ExitCode!=0 :
    print 'Error in:',Tool
    sys.exit(1)

dtiestimCmd="/tools/bin_linux64/dtiestim"
CheckTool(dtiestimCmd)
dtiprocessCmd="/tools/bin_linux64/dtiprocess"
CheckTool(dtiprocessCmd)
tractoCmd='/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/lib/Slicer-4.2/cli-modules/TractographyLabelMapSeeding'
#CheckTool(tractoCmd)
fiberstatsCmd='/tools/bin_linux64/fiberstats'
#CheckTool(fiberstatsCmd)

############################################
# Test for all possible measurement frames #
############################################

## Write Measurement Frames in a table
MFTable=[]
for XYZ in [ (X,Y,Z) for X in [1,-1] for Y in [1,-1] for Z in [1,-1] ] : # 2 x 2 x 2 = 8 possiblities
  MF='(' + str(XYZ[0]) + ',0,0) (0,' + str(XYZ[1]) + ',0) (0,0,' + str(XYZ[2]) + ')'
  MFTable.append(MF)

## Compute Avg Fiber Length for all possible MFs
AvgFibLenTupleTable=[] # each element of the table is [MF,AvgFibLen]
for MF in MFTable:
  # Display Measurement Frame
  print '=> Testing:',MF

  # Update DWI header
  TempDWIfile = open(TempDWI,'a') # open for Append
  for line in open(DWI): # read all lines and replace line containing "measurement frame" by the new MF
    if "measurement frame" in line :
      TempDWIfile.write('measurement frame: ' + MF + '\n')
    else :
      TempDWIfile.write(line)
  TempDWIfile.close()
  os.rename(TempDWI,DWI)
  if os.path.isfile(TempDWI) :
    os.remove(TempDWI)

  # Compute DTI
  DTI = OutputFolder + '/' + str(XYZ) + 'dti.nrrd'

  # Compute FA
  FA = OutputFolder + '/' + str(XYZ) + 'fa.nrrd'

  # Compute mask by OTSU thresholding FA
  mask = OutputFolder + '/' + str(XYZ) + 'mask.nrrd'

  # Compute Tractography
  tracts = OutputFolder + '/' + str(XYZ) + 'tracts.vtk'

  # Compute Average Fiber Length
  AvgFibLen=random.randint(1,100)
  AvgFibLenTupleTable.append( [MF,AvgFibLen] )

## Sort Average Fiber Length table by AvgFibLen
AvgFibLenTupleTable = sorted(AvgFibLenTupleTable, key=lambda AvgFibLenTuple: AvgFibLenTuple[1], reverse=True) # reverse: higher in 1st position
print '=> Results:'
for AvgFibLenTuple in AvgFibLenTupleTable:
  print AvgFibLenTuple[0] + ' \t: Average Fiber Length = ' + str(AvgFibLenTuple[1])

## Keep max Average Fiber Length in table (= 1st value because sorted)
print 'The measurement frame:' , AvgFibLenTupleTable[0][0] , '(AvgFibLen=' + str(AvgFibLenTupleTable[0][1]) + ') will be used.'

## Update DWI header with final right orientation
TempDWIfile = open(TempDWI,'a') # open for Append
for line in open(DWI): # read all lines and replace line containing "measurement frame" by the new MF
  if "measurement frame" in line :
    TempDWIfile.write('measurement frame: ' + AvgFibLenTupleTable[0][0] + '\n')
  else :
    TempDWIfile.write(line)
TempDWIfile.close()
os.rename(TempDWI,DWI)
if os.path.isfile(TempDWI) :
  os.remove(TempDWI)

# Exit
sys.exit(0)

