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
def get_ROIs(dstCopy, lesion_path, spreadsheet):
    import pandas as pd
    from shutil import copyfile
    xls = pd.ExcelFile(spreadsheet)
    sheet = xls.parse(1)
    sheetPres = xls.parse(0)

    file_list_names = getFileNames(lesion_path)
    #Get list of files that are in the spreadsheet with ROIs
    print('len(file_list_names): ', len(file_list_names))
    file_list_ROI = getFileListROI(file_list_names, sheet, sheetPres)
    print('len(file_list_ROI): ', len(file_list_ROI))
    # Remove images so that there is only ever one per studyIUID
    file_list_ROI = get_file_list_ROI_single(file_list_ROI, sheet)
    #Copy files to new folder
    for index, path in enumerate(file_list_ROI):
        copyfile(path, dstCopy + '/' + os.path.basename(file_list_names[index]))
        print(index, '\\', len(file_list_ROI) )


def main():
    # Globals
    CROP_SIZE = 400
    SPREADSHEET = '/vol/research/mammo2/will/data/batches/metadata/3/batch_3_IMAGE.xls'
    DICOM_FILES = '/vol/research/mammo2/will/data/batches/IMAGE_DATABASE/PUBLIC_SHARE/IMAGES/STANDARD_SET/3/'

    batch_numbers = [1, 3, 5, 6, 7]
    for batch in batch_numbers:
        dicom_files = (
            '/vol/research/mammo2/will/data/batches/IMAGE_DATABASE/PUBLIC_SHARE/IMAGES/STANDARD_SET/'
            + str(batch) + '/')
        spreadsheet = ('/vol/research/mammo2/will/data/batches/metadata/' +
            str(batch) + '/batch_' + str(batch) + '_IMAGE.xls')

        get_ROIs('/vol/research/mammo2/will/data/batches/roi/batch_' +
                 str(batch) + '/lesions_for_presentation_one_per_studyIUID',
            dicom_files, spreadsheet)

if __name__ == "__main__":
    main()
