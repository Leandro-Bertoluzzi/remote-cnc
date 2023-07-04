import os

def getFileNameInFolder(current, searched):
    """
    - Name: getFileNameInFolder
    - Parameter(s):
        - current: string, path to the reference file
        - searched: string, file name of the searched file
    - Description:
        Generates the absolute path to a file in the same folder
    """
    return os.path.join(os.path.split(current)[0], searched)
