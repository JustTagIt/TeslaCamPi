#!/usr/bin/python

# Auto uploader to dropbox
# Monitor TeslaCam, syncing up to dropbox
# Assumes to be run as a cronjob (every 5 mins)
# */5 * * * * /home/pi/dropbox-sync.py

# original reference source: https://www.raspberrypi.org/forums/viewtopic.php?t=164166
# requires: https://github.com/andreafabrizi/Dropbox-Uploader

import os
import subprocess
from subprocess import Popen, PIPE

#The directory to sync
syncdir="/mnt/cam/TeslaCam"
#Path to the Dropbox-uploaded shell script
uploader = "/home/pi/dropbox_uploader.sh"

#If 1 then files will be uploaded. Set to 0 for testing
upload = 1
#If 1 then don't check to see if the file already exists just upload it, if 0 don't upload if already exists
overwrite = 0
#If 1 then crawl sub directories for files to upload
recursive = 1
#Delete local file on successfull upload
deleteLocal = 0
#complete list of filesCopied that are pending deletion (if deleteLocal is set)
filesCopied = list()


#Prints indented output
def print_output(msg, level):
    print((" " * level * 2) + msg)


#Gets a list of files in a dropbox directory
def list_files(path):
    p = Popen([uploader, "list", path], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output = p.communicate()[0].decode("utf-8")

    fileList = list()
    lines = output.splitlines()

    for line in lines:
        if line.startswith(" [F]"):
            line = line[5:]
            line = line[line.index(' ')+1:]
            fileList.append(line)
                   
    return fileList


#Uploads a single file
def upload_file(localPath, remotePath):
    p = Popen([uploader, "upload", localPath, remotePath], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output = p.communicate()[0].decode("utf-8").strip()
    if output.startswith("> Uploading") and output.endswith("DONE"):
        return 1
    else:
        return 0

    
#Uploads files in a directory
def upload_files(path, level):
    fullpath = os.path.join(syncdir,path)
    print_output("Syncing " + fullpath,level)
    if not os.path.exists(fullpath):
        print_output("Path not found: " + path, level)
    else:

        #Get a list of file/dir in the path
        filesAndDirs = os.listdir(fullpath)

        #Group files and directories
        
        files = list()
        dirs = list()

        for file in filesAndDirs:
            filepath = os.path.join(fullpath,file)
            if os.path.isfile(filepath):
                files.append(file)       
            if os.path.isdir(filepath):
                dirs.append(file)

        print_output(str(len(files)) + " Files, " + str(len(dirs)) + " Directories",level)

        #If the path contains files and we don't want to override get a list of files in dropbox
        if len(files) > 0 and overwrite == 0:
            dfiles = list_files(path)

        #Loop through the files to check to upload
        for f in files:                                 
            print_output("Found File: " + f,level)   
            if upload == 1 and (overwrite == 1 or not f in dfiles):
                fullFilePath = os.path.join(fullpath,f)
                relativeFilePath = os.path.join(path,f)  
                print_output("Uploading File: " + f,level+1)   
                if upload_file(fullFilePath, relativeFilePath) == 1:
                    print_output("Uploaded File: " + f,level + 1)
                    filesCopied.append(fullFilePath)
                    #if deleteLocal == 1:
                    #    print_output("Deleting File: " + f,level + 1)
                    #    os.remove(fullFilePath)                        
                else:
                    print_output("Error Uploading File: " + f,level + 1)
                    
        #If recursive loop through the directories   
        if recursive == 1:
            for d in dirs:
                print_output("Found Directory: " + d, level)
                relativePath = os.path.join(path,d)
                upload_files(relativePath, level + 1)
            

                  

                
#Start
upload_files("",1)

# copy all the files first then delete separately... break up to slot in the unload/load gadget sequence for speed
if deleteLocal == 1:
    for f in filesCopied:
        print("Deleting File: " + f)
        os.remove(f)
    
    

    
