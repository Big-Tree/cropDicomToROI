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


def get_contrilateral(file_list_lesion, dst_copy_cont, all_dicom_files, spreadsheet, batch = 1):
    from functools import partial
    import multiprocessing as mp
    import pandas as pd
    from shutil import copyfile
    import pydicom
    import fnmatch
    import os
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
        matches = {'ImageSOPIUID':[], 'path':[]}

        func = partial(multiprocess_cont_match, tmp_properties, properties_to_match, sheet0)
        results = pool.map(func, sheet0['ImageSOPIUID'])
        results = np.asarray(results)
        matches_multi = dict(matches)
        matches['ImageSOPIUID'] = results[results!=None]


        #for tmp_ImageSOPIUID in sheet0['ImageSOPIUID']:
        #    for _ in tmp_properties:
        #        tmp_properties[_] = getSpreadsheetCell(_, tmp_ImageSOPIUID,
        #                                               sheet0)
        #    if tmp_properties == properties_to_match:
        #        matches['ImageSOPIUID'].append(tmp_ImageSOPIUID)
        #if matches == matches_multi:
        #    print('M A T C H')
        #else:
        #    print('Nooooooooooooooooooooooooooooooo')
        #    print(matches_multi, '\n', matches)
        # Get file path of the matches
        for match_ImageSOPIUID in matches['ImageSOPIUID']:
            search = fnmatch.filter(
                all_dicom_files, '*' + match_ImageSOPIUID + '*')
            matches['path'].append(search[0])

        print(len(matches['ImageSOPIUID']), ' matches', '(', f_index, '/',
              len(file_list_lesion), ')', 'batch ', batch)
        if len(matches['path']) != 0:
            # Sometimes there are no contrilateral images, sometimes there is
            # more than 1
            cont_image_paths_to_copy.append(matches['path'][0])
            lesion_names_with_cont.append(os.path.basename(f))

    # Copy the contilateral images to a folder
    with open(dst_copy_cont + '/lesion_to_cont_details.txt', 'w') as text_file:
        text_file.write('Format:\nLesion --- Contralateral')
        for count, (cont_path, lesion_name) in enumerate(zip(
                cont_image_paths_to_copy, lesion_names_with_cont)):
            copyfile(cont_path, dst_copy_cont + '/' + lesion_name)
            text_file.write('\n' + lesion_name[0:-4] + ' --- ' +
                            os.path.basename(cont_path)[0:-4])
            print(count + 1, '/', len(cont_image_paths_to_copy), 'batch ', batch )



def contrilateral_patches(crop_size, write_location, spreadsheet):
    import pandas as pd
    print('Creating contilateral patches, size: ', crop_size, '...')
    xls = pd.ExcelFile(spreadsheet)
    sheet0 = xls.parse(0)
    sheet1 = xls.parse(1)
    batch_numbers = [1, 3, 5, 6, 7]
    image_dict = {}
    for batch in batch_numbers:
        # Load in the images and filenames
        file_list_lesion = getFileNames(
            '/vol/research/mammo2/will/data/batches/roi/batch_' +
            str(batch) + '/lesions_for_presentation_one_per_studyIUID/')
        file_list_cont = getFileNames(
            '/vol/research/mammo2/will/data/batches/roi/batch_' +
            str(batch) + '/cont_for_presentation_one_per_studyIUID/')
        spreadsheet = ('/vol/research/mammo2/will/data/batches/metadata/' +
            str(batch) + '/batch_' + str(batch) + '_IMAGE.xls')
        print('file_list_lesion:\n', file_list_lesion)
        print('file_list_cont:\n', file_list_cont)
        print('spreadsheet:\n', spreadsheet)
    crops = {}
    for f_lesion, f_cont in zip(file_list_lesion, file_list_cont):
        ImageSOPIUID = os.path.basename(f_lesion)[:-4]
        indx = [_ == ImageSOPIUID for _ in sheet1['ImageSOPIUID']].index(True)
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
        pad = crop_size/2
        tmp = np.pad(tmp, pad, mode='constant', constant_values=(0))
        crops.update({'ImageSOPIUID': tmp[int(c[1]-crop_size/2+pad):int(c[1]+crop_size/2+pad),
                         int(c[0]-crop_size/2+pad):int(c[0]+crop_size/2+pad)]})
        # Reshape from (256, 256) to (256, 256, 1)
        crops['ImageSOPIUID'] = np.reshape(img[key]['crop'],
                                      (img[key]['crop'].shape[0],
                                       img[key]['crop'].shape[1],
                                       1))
    # Save as pickle
    print('Writing pickle...')
    print('len(image_pickle): ', len(crops))
    savePickle(crops, write_location + 'cont_batches_' +
               str(min(batch_numbers)) + '-' + str(max(batch_numbers))+ '.pickle')

# Get list of files that are for presentation and have ROIs
# Copy these files to a new folder
def get_ROIs(dst_copy_lesion, lesion_path, spreadsheet, batch = 1, copy = True):
    import pandas as pd
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
            '/vol/research/mammo2/will/data/batches/IMAGE_DATABASE/PUBLIC_SHARE/IMAGES/STANDARD_SET/'
            + str(batch) + '/')
        spreadsheet = ('/vol/research/mammo2/will/data/batches/metadata/' +
            str(batch) + '/batch_' + str(batch) + '_IMAGE.xls')

        lesion_file_list = get_ROIs('/vol/research/mammo2/will/data/batches/roi/batch_' +
            str(batch) + '/lesions_for_presentation_one_per_studyIUID',
            dicom_files, spreadsheet, copy = False)

        dst_copy_cont = ('/vol/research/mammo2/will/data/batches/roi/batch_' +
                         str(batch) +
                         '/cont_for_presentation_one_per_studyIUID')
        all_dicom_files = getFileNames(dicom_files)
        get_contrilateral(lesion_file_list, dst_copy_cont, all_dicom_files,
                          spreadsheet, batch)


# Create patches from the images that we separated out
# Do I already have a function to do this? Probs
def create_patches(crop_size, write_location, spreadsheet):
    batch_numbers = [1, 3, 5, 6, 7]
    image_dict = {}
    for batch in batch_numbers:
        # Load in the images and filenames
        dicom_files = (
            '/vol/research/mammo2/will/data/batches/roi/batch_'
            + str(batch) + '/lesions_for_presentation_one_per_studyIUID/')
        spreadsheet = ('/vol/research/mammo2/will/data/batches/metadata/' +
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
    savePickle(image_pickle, write_location + 'batches_' +
               str(min(batch_numbers)) + '-' + str(max(batch_numbers))+ '.pickle')



def main():
    # Globals
    CROP_SIZE = 256
    SPREADSHEET = '/vol/research/mammo2/will/data/batches/metadata/1/batch_1_IMAGE.xls'
    DICOM_FILES =(
    '/vol/research/mammo2/will/data/batches/roi/batch_1/lesions_for_presentation_one_per_studyIUID/')
    patch_write_location = '/vol/research/mammo2/will/data/batches/roi/'

    #create_patches(CROP_SIZE, patch_write_location, SPREADSHEET)
    select_and_copy_dicom_images(batch_numbers = [1, 3, 5, 6, 7])
    #contrilateral_patches(CROP_SIZE, patch_write_location, SPREADSHEET)

if __name__ == "__main__":
    main()
