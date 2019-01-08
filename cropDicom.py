from cropDicomFunctions import *
# _______Conterlateral____________
# Get file names of selected lesion dicom images
# Using the spreadsheet find the contrilateral images
# Copy these images to a folder


def multiprocess_cont_match(tmp_properties, properties_to_match, sheet0, tmp_ImageSOPIUID):
    for _ in tmp_properties:
        tmp_properties[_] = getSpreadsheetCell(_, tmp_ImageSOPIUID,
                                               sheet0)
    if tmp_properties == properties_to_match:
        return(tmp_ImageSOPIUID)

def multiprocess_copy(dst_copy_cont, batch, num_files, items):
    from shutil import copyfile
    cont_path = items[0]
    lesion_name = items[1]
    counter = items[2]
    copyfile(cont_path, dst_copy_cont + '/' + lesion_name)
    print('Copy (', counter, '/', num_files, ')', 'batch ', batch)

def get_contrilateral(file_list_lesion, dst_copy_cont, all_dicom_files, spreadsheet, batch = 1):
    from functools import partial
    import multiprocessing as mp
    import pandas as pd
    from shutil import copyfile
    import pydicom
    import fnmatch
    import os
    import time
    xls = pd.ExcelFile(spreadsheet)
    sheet1 = xls.parse(1)
    sheet0 = xls.parse(0)

    print('Finding the contrilateral images...')
    cont_image_paths_to_copy = []
    lesion_names_with_cont = []
    pool = mp.Pool()
    for f_index, f in enumerate(file_list_lesion):
        focus_ImageSOPIUID = os.path.basename(f)[:-4]
        # Get lesions properties
        properties = {'StudyIUID': '', 'ImageLaterality': '', 'ViewPosition':
                      '', 'PresentationIntentType': ''}
        focus_properties = dict(properties)
        for _ in focus_properties:
            focus_properties[_] = getSpreadsheetCell(_, focus_ImageSOPIUID,
                                                     sheet0)
        # Calculate properties to search for for contilateral
        properties_to_match = dict(focus_properties)
        if properties_to_match['ImageLaterality'] == 'R':
            properties_to_match['ImageLaterality'] = 'L'
        else:
            properties_to_match['ImageLaterality'] = 'R'

        # Search spreadsheet for contrilateral images
        tmp_properties = dict(properties)
        match = {'ImageSOPIUID':[], 'path':[]}

        func = partial(multiprocess_cont_match, tmp_properties, properties_to_match, sheet0)
        results = pool.map(func, sheet0['ImageSOPIUID'])
        results = np.asarray(results)
        if sum(results != None) > 0:
            match['ImageSOPIUID'] = results[results!=None][0]
            # Get file path of the match
            search = fnmatch.filter(
                all_dicom_files, '*' + match['ImageSOPIUID'] + '*')
            match['path'].append(search[0])

            print('Match', '(', f_index+1, '/',
                  len(file_list_lesion), ')', 'batch ', batch)
            cont_image_paths_to_copy.append(match['path'][0])
            lesion_names_with_cont.append(os.path.basename(f))
        else:
            print('No contrilateral for:\n', focus_ImageSOPIUID)


    # Check to see if destination directory exists
    print('checking to see if following directory exists:\n{}'.format(
        dst_copy_cont))
    if os.path.isdir(dst_copy_cont) == False:
        print('Did not exist... creating')
        os.mkdir(dst_copy_cont)
    # Write text file detailing lesions and cont
    with open(dst_copy_cont + '/lesion_to_cont_details.txt', 'w') as text_file:
        text_file.write('Format:\nLesion --- Contralateral')
        for cont_path, lesion_name in zip(
                cont_image_paths_to_copy, lesion_names_with_cont):
            text_file.write(
                '\n' + lesion_name[0:-4] + ' --- ' +
                os.path.basename(cont_path)[0:-4])
    # Copy contilateral images to a folder - use multi processing
    func = partial(multiprocess_copy, dst_copy_cont, batch,
                   len(cont_image_paths_to_copy))
    results = pool.map(func, list(zip(cont_image_paths_to_copy,
                                 lesion_names_with_cont,
                                      range(len(cont_image_paths_to_copy)))))



# Should run through the dicom contrilaterals, find the ROIs and crop
# The conts are named with their matching lesion making it easier to look up
# the roi
def contrilateral_patches(crop_size, write_location, batch_numbers):
    import pandas as pd
    print('Creating contilateral patches, size: ', crop_size, '...')
    crops = []
    for batch in batch_numbers:
        # Load in the images and filenames
        file_list_cont = getFileNames(
            '/vol/research/mammo/mammo2/will/data/batches/roi/batch_' +
            str(batch) + '/cont_for_presentation_one_per_studyIUID/')
        spreadsheet = ('/vol/research/mammo/mammo2/will/data/batches/metadata/' +
            str(batch) + '/batch_' + str(batch) + '_IMAGE.xls')
        xls = pd.ExcelFile(spreadsheet)
        sheet0 = xls.parse(0)
        sheet1 = xls.parse(1)
        # conts have the name of their lesions pair
        for count, f_cont in enumerate(file_list_cont): 
            print('Crop', '(', count+1, '/', len(file_list_cont), ')', 'batch ',
                  batch)
            imageSOPIUID = os.path.basename(f_cont)[:-4]
            # Get ROI coords
            roi = {'x1': '', 'x2': '', 'y1': '' ,'y2': '', 'image_width': ''}
            roi['x'] = [getSpreadsheetCell('X1', imageSOPIUID, sheet1),
                        getSpreadsheetCell('X2', imageSOPIUID, sheet1)]
            roi['y'] = [getSpreadsheetCell('Y1', imageSOPIUID, sheet1),
                        getSpreadsheetCell('Y2', imageSOPIUID, sheet1)]
            # Get image width
            img = pydicom.dcmread(f_cont)
            roi['image_width'] = img.Columns

            # Compute contrilateral coords
            roi_cont = {'x': '','y': ''}
            roi_cont['x'] = [roi['image_width'] - roi['x'][0],
                             roi['image_width'] - roi['x'][1]]
            roi_cont['y'] = [roi['y'][0],
                             roi['y'][1]]

            # Take crops
            tmp = img.pixel_array
            x = roi_cont['x']
            y = roi_cont['y']
            c = [round((x[0]+x[1])/2), round((y[0]+y[1])/2)]
            # Pad images before cropping (pad with 0's)
            pad = round(crop_size/2)
            tmp = np.pad(tmp, pad, mode='constant', constant_values=(0))
            # crop
            tmp = (tmp[int(c[1]-crop_size/2+pad):int(c[1]+crop_size/2+pad),
                             int(c[0]-crop_size/2+pad):int(c[0]+crop_size/2+pad)])
            # Reshape from (256, 256) to (256, 256, 1)
            tmp.shape = (tmp.shape[0], tmp.shape[1], 1)
            crops.append(tmp)
    # Save as pickle
    print('Writing pickle...')
    print('len(image_pickle): ', len(crops))
    savePickle(crops, write_location + 'batch_' +
               str(batch_numbers[0]) + '/contrilaterals.pickle')

# Get list of files that are for presentation and have ROIs
# Copy these files to a new folder
def get_ROIs(dst_copy_lesion, lesion_path, spreadsheet, batch = 1, copy = True):
    import pandas as pd
    import os
    from shutil import copyfile
    xls = pd.ExcelFile(spreadsheet)
    sheet1 = xls.parse(1)
    sheet0 = xls.parse(0)

    file_list = getFileNames(lesion_path)
    # Remove files that do not have ROIs (not in the spreadsheet)
    file_list = filter_spreadsheet(file_list, sheet1)
    # Remove file that are not FOR PRESENTATION
    file_list = filter_for_presentation(file_list, sheet0)
    # Remove files so that there is only one per studyIUID
    file_list = filter_for_single_StudyIUID(file_list, sheet1)

    if copy == True:
        # Check to see if destination directory exists
        print('checking to see if following directory exists:\n{}'.format(
            dst_copy_lesion))
        if os.path.isdir(dst_copy_lesion) == False:
            print('Did not exist... creating')
            os.mkdir(dst_copy_lesion)
        for index, path in enumerate(file_list):
            copyfile(path, dst_copy_lesion + '/' + os.path.basename(file_list[index]))
            print(index, '\\', len(file_list), 'batch ', batch )
    return file_list


# This will copy images to a separate folder that have both ROIs, are for
# presentation and ensures that only one image from each StudyIUID is copied
def select_and_copy_dicom_images(batch_numbers):
    #batch_numbers = [1]
    for batch in batch_numbers:
        dicom_files = (
            '/vol/research/mammo/mammo2/will/data/batches/IMAGE_DATABASE/PUBLIC_SHARE/IMAGES/STANDARD_SET/'
            + str(batch) + '/')
        spreadsheet = ('/vol/research/mammo/mammo2/will/data/batches/metadata/' +
            str(batch) + '/batch_' + str(batch) + '_IMAGE.xls')

        lesion_file_list = get_ROIs('/vol/research/mammo/mammo2/will/data/batches/roi/batch_' +
            str(batch) + '/lesions_for_presentation_one_per_studyIUID',
            dicom_files, spreadsheet, copy = True)

        dst_copy_cont = ('/vol/research/mammo/mammo2/will/data/batches/roi/batch_' +
                         str(batch) +
                         '/cont_for_presentation_one_per_studyIUID')
        all_dicom_files = getFileNames(dicom_files)
        get_contrilateral(lesion_file_list, dst_copy_cont, all_dicom_files,
                          spreadsheet, batch)


# Create patches from the images that we separated out
# Both lesions and normal contrilaterals
# Do I already have a function to do this? Probs
def lesion_patches(crop_size, write_location, batch_numbers):
    image_dict = {}
    for batch in batch_numbers:
        # Load in the images and filenames
        dicom_files = (
            '/vol/research/mammo/mammo2/will/data/batches/roi/batch_'
            + str(batch) + '/lesions_for_presentation_one_per_studyIUID/')
        spreadsheet = ('/vol/research/mammo/mammo2/will/data/batches/metadata/' +
            str(batch) + '/batch_' + str(batch) + '_IMAGE.xls')
        print('dicom_files:\n', dicom_files)
        print('spreadsheet:\n', spreadsheet)
        tmp_dicom, tmp_list = getFiles(dicom_files)
        image_dict.update(buildDict(tmp_dicom, tmp_list, spreadsheet, verbose =
                                   True))
        print('len(image_dict): ', len(image_dict))

    # Compute patches from full RGB images
    image_dict = computeCrops(image_dict, crop_size)
    # Create dict ready for pickle
    # key = file name: RGB image
    image_pickle = {}
    for key in image_dict:
        image_pickle.update({key: image_dict[key]['crop']})
    print('Writing pickle...')
    print('len(image_pickle): ', len(image_pickle))
    savePickle(image_pickle, write_location + 'batch_' +
               str(batch_numbers[0]) + '/lesions.pickle')



def main():
    import time
    import os

    # Globals
    CROP_SIZE = 256
    SPREADSHEET = '/vol/research/mammo/mammo2/will/data/batches/metadata/1/batch_1_IMAGE.xls'
    DICOM_FILES =(
    '/vol/research/mammo/mammo2/will/data/batches/roi/batch_1/lesions_for_presentation_one_per_studyIUID/')
    patch_write_location = '/vol/research/mammo/mammo2/will/data/batches/roi/'
    #patch_write_location = \
    #   '/vol/research/mammo/mammo2/will/data/batches/roi_new/'
    #batch_numbers = [1, 3, 5, 6, 7]
    all_batches = [[1], [3], [5], [6], [7], [8], [10], [11], [12], [13], [14],
                   [15], [16], [18], [19], [21], [22],
                   [23], [30]]
    #all_batches = [[1]]

    for batch_numbers in all_batches:
        # Check to see if destination directory exists
        tmp_path = '/vol/research/mammo/mammo2/will/data/batches/roi/batch_' +\
            str(batch_numbers[0])
        print('checking to see if following directory exists:\n{}'.format(
            tmp_path))
        if os.path.isdir(tmp_path) == False:
            print('Did not exist... creating')
            os.mkdir(tmp_path)

        start_time = time.time()
        #select_and_copy_dicom_images(batch_numbers)
        lesion_patches(CROP_SIZE, patch_write_location, batch_numbers)
        #contrilateral_patches(CROP_SIZE, patch_write_location, batch_numbers)
        print('BATCH {} COMPLETED'.format(batch_numbers[0]))
    print('Done: ', round(time.time() - start_time), ' seconds')

if __name__ == "__main__":
    main()

