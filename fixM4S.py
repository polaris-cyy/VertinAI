import os
import subprocess

def fixM4S(targetPath, outputPath=None, bufSize:int = 256 * 1024 * 1024) -> str:
    assert bufSize > 0
    if outputPath is None:
        outputPath = f"{os.path.dirname(targetPath)}/temp_{os.path.basename(targetPath)}"  
    with open(targetPath, 'rb') as targetFile:
        header = targetFile.read(32)    
        newHeader = header.replace(b'000000000', b'')
        newHeader = newHeader.replace(b'$', b' ')
        newHeader = newHeader.replace(b'avc1', b'')
        with open(os.path.join(outputPath, os.path.basename(targetPath)), 'wb') as outputFile:
            outputFile.write(newHeader)
            i = targetFile.read(bufSize)
            while i:
                outputFile.write(i)
                i = targetFile.read(bufSize)
    return outputPath

def fixM4S_from_folder(targetFolder=None, outputFolder=None, bufSize: int = 256 * 1024 * 1024) -> str:
    assert bufSize > 0
    if targetFolder is None:
        targetFolder = os.path.join(os.getcwd(), "data")
    if outputFolder is None:
        outputFolder = os.path.join(os.path.dirname(targetFolder), "fixedM4S")
    if not os.path.isdir(outputFolder):
        os.makedirs(outputFolder)
    
    print("Fixing M4S files in folder: ", targetFolder)
    for targetPath in os.listdir(targetFolder):
        targetPath = os.path.join(targetFolder, targetPath)
        if os.path.isfile(targetPath) and targetPath.endswith(".m4s"):
            fixM4S(targetPath, outputFolder, bufSize)
        elif os.path.isdir(targetPath):
            fixM4S_from_folder(targetPath, os.path.join(outputFolder, os.path.basename(targetPath)), bufSize)
    return outputFolder

def modify_extension(targetPath):
    if not os.path.isfile(targetPath):
        raise FileNotFoundError(f"{targetPath} not found")
    if not targetPath.endswith(".m4s"):
        return
    
    print(f"Converting {targetPath} to mp3 or mp4")
    fileName, fileExtension = os.path.splitext(os.path.basename(targetPath))
    if "30280" in fileName: 
        if targetPath.replace('.m4s', '.mp3') in os.listdir(os.path.dirname(targetPath)):
            print(f"{targetPath.replace('.m4s', '.mp3')} already exists, skipping...")
            os.remove(targetPath)
            return
        cmd = f"ffmpeg -loglevel quiet -i {targetPath} -q:a 0 {targetPath.replace('.m4s', '.mp3')}"
    else:
        if targetPath.replace('.m4s', '.mp4') in os.listdir(os.path.dirname(targetPath)):
            print(f"{targetPath.replace('.m4s', '.mp4')} already exists, skipping...")
            os.remove(targetPath)
            return
        cmd = f"ffmpeg -loglevel quiet -i {targetPath} -c copy {targetPath.replace('.m4s', '.mp4')}"
    subprocess.call(cmd, shell=True)
    os.remove(targetPath)
    
def modify_extension_from_folder(targetFolder):
    if targetFolder is None:
        targetFolder = os.path.join(os.getcwd(), "fixedM4S")
    assert os.path.isdir(targetFolder)
    for targetPath in os.listdir(targetFolder):
        targetPath = os.path.join(targetFolder, targetPath)
        if os.path.isfile(targetPath) and targetPath.endswith(".m4s"):
            modify_extension(targetPath)
        elif os.path.isdir(targetPath):
            modify_extension_from_folder(targetPath)