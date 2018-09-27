from cropDicomFunctions import *
# _______Conterlateral____________
# Get file names
def save_contrilateral_images():
    import pandas as pd
    lesionPath = '/vol/research/mammo2/will/data/batches/roi/batch_1/lesions'
    fileListNames = getFileNames(lesionPath)

    xls = pd.ExcelFile(SPREADSHEET)
    sheet = xls.parse(0)
    contralaterals = []
    for _ in fileListNames:
        imageSOPIUD = os.path.basename(_)[:-4]
        tmp = getContralateral(imageSOPIUD, sheet)
        if tmp != None:
            contralaterals.append(tmp)
    print(len(contralaterals))
    print(len(contralaterals[5]))
    print(contralaterals[1])

# ___________Get ROIs______________

# Get list of files that are for presentation and have ROIs
# Copy these files to a new folder
def get_ROIs(dstCopy, lesion_path, spreadsheet, batch = 1):
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

    for index, path in enumerate(file_list):
        copyfile(path, dstCopy + '/' + os.path.basename(file_list[index]))
        print(index, '\\', len(file_list), 'batch ', batch )


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

        get_ROIs('/vol/research/mammo2/will/data/batches/roi/batch_' +
            str(batch) + '/lesions_for_presentation_one_per_studyIUID',
            dicom_files, spreadsheet)


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

    create_patches(CROP_SIZE, patch_write_location, SPREADSHEET)
    #select_and_copy_dicom_images()

if __name__ == "__main__":
    main()
