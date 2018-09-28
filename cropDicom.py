from cropDicomFunctions import *
# _______Conterlateral____________
# Get file names of selected lesion dicom images
# Using the spreadsheet find the contrilateral images
# Copy these images to a folder

def get_contrilateral(file_list_lesion, dst_copy_cont, all_dicom_files, spreadsheet, batch = 1):
    import pandas as pd
    from shutil import copyfile
    import pydicom
    import fnmatch
    xls = pd.ExcelFile(spreadsheet)
    sheet1 = xls.parse(1)
    sheet0 = xls.parse(0)

    print('Finding the contrilateral images...')
    cont_image_paths_to_copy = []
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
        for tmp_ImageSOPIUID in sheet0['ImageSOPIUID']:
            for _ in tmp_properties:
                tmp_properties[_] = getSpreadsheetCell(_, tmp_ImageSOPIUID,
                                                       sheet0)
            if tmp_properties == properties_to_match:
                matches['ImageSOPIUID'].append(tmp_ImageSOPIUID)
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

    # Copy the contilateral images to a folder
    print('Copying the contrilateral patches...')
    for index, path in enumerate(cont_image_paths_to_copy):
        copyfile(path, dst_copy_cont + '/' +
                 os.path.basename(cont_image_paths_to_copy[index]))
        #print(os.path.basename(
        #    cont_image_paths_to_copy[index]), 
        #    '\nis cont to:\n',
        #    os.path.basename(file_list_lesion[index]),
        #    '\n')
        print(index + 1, '/', len(cont_image_paths_to_copy), 'batch ', batch )



def contrilateral_patches():
    for f in file_list_lesion:
        studyIUID = os.path.basename(f)[:-4]
        indx = [_ == key for _ in sheet['ImageSOPIUID']].index(True)
        # Get ROI coords
        roi = {'x1': '', 'x2': '', 'y1': '' ,'y2': '', 'image_width': ''}
        roi['x1'] = getSpreadsheetCell('X1', imageSOPIUID, sheet1)
        roi['x2'] = getSpreadsheetCell('X2', imageSOPIUID, sheet1)
        roi['y1'] = getSpreadsheetCell('Y1', imageSOPIUID, sheet1)
        roi['y2'] = getSpreadsheetCell('Y2', imageSOPIUID, sheet1)
        # Get image width
        img = pydicom.dcmread(f)
        roi['image_width'] = img.Columns

        # Compute contrilateral coords
        roi_cont = {'x1': '', 'x2': '', 'y1': '' ,'y2': ''}
        roi_cont['x1'] = roi['image_width'] - roi['x2']
        roi_cont['x2'] = roi['image_width'] - roi['x1']
        roi_cont['y1'] = roi['y1']
        roi_cont['y2'] = roi['y2']



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
def select_and_copy_dicom_images():
    batch_numbers = [1, 3, 5, 6, 7]
    batch_numbers = [1]
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
    dicom_img = np.asarray([]) # DELETE
    file_list = [] # DELETE
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
    print('Done')
    # Build a dict and convert the dicom files to RGB
    #image_dict = buildDict(dicom_img, file_list, spreadsheet)

    # Compute patches from full RGB images
    image_dict = computeCrops(image_dict, crop_size)
    #writeCropsToDisk(image_dict, write_location, crop_size)
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
    select_and_copy_dicom_images()

if __name__ == "__main__":
    main()
