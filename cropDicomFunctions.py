import glob
import os
import numpy as np
import pandas as pd
import pydicom
import matplotlib.pyplot as plt
import png
from fnmatch import fnmatch

def getFileNames(dicom_files):
    fileList = []
    for path, subdirs, files in os.walk(dicom_files):
        for name in files:
            if fnmatch(name, '*.dcm'):
                fileList.append(os.path.join(path, name))

    print(len(fileList), ' dicom images found')
    return fileList


# File walk method
def getFiles(dicom_files, verbose=1):
    fileList = []
    for path, subdirs, files in os.walk(dicom_files):
        for name in files:
            if fnmatch(name, '*.dcm'):
                fileList.append(os.path.join(path, name))

    print(len(fileList), ' dicom images found')


    # Load dicom files into np array
    dicomImg = np.array([])
    count = 0
    print(len(fileList), ' Files found')
    print('Loading images...')
    for f in fileList:
        dicomImg = np.append(dicomImg, pydicom.dcmread(f))
        count += 1
        print(count, '/', len(fileList))
    #print('name:\n', dicomImg[0].PresentationIntentType)
    return dicomImg, fileList




def deletePreProcessed(dicomImg, fileList):
    forPresentationCount = 0
    toDelete = []
    for index, _ in enumerate(dicomImg):
        tmp = _.PresentationIntentType
        if tmp == 'FOR PRESENTATION':
            forPresentationCount += 1
        else:
            toDelete.append(index)
    print('dicomImg len:', len(dicomImg))
    np.delete(dicomImg, toDelete)
    mask = np.ones(len(dicomImg), dtype=bool)
    mask[toDelete] = False
    dicomImg = dicomImg[mask]
    fileList = np.asarray(fileList)
    fileList = fileList[mask]
    print('\nTotal DICOM: ', len(dicomImg))
    print('Total FOR PROCESSING: ', forPresentationCount)
    return dicomImg, fileList

# Get the imageSOPIUD of the contralateral images
# given the imageSOPIUD and spreadsheet sheet
def getContralateral(imageSOPIUD, sheet):
    print('imageSOPIUD: ', imageSOPIUD)
    properties = {'imageSOPIUD':[], 'viewPosition':[], 'imageLaterality':[], 'presentationIntentType':[]}

    # Find row that has the img
    indx = [_ == imageSOPIUD for _ in sheet['ImageSOPIUID']].index(True) # ImageSOPIUID, ReferencedSOPInstanceUID
    studyIUID = sheet['StudyIUID'][indx]
    lesion = dict.fromkeys(properties)
    lesion['viewPosition'] = sheet['ViewPosition'][indx]
    lesion['imageLaterality'] = sheet['ImageLaterality'][indx]
    lesion['presentationIntentType'] = sheet['PresentationIntentType'][indx]
    print('\nlesion[viewPosition]: ', lesion['viewPosition'])
    print('lesion[imageLaterality]: ', lesion['imageLaterality'])
    print('lesion[presentationIntentType]: ', lesion['presentationIntentType'])

    # Get properties for all images in the same studyIUID
    studyGroup = {'imageSOPIUD': [], 'properties':[]}
    for indx, _ in enumerate(sheet['StudyIUID']):
        if studyIUID == _:
            studyGroup['properties'].append(dict.fromkeys(properties))
            studyGroup['properties'][-1]['viewPosition'] = sheet['ViewPosition'][indx]
            studyGroup['properties'][-1]['imageLaterality'] = sheet['ImageLaterality'][indx]
            studyGroup['properties'][-1]['presentationIntentType'] = sheet['PresentationIntentType'][indx]
            studyGroup['imageSOPIUD'].append(sheet['ImageSOPIUID'][indx])
    # Set properties to match
    propertiesToMatch = dict.fromkeys(properties)
    if lesion['imageLaterality'] == 'R':
        propertiesToMatch['imageLaterality'] = 'L'
    else:
        propertiesToMatch['imageLaterality'] = 'R'
    propertiesToMatch['viewPosition'] = lesion['viewPosition']
    propertiesToMatch['presentationIntentType'] = lesion['presentationIntentType']

    print('\npropertiesToMatch[viewPosition]: ', propertiesToMatch['viewPosition'])
    print('propertiesToMatch[imageLaterality]: ', propertiesToMatch['imageLaterality'])
    print('propertiesToMatch[presentationIntentType]: ', propertiesToMatch['presentationIntentType'])

    # Find matches
    matches = {'imageSOPIUD': [], 'properties':[]}
    for i in range(len(studyGroup['properties'])):
        if studyGroup['properties'][i] == propertiesToMatch:
            matches['properties'].append(studyGroup['properties'][i])
            matches['imageSOPIUD'].append(studyGroup['imageSOPIUD'][i])
            print('match made')
    if len(matches['properties']) > 1 or len(matches['properties']) == 0:
        print('    MY_ERROR: ', len(matches['properties']), ' matches for contralateral')
    else:
        print('        MATCH MATCH MATCH len: ', len(matches['properties']))
        return matches['imageSOPIUD'][0]

# Remove images from fList so that there is only one per patient
# Pass sheet that has 'studyIUID'
def filter_for_single_StudyIUID(file_list, sheet):
    # Run through file_list
    # Images should be ordered in terms of patient
    # Hold the current patient in tmp_patient
    # If any susequent imgages have the same tmp_patient delete them
    # Else update the tmp_patient
    print('filter for single StudyIUID...')
    tmp_studyIUID = ''
    new_file_list = []
    for f in file_list:
        key = os.path.basename(f)[:-4]
        # Find the row in the xml file that holds the img info
        try:
            indx = [_ == key for _ in sheet['ImageSOPIUID']].index(True)
            if tmp_studyIUID != getSpreadsheetCell('StudyIUID', key, sheet):
                # New studyIUID - append
                new_file_list.append(f)
            tmp_studyIUID = getSpreadsheetCell('StudyIUID', key, sheet)
        except ValueError:
            print(key, ' not found\n')
    print('List reduced from: ', len(file_list),
          'to: ',  len(new_file_list))
    return new_file_list

# Remove files that are not FOR PRESENTATION
def filter_for_presentation(file_list, sheet, verbose = True):
    if verbose == True:
        print('Filter for presentation...')
    new_list = []
    for f in file_list:
        key = os.path.basename(f)[:-4]
        # Get index
        try:
            indx = [_==key for _ in sheet['ImageSOPIUID']].index(True)
            # Check presentation type
            if (getSpreadsheetCell('PresentationIntentType', key, sheet) == 
                    'FOR PRESENTATION'):
                # Add to newlist
                new_list.append(f)
        except ValueError:
            if verbose == True:
                print('MY_ERROR: key not fonud:\n', key)
    if verbose == True:
        print(len(file_list), ' reduced to ', len(new_list))
    return new_list


# Remove files that are not in the spreadsheet
def filter_spreadsheet(fList, sheet, verbose = False):
    print('Removing files that are not in the spreadsheet...')
    img = {}
    new_list = []
    for f in fList:
        key = os.path.basename(f)[:-4]
        # Find row in the xml file that holds the img info
        try:
            indx = [_==key for _ in sheet['ImageSOPIUID']].index(True) # ImageSOPIUID, ReferencedSOPInstanceUID
            # No error therefore image must be in spreadsheet
            new_list.append(f)
        except ValueError:
            if verbose == True:
                print('MY_ERROR: key not found:\n', key)
    print(len(fList), ' reduced to ', len(new_list))
    return new_list
# Given a sheet and ImageSOPIUID, returns value at column x

def getSpreadsheetCell(column, ImageSOPIUID, sheet):
    # find index for ImageSOPIUID
    indx = [_ == ImageSOPIUID for _ in sheet['ImageSOPIUID']].index(True)
    return sheet[column][indx]

# Import xls file, extract ROI coords, get pixel array from DICOM image
def buildDict(dicomImg, fileList, spreadsheet, verbose = True):
    #xls = pd.ExcelFile('/vol/vssp/cvpwrkspc01/scratch/wm0015/download/batch_1_IMAGE.xls')
    #xls = pd.ExcelFile('/vol/vssp/cvpwrkspc01/scratch/wm0015/batch_50_IMAGE.xls')
    xls = pd.ExcelFile(spreadsheet)
    sheet = xls.parse(1)

    # Create a dict where the key is the image name
    # Each key has the image, and coords
    img = {}
    for i in range(len(fileList)):
        key = os.path.basename(fileList[i])[:-4]
        # Find row in the xml file that holds the img info
        try:
            indx = [_ == key for _ in sheet['ImageSOPIUID']].index(True) # ImageSOPIUID, ReferencedSOPInstanceUID
            img.update({key:{}})
            img[key].update({'img': dicomImg[i].pixel_array})
            img[key].update({'x': [sheet['X1'][indx], sheet['X2'][indx]]})
            img[key].update({'y': [sheet['Y1'][indx], sheet['Y2'][indx]]})
        except ValueError:
            if verbose == True:
                print('MY_ERROR: key not found:\n', key)

    print(len(img), 'DICOM images extracted')
    # print(img)
    # Crop the images to given ROI
    toDelete = [] # Keep track of error causing keys and delete after loop
    for key in img:
        try:
            tmp = img[key]['img']
            x = img[key]['x']
            y = img[key]['y']
            x = [int(x[0]), int(x[1])]
            y = [int(y[0]), int(y[1])]
            #x is width, y is height
            #in numpy array, y,x
            img[key].update({'cropROI':tmp[y[0]:y[1], x[0]:x[1]]})
        except:
            print('ROI extraction failed...Removing key\nkey:  ', key, '\nx  :', x, '\ny:  ', y)
            toDelete.append(key)

    #img_calc = img['1.2.840.113681.2230565232.954.3504500766.32']
    for _ in toDelete:
        img.pop(_)
    return img


# Write images to disk with markers and basic crop    
def writeMarkedImages(img):
    for key in img:
        plt.figure(figsize=(20,20))
        marker = [(img[key]['x'][1] + img[key]['x'][0])/2, (img[key]['y'][1] + img[key]['y'][0])/2 ]
        plt.imshow(img[key]['img']/16383, cmap='gray', vmin=0, vmax=0.2)
        plt.plot(marker[0], marker[1], marker='x', color=[1,0,1], markersize=30)
        plt.savefig('/vol/vssp/cvpwrkspc01/scratch/wm0015/markers/tmp/' + key +'_full.png')
        #plt.show()
        plt.close()

        plt.figure(figsize=(20,20))
        plt.imshow(img[key]['cropROI'], cmap='gray')
        plt.savefig('/vol/vssp/cvpwrkspc01/scratch/wm0015/markers/tmp/' + key +'_crop.png')
        #plt.show()
        plt.close()

# Crop the images so that the ROI is centred but all crops are the same size
def computeCrops(img, crop_size = 256):
    for key in img:
        tmp = img[key]['img']
        x = img[key]['x']
        y = img[key]['y']
        c = [round((x[0]+x[1])/2), round((y[0]+y[1])/2)]
        # Pad images before cropping (wrap around)
        pad = 1000
        tmp = np.pad(tmp, pad, mode='wrap')
        img[key].update({'crop':
                         tmp[int(c[1]-crop_size/2+pad):int(c[1]+crop_size/2+pad),
                             int(c[0]-crop_size/2+pad):int(c[0]+crop_size/2+pad)]})
        # Reshape from (256, 256) to (256, 256, 1)
        img[key]['crop'] = np.reshape(img[key]['crop'],(img[key]['crop'].shape[0], img[key]['crop'].shape[1], 1))
    return img

# Find bit depth
def findBitDepth(img):
    print('Find bit depth...')
    maxmax = 0
    for key in img:
        tmp = img[key]['img']
        print(np.amax(tmp))
        if np.amax(tmp) > maxmax:
            maxmax = np.amax(tmp)
    print('The largest value is: ', maxmax)

# Find average ROI size
def findAverageROISize(img):
    print('Find average ROI size...')
    totalX = 0
    totalY = 0
    for key in img:
        x = img[key]['x']
        y = img[key]['y']
        totalX += x[1] - x[0]
        totalY += y[1] - y[0]
    print('Average ROI width: ', totalX/len(img), '\nAverage ROI length: ', totalY/len(img))

# View crops / save to disk
def writeCropsToDisk(img, folder_location, crop_size):
    count = 0
    for key in img:
        count+=1
        #f = open('/vol/vssp/cvpwrkspc01/scratch/wm0015/batch1_crop/' + key + '.png', 'wb')
        f = open(folder_location + key + '.png', 'wb')
        w = png.Writer(width = crop_size, height = crop_size, bitdepth=16, greyscale=True)
        w.write(f, img[key]['crop'])
        f.close()
        print(count, '/', len(img))
        if count == -1:
            break

def buildArrayForPickle(img):    #img.update({key:{}})
    allCrops = {}
    for key in img:
        allCrops.update({key:[]})
        allCrops[key] = img[key]['crop']
    return allCrops

def savePickle(ob, dest):
    import pickle
    print('Pickling...')
    with open(dest, 'wb') as output:
        pickle.dump(ob, output, pickle.HIGHEST_PROTOCOL)

def buildDictNormals(dicomImg, fileList):
    from scipy import ndimage
    # Get pixel values
    # Draw square around breast
    # Select random centre for crop within breast
    img = {}
    for i in range(len(fileList)):
        key = os.path.basename(fileList[i])[:-4]
        img.update({key:{}})
        img[key].update({'img': dicomImg[i].pixel_array})
        # Get centre of mass (breast centre)
        centre = ndimage.measurements.center_of_mass(img[key]['img'])
        centre = np.asarray(centre).astype(int)

#         #Check images
#         plt.figure(figsize=(20,20))
#         #plt.imshow(img[key]['img']/16383, cmap='gray', vmin=0, vmax=0.2)
#         plt.imshow(img[key]['img'], cmap='gray')
#         plt.plot(centre[1], centre[0], marker='x', color=[1,0,1], markersize=30)
#         #plt.savefig('/vol/vssp/cvpwrkspc01/scratch/wm0015/markers/tmp/' + key +'_full.png')
#         plt.show()
#         plt.close()

        #LATER
#         img[key].update({'x': [sheet['X1'][indx], sheet['X2'][indx]]})
#         img[key].update({'y': [sheet['Y1'][indx], sheet['Y2'][indx]]})
