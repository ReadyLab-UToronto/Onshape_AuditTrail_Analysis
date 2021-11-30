import csv
import os
import sys
import datetime
import matplotlib.pyplot as plt
import numpy as np
import json
import copy

sys.path.append("API_Related_Files")
#import API_Related_Files.API_Call_Methods

"""
The default data format for audit trails is: 
[index, event time, document, tab, user, description, feature reference, notes] 

Process to download audit trails from Onshape
Tip: 
- Download as an excel file from Onshape, make any necessary edits to the audit trail (cleaning up, deleting/fixing entries, etc) then save as csv file before running analysis on it. Excel sometimes defaults to stripping the seconds off of the event time entries when saving as csv depending on your system time format settings.

We can use datetime to convert the "event time" column strings to datetime objects: 
datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")

Current limitations:
- currently searching only one entry forward and backwards of "insert feature" and "Edit : XXX" entries for 
    "add of modify a sketch" to determine whether the feature inserted/edited was a sketch. This looks like it may catch
    vast majority of cases but still not fool proof. Searching 2 forward/back might introduce other unwanted problems though
- currently lumping time spent on edits with no changes (clicked into edit something then clicked green checkmark without having made any actual changes) together with cancelledEditTime  

Key assumptions: 
- assumes first entry (bottom of csv) is "open document", which marks the beginning of the task
- assumes last entry (top of csv) is "closed document", marking the end of the task
(Currently this requires manually editing the csv file once downloaded from Onshape) 
"""



def read_file(fileName) -> None:
    """
    This function reads audit trails data and performs basic audit trail integrity checks.
    Currently, it checks the indices for being in order and date and time matches the expected format,
    then creates a cleaned version and outputs that as a separate file
    """

    # To store all data in the audit trail csv file
    orig_data = []

    # Builds the filepath by appending the file name to the current work directory
    # The raw participant audit trails should be stored in a subfolder called "Participant_audit_trails"
    filePathName = os.path.join(os.getcwd(), "Participant_audit_trails", fileName)
    # print("Opening file: " + filePathName)

    # Open csv file and copy all rows into "orig_data"
    with open(filePathName, 'r') as csv_file:
        data_reader = csv.reader(csv_file)
        for row in data_reader:
            orig_data.append(row)

    # Check that index column starts at 1 and doesn't skip any numbers
    if str(orig_data[1][0]) != "1":
        print("Index does not start with 1!")
        return -1
    # Next, check if index is in order starting from 1
    totalEntries = len(orig_data) - 1
    # Note: we're doing 1 less than len(orig_data) to not count the top row as an entry since that's the column header

    for index in range(1, totalEntries):
        # print("Checking index: " + str(index) + "  dataset index: " + str(orig_data[index][0]))
        if str(orig_data[index][0]) != str(index):
            print("Index not in order!")
            print("Expected index " + str(index) + " Dataset index " + str(orig_data[index][0]))
            return -1
        else:
            pass

    # Optional:
    # print("INFO: Original input file indices check out")
    # print("INFO: Number of entries in dataset: " + str(totalEntries))

    # call function to clean the csv
    cleanCsv(fileName, orig_data)

    return None

def cleanCsv(fileName, orig_data):
    """
    Clean CSV file to get rid of useless entries
    Entries that get deleted:
        - "Update Part Metadata"
        - "Commit add or edit of part studio feature"
    Purposefully NOT removing "Add or modify a sketch" entries since we'll be using those to identify if an inserted/edited
    feature was a sketch or not during analysis (hopefully this will not be necessary in the future if Onshape updates the
    audit trails)
    """

    # First, create the "filename_cleaned" string, the [:-4] gets rid of the ".csv" part,
    # slotting "_cleaned" before the .csv part. We will save a separate "cleaned" audit trail as output
    cleanedFileName = fileName[:-4] + "_cleaned" + fileName[-4:]
    #print("Output file name= " + cleanedFileName)

    #parentDirectory = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    #outFilePath = os.path.join(parentDirectory, "Participant_audit_trails", cleanedFileName)
    outFilePath = os.path.join(os.getcwd(), "Participant_audit_trails", cleanedFileName)
    #print("Output file path: ", outFilePath)

    # if lines don't contain "commit add" or "metadata" then write the row into the output csv
    # at the same time checks each row to make sure time format is as expected
    with open(outFilePath, "w", newline="") as out_file:
        writer = csv.writer(out_file)

        goodEntries = 0
        # for loop iteration index to be able to display which entry failed the time format check

        for index, row in enumerate(orig_data):
            if "Commit add or edit" in row[5] or "Update Part Metadata" in row[5] or "Delete part studio feature" in row[5]:
                pass
            else:
                # if not those above, then make a copy of this row, re-index, then write to output
                # also re-index while writing the rows, top row (row 0) should say "Index"
                rowCopy = copy.copy(row)
                rowCopy[0]=goodEntries
                if goodEntries == 0:
                    rowCopy[0] = "Index"
                writer.writerow(rowCopy)
                goodEntries += 1


            if index == 0:
                # first row is the text "Index" so don't check for this row
                pass
            else:
                try:
                    row[1] = datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    print("Issue with with date time entry at index: " + str(index))
                    pass
                #print(row[1], " type: ", type(row[1]))

    #print("INFO: Number of entries after scrubbing: " + str(goodEntries-1))

    # now run the analyze function on the cleaned csv that's just been saved
    analyzeAuditTrail(cleanedFileName)

    return None

def timeConverter(totalTime):
    ### This function takes in a datetime object, converts it into number of seconds,
    ### then into minutes and seconds using divmod, then turns the output into
    ### integers, then strings for easier printing (eliminates need to mess with formatting floating point format during print)
    minSec = divmod(totalTime.total_seconds(), 60)
    # divmod returns a tuple of 2 floats (minute, second), convering them to integers
    minutes = str(int(minSec[0]))
    seconds = str(int(minSec[1]))
    return [minutes,seconds]

def analyzeAuditTrail(fileName):
    """
    Function to identify the relevant feature for each audit trail entry based on the description
    Args:
        fileName:

    Returns:
    """

    #fileName += ".csv"
    # current directory is "API_Rel._Files", need to step one directory up first
    # os.pardir adds the ".." to the end of the current wd, then abspath fines the actual path of the parent dir
    #parentDirectory = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    # stepping into the participant audit trails folder, tacking on file name, with .csv tacked on already
    #filePathName = os.path.join(parentDirectory, "Participant_audit_trails", fileName)
    # updated file path with main python file at the root of the project folder
    filePathName = os.path.join(os.getcwd(), "Participant_audit_trails", fileName)
    #print("fileName: " + fileName)
    #print("filePathName: " + filePathName)
    #print("Opening file: " + filePathName)

    data = []  # to store cleaned audit trail data

    # load in data (should be the cleaned .csv)
    with open(filePathName, 'r') as csv_file:
        data_reader = csv.reader(csv_file)
        for row in data_reader:
            data.append(row)

    fileName = fileName.removesuffix(".csv")  # fileName = XX_IDXX_cleaned.csv

    insertFeatureIndices = []
    editFeatureIndices = []
    skippedFeatures = []
    sketchesCreatedNames = []

    # intialize counters (counts instances)
    sketchesCreated = featuresCreated = sketchesEdited = featuresEdited = switchedToDrawing = 0

    # need to initialize the time counters to 0 seconds first
    sketchCreateTime = featureCreateTime = sketchEditTime = featureEditTime = \
        readDrawingTime = partstudioTime = datetime.timedelta(seconds=0)
    cancelledCreateTime = cancelledEditTime = datetime.timedelta(seconds=0)

    # the following counters are operations with no start/end times (noTimeDelta features)
    movedFeature = movedRollbackBar = operationsCancelled = undoRedo = createFolder = \
        renameFeature = showHide = deletedFeature = 0

    # Global variable for controlling how long actions without start & end times should be recorded as (how many seconds)
    noTimeDeltaFeatures = 1 #seconds
    # these features are: operationsCancelled, movedRollbackBar, movedFeature, undoRedo, createFolder, renameFeature, showHide

    # list for hidden markov model building
    HMMList = []
    HMMList_StartEnd = []

    ########################
    # time_series array will be used to build the sequential list of actions
    time_series = []

    """
    Each element in the time_series array has the format: 
    (action type, start time of the action, time duration) 

    E.g.    ("sketch", datetime(00:05:15), datetime(00:00:20)) 
            = did sketching starting at 5 min 15 sec for 20 seconds

    All action_type: 
    -- TO BE DOCUMENTED -- 
    """
    ########################

    # Convert every entry in the event time column from a string into a datetime object
    # Also clear feature reference column (6) in case the file being read already has some existing data
    for row in data[1:]: # skip top row since it's just labels
        #print(str(len(row)))
        row[1] = datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        # the 7th and 8th column might be empty, if so, append a blank entry
        try:
            row[6] = ""
            #print("old row len =" + str(len(row)))
        except IndexError:
            row.append("")
        try:
            row[7] = ""
        except IndexError:
            row.append("")
            #print("new row len =" + str(len(row)))

    # Dealing with the top header row
    # Sometimes the header row will be missing entries, so checking for the proper length, if not, then append as needed
    #print(data[0])
    if len(data[0]) == 6:
        #print("Len is 6")
        data[0].append("")
        data[0].append("")
    elif len(row[0]) == 7:
        #print("Len is 7")
        data[0].append("")

    # then rename row 7 and 8 with proper names
    data[0][6] = "Feature Reference"
    data[0][7] = "HMM Sequence"
    #print(data[0])


    # start range() at 1 to skip the top row, then reverse it to start from the bottom of the csv file
    for i in reversed(range(1,len(data))):
        #print("Currently on index: " + str(i))

        # for adding part studio features (sketches/all other feature)
        if data[i][5] == "Add part studio feature":
            #print("Found add part studio feature at: " + str(i))
            featureStartIndex = i
            while True:
                featureStartIndex -= 1
                #print(featureStartIndex)
                if "Insert feature" in data[featureStartIndex][5]:
                    #print("found Insert feature at index " + str(featureStartIndex))
                    if featureStartIndex in insertFeatureIndices:
                        # check to see if this insert feature has already been matched to another "add ps feature"
                        # if yes, then skip to find the next available
                        pass
                    else:
                        # if "add of modify a sketch" is before or after insert feature, that means the
                        # inserted feature was likely a sketch
                        if "Add or modify a sketch" in data[featureStartIndex + 1][5] or \
                                "Add or modify a sketch" in data[featureStartIndex - 1][5]:
                            #print("Added sketch at: " + str(featureStartIndex))
                            featureName = data[featureStartIndex][5].split(" : ")[1] + " (Sketch)"
                            data[featureStartIndex][6] = featureName
                            data[i][6] = featureName
                            data[featureStartIndex][7] = "End Create"
                            data[i][7] = "Start Create"
                            # add this to the running list of discovered insert feature indices
                            insertFeatureIndices.append(featureStartIndex)
                            # calculate time spent creating a new sketch
                            sketchCreateTime += data[featureStartIndex][1] - data[i][1]
                            timeSeriesEntry = "sketchCreateTime - " + featureName
                            time_series.append((timeSeriesEntry, data[i][1] , (data[featureStartIndex][1] - data[i][1])))
                            sketchesCreated += 1
                            sketchesCreatedNames.append(featureName)
                            HMMList.append("Create")
                            break
                        else:
                            #print("Regular feature added at: " + str(featureStartIndex))
                            featureName = data[featureStartIndex][5].split(" : ")[1]
                            data[featureStartIndex][6] = featureName
                            data[i][6] = featureName
                            data[featureStartIndex][7] = "End Create"
                            data[i][7] = "Start Create"
                            # add this to the running list of discovered insert feature indices
                            insertFeatureIndices.append(featureStartIndex)
                            # calculate time spent creating a new feature
                            featureCreateTime += data[featureStartIndex][1] - data[i][1]
                            timeSeriesEntry = "featureCreateTime - " + featureName
                            time_series.append((timeSeriesEntry, data[i][1], (data[featureStartIndex][1] - data[i][1])))
                            featuresCreated += 1
                            HMMList.append("Create")
                            break

                if "Cancel Operation" in data[featureStartIndex][5]:
                    #print("Operation cancelled at: " + str(featureStartIndex))
                    featureName = "Cancelled add feature"
                    data[featureStartIndex][6] = featureName
                    data[i][6] = featureName
                    #data[featureStartIndex][7] = "End Create"
                    #data[i][7] = "Start Create"
                    # calculate time spent on a cancelled new feature creation
                    cancelledCreateTime += data[featureStartIndex][1] - data[i][1]
                    time_series.append(("cancelCreateTime", data[i][1], (data[featureStartIndex][1] - data[i][1])))
                    operationsCancelled += 1
                    #HMMList.append("Create")
                    break

        # for editing of part studio features (sketches/all other feature)
        elif data[i][5] == "Start edit of part studio feature":
            #print("Found edit of part studio feature at: " + str(i))
            featureStartIndex = i
            HMMList.append("Revise")
            while True:
                featureStartIndex -= 1
                if "Edit :" in data[featureStartIndex][5]:
                    #print("found Edit at index " + str(featureStartIndex))
                    if featureStartIndex in editFeatureIndices:
                        # check to see if this insert feature has already been matched to another "edit ps feature"
                        # if yes, then skip to find the next available
                        pass
                    else:
                        if "Add or modify a sketch" in data[featureStartIndex + 1][5] or \
                                "Add or modify a sketch" in data[featureStartIndex - 1][5]:
                            #print("Edited (Add or modify) sketch at: " + str(featureStartIndex))
                            featureName = data[featureStartIndex][5].split(" : ")[1] + " (Sketch)"
                            data[featureStartIndex][6] = featureName
                            data[i][6] = featureName
                            data[featureStartIndex][7] = "End Edit"
                            data[i][7] = "Start Edit"
                            # add this to the running list of discovered edit feature indices
                            editFeatureIndices.append(featureStartIndex)
                            # calculate time spent editing a sketch
                            sketchEditTime += data[featureStartIndex][1] - data[i][1]
                            timeSeriesEntry = "sketchEditTime - " + featureName
                            time_series.append((timeSeriesEntry, data[i][1] , (data[featureStartIndex][1] - data[i][1])))
                            sketchesEdited += 1
                            break
                        else:
                            #print("Regular feature edit at: " + str(featureStartIndex))
                            featureName = data[featureStartIndex][5].split(" : ")[1]
                            data[featureStartIndex][6] = featureName
                            data[i][6] = featureName
                            data[featureStartIndex][7] = "End Edit"
                            data[i][7] = "Start Edit"
                            # add this to the running list of discovered edit feature indices
                            editFeatureIndices.append(featureStartIndex)
                            # calculate time spent editing a feature
                            featureEditTime += data[featureStartIndex][1] - data[i][1]
                            timeSeriesEntry = "featureEditTime - " + featureName
                            time_series.append((timeSeriesEntry, data[i][1] , (data[featureStartIndex][1] - data[i][1])))
                            featuresEdited += 1
                            break
                # if the next thing following "start edit" is "add or modify a sketch" without an "Edit : ", then
                # that means the user clicked the green checkmark without making any actual changes to a sketch
                elif "Add or modify a sketch" in data[featureStartIndex][5]:
                    # sometimes the "edit" entry can come after the "add or modify a sketch" entry, so we still need to
                    # check to make sure the entry above isn't an feature edit commit
                    # if it is, then this there were in fact modifications done to a sketch feature
                    if "Edit" in data[featureStartIndex - 1][5]:
                        featureName = data[featureStartIndex-1][5].split(" : ")[1] + " (Sketch)"
                        data[featureStartIndex-1][6] = featureName
                        data[i][6] = featureName
                        data[featureStartIndex-1][7] = "End Edit"
                        data[i][7] = "Start Edit"
                        # add this to the running list of discovered edit feature indices
                        editFeatureIndices.append(featureStartIndex)
                        # calculate time spent editing a sketch
                        sketchEditTime += data[featureStartIndex-1][1] - data[i][1]
                        timeSeriesEntry = "sketchEditTime - " + featureName
                        time_series.append((timeSeriesEntry, data[i][1], (data[featureStartIndex-1][1] - data[i][1])))
                        sketchesEdited += 1
                        break
                    else:
                        # if "edit" wasn't found in the entry above, then this was likely a edit with no real changes
                        featureName = "No change edit to a sketch feature"
                        data[featureStartIndex][6] = featureName
                        data[i][6] = featureName
                        data[featureStartIndex][7] = "End Edit"
                        data[i][7] = "Start Edit"
                        # add this to the running list of discovered edit feature indices
                        editFeatureIndices.append(featureStartIndex)
                        # counting this time as same as cancelledEditTime, lumping them together
                        cancelledEditTime += data[featureStartIndex][1] - data[i][1]
                        time_series.append(("cancelledEditTime", data[i][1], (data[featureStartIndex][1] - data[i][1])))
                        operationsCancelled += 1
                        break
                # if another "start edit" or "add part studio feature" is encountered before finding an "edit :", then
                # the user likely started editing a feature, but didn't actually make a change before clicking the green checkmark
                # essentially leaving two "start edit part studio feature" entries back to back
                # similar situation to the no-change edit sitaution for sketches, but in this case there's no entry at all
                elif "Start edit of part studio feature" in data[featureStartIndex][5] or \
                    "Add part studio feature" in data[featureStartIndex][5]:
                    #print("NO CHANGE FEATURE EDIT AT INDEX: " + str(featureStartIndex))
                    featureName = "No change edit to a feature"
                    # only mark the i-th (start) entry with featureName, since there's no ending entry in audit trail
                    data[i][6] = featureName
                    # add this to the running list of discovered edit feature indices
                    editFeatureIndices.append(featureStartIndex)
                    # counting these as zeroDelta times since there's no way to determine for sure how long they spent on these
                    cancelledEditTime += datetime.timedelta(seconds=noTimeDeltaFeatures)
                    time_series.append(("cancelledEditTime", data[i][1], datetime.timedelta(seconds=noTimeDeltaFeatures)))
                    operationsCancelled += 1
                    break
                elif "Cancel Operation" in data[featureStartIndex][5]:
                    #print("Edit operation cancelled at: " + str(featureStartIndex))
                    featureName = "Cancelled edit feature"
                    data[featureStartIndex][6] = featureName
                    data[i][6] = featureName
                    data[featureStartIndex][7] = "End Edit"
                    data[i][7] = "Start Edit"
                    # calculate time spent on a cancelled new feature creation
                    cancelledEditTime += data[featureStartIndex][1] - data[i][1]
                    time_series.append(("cancelledEditTime", data[i][1], (data[featureStartIndex][1] - data[i][1])))
                    operationsCancelled += 1
                    break

        # tracking opening and closing drawings
        elif "BLOB opened" in data[i][5]:
            currentDrawing = data[i][3]
            # search ahead for when this drawing was closed
            featureStartIndex = i
            HMMList.append("Drawing")
            while True:
                featureStartIndex -= 1
                # finds the next "BLOB closed"
                if "BLOB closed" in data[featureStartIndex][5]:
                    # check and see if this "BLOB closed" matches the current drawing
                    if data[featureStartIndex][3] == currentDrawing:
                        data[featureStartIndex][6] = currentDrawing + "(closed)"
                        data[i][6] = currentDrawing + "(opened)"
                        #data[featureStartIndex][7] = "Close Drawing"
                        data[i][7] = "Refer to Drawing"
                        # calculate time spent reading a drawing
                        readDrawingTime += data[featureStartIndex][1] - data[i][1]
                        timeSeriesEntry = "readDrawingTime - " + currentDrawing
                        time_series.append((timeSeriesEntry, data[i][1], (data[featureStartIndex][1] - data[i][1])))
                        switchedToDrawing += 1
                        break
                    else:
                        pass
                else:
                    pass

        # tracking opening and closing partstudios
        elif "PARTSTUDIO opened" in data[i][5]:
            currentPS = data[i][3]
            # search ahead for when this partstudio was closed
            featureStartIndex = i
            #print("partstudio open, index: " + str(i))
            while True:
                featureStartIndex -= 1
                # finds the next "BLOB closed"
                if "PARTSTUDIO closed" in data[featureStartIndex][5]:
                    # check and see if this part studio matches the current part studio
                    # not actually necessary in my dataset since there's only one partstudio
                    #if data[featureStartIndex][3] == currentPS:
                    data[featureStartIndex][6] = currentPS + "(closed)"
                    data[i][6] = currentPS + "(opened)"
                    # calculate time spent inside partstudios (this will overlap with feature creation and edit times)
                    partstudioTime += data[featureStartIndex][1] - data[i][1]
                    time_series.append(("partstudioTime", data[i][1], (data[featureStartIndex][1] - data[i][1])))
                    # no need to track times switched to partstudio since it should be the same as times switched to drawing
                    #print("closed: " + str(featureStartIndex))
                    break
                if featureStartIndex == 1:
                    print("ERROR: Partstudio closed not found! Start index: " + str(i))
                    break

        # tracking moving features or rollback bar
        elif "Move" in data[i][5]:
            if "Rollback bar" in data[i][5]:
                data[i][6] = "-- move rollbackbar +1 --"
                time_series.append(("moveRollbackBar", data[i][1], datetime.timedelta(seconds=noTimeDeltaFeatures)))
                movedRollbackBar += 1
                #HMMList.append("Revise")
                #data[i][7] = "Revise"
            elif "tab" in data[i][5]:
                # moved a tab, not a feature
                data[i][6] = "-- moved tab, ignore --"
            else:
                data[i][6] = "-- move feature +1 --"
                time_series.append(("moveFeature", data[i][1], datetime.timedelta(seconds=noTimeDeltaFeatures)))
                movedFeature += 1
                HMMList.append("Organize")
                data[i][7] = "Organize"

        # tracking undo/redo
        elif "Undo Redo" in data[i][5]:
            # if the undo/redo was done during sketching, the only etry will be "Undo Redo Operation"
            # if the undo/redo is done in partstudio, then there will be one more entry "Undo : 1 step"
            # need to check for this
            #print("Checking undo (or redo) steps, this one's description is : " + data[i][5])
            # the "Undo : " entry can come before or after "Undo Redo Operation"
            if "Undo : " in data[i-1][5]:
                data[i-1][6] = "-- Feature undoRedo +1 --"
                data[i][6] = "-- Feature undoRedo --"
            elif "Undo : " in data[i+1][5]:
                data[i+1][6] = "-- Feature undoRedo +1 --"
                data[i][6] = "-- Feature undoRedo --"
            elif "Redo : " in data[i-1][5]:
                data[i + 1][6] = "-- Feature undoRedo +1 --"
                data[i][6] = "-- Feature undoRedo --"
            elif "Redo : " in data[i+1][5]:
                data[i + 1][6] = "-- Feature undoRedo +1 --"
                data[i][6] = "-- Feature undoRedo --"
            else:
                data[i][6] = "-- Sketch undoRedo +1 --"
            time_series.append(("undoRedo", data[i][1], datetime.timedelta(seconds=noTimeDeltaFeatures)))
            HMMList.append("Revise")
            #data[i][7] = "Revise"
            # currently grouping all undoRedo together, not separately tracking them
            undoRedo += 1

        # create folder
        elif "Create folder" in data[i][5]:
            data[i][6] = "New folder: " + data[i][5].split(" : ")[1]
            time_series.append(("createFolder", data[i][1], datetime.timedelta(seconds=noTimeDeltaFeatures)))
            createFolder += 1
            HMMList.append("Organize")
            data[i][7] = "Organize"
            #featureName = data[featureStartIndex-1][5].split(" : ")[1] + " (Sketch)"

        elif "Rename" in data[i][5]:
            data[i][6] = "-- renameFeature +1 --"
            time_series.append(("renameFeature", data[i][1], datetime.timedelta(seconds=noTimeDeltaFeatures)))
            renameFeature += 1
            HMMList.append("Organize")
            data[i][7] = "Organize"

        elif "Show" in data[i][5] or "Hide" in data[i][5]:
            data[i][6] = "-- showHide +1 --"
            time_series.append(("showHide", data[i][1], datetime.timedelta(seconds=noTimeDeltaFeatures)))
            showHide += 1

        elif "Add or modify a sketch" in data[i][5]:
            # these entries are already accounted for above, just marking them so they're not blank in the output
            #data[i][6] = "-- add/mod. sketch (accounted for) --"
            data[i][6] = "---"

        elif "Delete" in data[i][5]:
            featureName = data[i][5].split(" : ")[1]
            data[i][6] = "deleted " + featureName
            time_series.append(("deletedFeature", data[i][1], datetime.timedelta(seconds=noTimeDeltaFeatures)))
            deletedFeature += 1
            HMMList.append("Delete")
            data[i][7] = "Delete"

        elif "Close document" in data[i][5]:
            if data[i][0] != str(1):
                print(data[i])
                print("Error! Close document is not the last entry!")
                return -1
            else:
                pass
                #endTime = datetime.datetime.strptime(data[i][1])

        elif "Open document" in data[i][5]:
            #startTime = datetime.datetime.strptime(data[i][1])
            if data[i][0] != str(len(data)-1): # -1 to account for top row not being a valid entry
                print("Error! Open document is not the first entry!")

        # a list of things that I don't want to be accidentally marked as skipped, they're all accounted for in sub-routines of
        # other higher level elif checks
        elif "Edit" in data[i][5] or \
                "Insert feature" in data[i][5] or \
                "Cancel Operation" in data[i][5] or \
                "Create Version" in data[i][5] or \
                "Change size" in data[i][5] or \
                "Change part appearance" in data[i][5] or \
                "Branch Workspace" in data[i][5] or \
                "Suppress" in data[i][5] or \
                "Unsuppress" in data[i][5] or \
                "Unpack" in data[i][5] or \
                "Create variable" in data[i][5] or \
                "Insert tab" in data[i][5] or \
                "BLOB closed" in data[i][5] or \
                "PARTSTUDIO closed" in data[i][5] or \
                "Update version" in data[i][5] or \
                "Create version" in data[i][5] or \
                "Undo : " in data[i][5] or \
                "Redo : " in data[i][5] or \
                "Tab Part Studio 1 Copy 1 of type PARTSTUDIO created by CAD_Study" in data[i][5]:
                #
            #data[i][6] = "-"
            pass

        else:
            print("WARNING: Not yet accounted for entry at index: " + str(i) + "\n\tDescription: " + data[i][5])
            skippedFeatures.append(("Index: " + str(i) + " - Description: " + data[i][5])) # keep track of all skipped features in a list
            #pass

    # print the list of entries that are skipped, to catch anything new that's not currently being checked for
    if skippedFeatures: # if the skippedFeatures list is empty, then it is FALSE, then the if statement won't print
        #print("WARNING: Skipped these entries (indices): " + str(skippedFeatures))
        print("WARNING, skipped some entries, check the 'skipped' JSON file")
        skippedFeatures.insert(0, "Skipped features indices: ")
        fileName = fileName.removesuffix(".csv")  # fileName = XX_IDXX_cleaned.csv
        jsonFileName = os.path.join(os.getcwd(), "Analysis_output", fileName)
        jsonFileName = jsonFileName + "_skipped.json"
        with open(jsonFileName, 'w') as outfile:
            json.dump(skippedFeatures, outfile, indent=0, default=str)

    # write cleaned audit trail to a new file
    # (if needed) first, create the "filename_cleaned" string
    #cleanedFileName = fileName[:-4] + "_cleaned" + fileName[-4:]
    # if the function is fed the cleaned filename already then no need to add "_cleaned" to the name
    #print("Output file name= " + cleanedFileName)
    #parentDirectory = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

    # fileName already includes "_cleaned"
    outFilePath = os.path.join(os.getcwd(), "Participant_audit_trails", fileName + ".csv")
    #print("Output file path: ", outFilePath)

    with open(outFilePath, "w", newline="") as out_file:
        writer = csv.writer(out_file)
        for row in data:
            writer.writerow(row)
    #print("INFO: Output csv file now includes identified relevant features: " + outFilePath)


    ############################################################################
    #### writing timeseries to json output file for easier manual error checking ####
    #print(time_series)
    jsonFileName = os.path.join(os.getcwd(), "Analysis_output", fileName)
    jsonFileName = jsonFileName + "_timeseries.json"
    #print(jsonFileName)
    with open(jsonFileName, 'w') as outfile:
        # indent=0 prints each list item as a new line, makes it easier to visually read
        json.dump(time_series, outfile, indent=0, default=str)
        #json.dump(time_series, outfile, default=str)

    ############################################################################
    ##################### Write HMM list to json output file ###################
    HMMFileName = os.path.join(os.getcwd(), "Analysis_output", fileName)
    HMMFileName = HMMFileName + "_HMM_List.json"
    #print(HMMFileName)
    with open(HMMFileName, 'w') as outfile:
        # indent=0 prints each list item as a new line, makes it easier to visually read
        json.dump(HMMList, outfile, indent=0, default=str)
        #json.dump(HMMList, outfile, default=str)


    ###########################################################################
    ######### Write a separate HMM list with start and ends to output #########
    entriesToSkip = [""] #, "Close Drawing"] # can potentially exclude close drawing as well

    for row in reversed(data[1:]):
        #if row[7]:
        if row[7] not in entriesToSkip:
            HMMList_StartEnd.append(row[7])

    # sometimes we will end up with "open" "open" "closed" "closed", should swap things around to be 2x "open" "closed"
    for i in range(len(HMMList_StartEnd)-1):
        current = HMMList_StartEnd[i]
        next = HMMList_StartEnd[i+1]
        #print(last)
        if current == "Open Drawing" and next == "Open Drawing":
            HMMList_StartEnd[i+1], HMMList_StartEnd[i+2] = HMMList_StartEnd[i+2], HMMList_StartEnd[i+1]
            #print("Doubled up!")

    HMMFileName = os.path.join(os.getcwd(), "Analysis_output", fileName)
    HMMFileName = HMMFileName + "_HMM_StartEnd.json"
    with open(HMMFileName, 'w') as outfile:
        json.dump(HMMList_StartEnd, outfile, indent=0, default=str)
        #json.dump(HMMList_StartEnd, outfile, default=str)

    #############################################
    #### Now deal with creating the eventplot ###

    # first, calculate a few derived time values
    startTime = data[-1][1]
    endTime = data[1][1]
    totalTime = endTime - startTime

    partstudioTimeAccountedFor = \
        sketchCreateTime+featureCreateTime+sketchEditTime+featureEditTime+cancelledCreateTime+cancelledEditTime #+readDrawingTime

    unaccountedTime = partstudioTime - partstudioTimeAccountedFor
    #print("Unaccounted time: " + str(unaccountedTime))
    unaccountedRatio = unaccountedTime / partstudioTime
    #print("unaccountedRatio (raw): " + str(unaccountedRatio))
    if partstudioTime < partstudioTimeAccountedFor:
        print("partstudioTime < partstudioTimeAcocuntedFor! ")
        unaccountedTime = 999
        unaccountedRatio = 999

    ##### Append data to existing database #####
    database = []
    databaseFileName = os.path.join(os.getcwd(), "Analysis_output", "Audit_Trail_Database.csv")
    #print(databaseFileName)
    with open(databaseFileName, 'r') as csv_file:
        data_reader = csv.reader(csv_file)
        for row in data_reader:
            database.append(row)
    # parentDirectory = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    # outFilePath = os.path.join(parentDirectory, "Participant_audit_trails", databaseFileName)
    # print("Output file path: ", outFilePath)


    rowEntry = [fileName,
                totalTime,
                partstudioTime,
                partstudioTimeAccountedFor,
                unaccountedTime,
                readDrawingTime,
                sketchCreateTime,
                featureCreateTime,
                sketchEditTime,
                featureEditTime,
                cancelledCreateTime,
                cancelledEditTime,
                # unaccounted ratio is a floating point number, want to show it as % in database
                round(unaccountedRatio,4)*100,
                "Counters ->",
                sketchesCreated,
                featuresCreated,
                operationsCancelled,
                sketchesEdited,
                featuresEdited,
                switchedToDrawing,
                movedFeature,
                movedRollbackBar,
                undoRedo,
                createFolder,
                renameFeature,
                showHide,
                deletedFeature
    ]

    # write over existing entry if a row with the same filename already exists
    newEntryFlag = True

    # iterate through database's first column, if there's an existing entry with the same file name, set flag to False
    for index, row in enumerate(database):
        #print("Index = " + str(index))
        #print("Checking row" + str(index) + " with entry: "+ row[0])
        if row[0] == fileName:
            database[index] = rowEntry
            #print("found, index:" + str(index))
            newEntryFlag = False

    # otherwise add new row to the end
    if newEntryFlag is True:
        database.append(rowEntry)
        #print("adding new entry to database: \n" + str(rowEntry))

    with open(databaseFileName, "w", newline="") as out_file:
        writer = csv.writer(out_file)
        for row in database:
            writer.writerow(row)


    ##############################################
    ############## Printing outputs ##############

    """
    print("\n### Timers ###")
    totalTime = timeConverter(totalTime)
    print("Total time spent: " + totalTime[0] + " minutes," + totalTime[1] + " seconds")
    readDrawingTime = timeConverter(readDrawingTime)
    print("Total readDrawingTime: " + readDrawingTime[0] + " minutes," + readDrawingTime[1] + " seconds")
    partstudioTime = timeConverter(partstudioTime)
    print("Total partstudioTime (based on Onshape tabs): " + partstudioTime[0] + " minutes," + partstudioTime[1] + " seconds")
    #print("Total partstudioTime (raw): " + str(partstudioTime))
    partstudioTimeAccountedFor = timeConverter(partstudioTimeAccountedFor)
    print("Of which "+ partstudioTimeAccountedFor[0] + " minutes, " + partstudioTimeAccountedFor[1] + " seconds "
          "are accounted for with one of the following individual time trackers:")
    print("Time unaccounted for (panning, zooming, UI surfing, \nsitting in PS thinking, organizing feature tree, renaming feautres): {:.2%}".format(unaccountedRatio))

    print("")
    sketchCreateTime = timeConverter(sketchCreateTime)
    print("Total sketchCreateTime: " + sketchCreateTime[0] + " minutes," + sketchCreateTime[1] + " seconds")
    featureCreateTime = timeConverter(featureCreateTime)
    print("Total featureCreateTime: " + featureCreateTime[0] + " minutes," + featureCreateTime[1] + " seconds")
    sketchEditTime = timeConverter(sketchEditTime)
    print("Total sketchEditTime: " + sketchEditTime[0] + " minutes," + sketchEditTime[1] + " seconds")
    featureEditTime = timeConverter(featureEditTime)
    print("Total featureEditTime: " + featureEditTime[0] + " minutes," + featureEditTime[1] + " seconds")
    cancelledCreateTime = timeConverter(cancelledCreateTime)
    print("Total cancelledCreateTime: " + cancelledCreateTime[0] + " minutes," + cancelledCreateTime[1] + " seconds")
    cancelledEditTime = timeConverter(cancelledEditTime)
    print("Total cancelledEditTime: " + cancelledEditTime[0] + " minutes," + cancelledEditTime[1] + " seconds")

    print("\n### Counters ###")
    print("sketchesCreated: " + str(sketchesCreated))
    print("featuresCreated: " + str(featuresCreated))
    print("operationsCancelled: " + str(operationsCancelled))
    print("sketchesEdited: " + str(sketchesEdited))
    print("featuresEdited: " + str(featuresEdited))
    print("switchedToDrawing: " + str(switchedToDrawing))
    print("movedFeature: " + str(movedFeature))
    print("movedRollbackBar: " + str(movedRollbackBar))
    print("undoRedo: " + str(undoRedo))
    print("createFolder: " + str(createFolder))
    print("renameFeature: " + str(renameFeature))
    print("showHide: " + str(showHide))
    print("deletedFeature: " + str(deletedFeature))

    """

    #print("\nsketch names: ")
    #print(*sketchesCreatedNames, sep="\n")

    #print(time_series)
    # Plotting the time series event plot
    #position = [[],[],[],[],[],[],[],[],[],[],[],[],[],[]]  # x coordinates, a list of 14 lists
    position = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]  # x coordinates, a list of 18 lists
    # (added 3 extra for plotting different drawings in different colours

    for (action, timestamp, duration) in time_series:
        if "readDrawingTime - Changes" in action:
            for i in range(duration.seconds):
                position[17].append((timestamp - startTime).seconds + i)
        elif "readDrawingTime - Step 4" in action:
            for i in range(duration.seconds):
                position[16].append((timestamp - startTime).seconds + i)
        elif "readDrawingTime - Step 3" in action:
            for i in range(duration.seconds):
                position[15].append((timestamp - startTime).seconds + i)
        elif "readDrawingTime - Step 2" in action:
            for i in range(duration.seconds):
                position[14].append((timestamp - startTime).seconds + i)
        elif "readDrawingTime - Step 1" in action:
            for i in range(duration.seconds):
                position[13].append((timestamp - startTime).seconds + i)
        elif "sketchCreateTime" in action:
            for i in range(duration.seconds):
                position[12].append((timestamp - startTime).seconds + i)
        elif "featureCreateTime" in action:
            for i in range(duration.seconds):
                position[11].append((timestamp - startTime).seconds + i)
        elif "sketchEditTime" in action:
            for i in range(duration.seconds):
                position[10].append((timestamp - startTime).seconds + i)
        elif "featureEditTime" in action:
            for i in range(duration.seconds):
                position[9].append((timestamp - startTime).seconds + i)
        elif action == "cancelledCreateTime":
            for i in range(duration.seconds):
                position[8].append((timestamp - startTime).seconds + i)
        elif action == "cancelledEditTime":
            for i in range(duration.seconds):
                position[7].append((timestamp - startTime).seconds + i)
        elif action == "moveRollbackBar":
            for i in range(duration.seconds):
                position[6].append((timestamp - startTime).seconds + i)
        elif action == "moveFeature":
            for i in range(duration.seconds):
                position[5].append((timestamp - startTime).seconds + i)
        elif action == "renameFeature":
            for i in range(duration.seconds):
                position[4].append((timestamp - startTime).seconds + i)
        elif action == "undoRedo":
            for i in range(duration.seconds):
                position[3].append((timestamp - startTime).seconds + i)
        elif action == "deletedFeature":
            for i in range(duration.seconds):
                position[2].append((timestamp - startTime).seconds + i)
        elif action == "showHide":
            for i in range(duration.seconds):
                position[1].append((timestamp - startTime).seconds + i)
        elif action == "createFolder":
            for i in range(duration.seconds):
                position[0].append((timestamp - startTime).seconds + i)

    offset =  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 13, 13, 13, 13] # y coordinates, last 4 are for drawings so superimposing them
    linelengths1 = 7 * [0.5] + 6 * [0.9] + 5*[0.9] #last 5 controls height of readDrawing bars
    colors1 = 7*["orangered"] + 6*["mediumblue"] + ["red"] + ["gold"] + ["lime"] + ["purple"]+ ["blue"]
                                    #Drawing:       #1          #2         #3         #4        #changes

    plt.rcParams["figure.figsize"] = (10, 5)  # Resize the plot
    # task2 plots are much shorter in duration, so resize the overall plot to be narrower
    if "Task2" in fileName:
        plt.rcParams["figure.figsize"] = (8, 5)  # Resize the plot
    plt.eventplot(position, lineoffsets=offset,linelengths=linelengths1, linewidths= 1, colors=colors1)
    y = ["Created folder", "Show/hide", "Deleted feature", "Undo/Redo", "Rename feature", "Move feature",
         "Move rollback bar", "Cancelled edit", "Cancelled creation", "Edit PS feature", "Edit sketch",
         "Create PS feature", "Create sketch feature", "Read drawing"]
    plt.yticks(np.arange(len(y)), y)
    plt.xlabel("Time (s)")
    # removing "_cleaned" from the plot title
    fileName = fileName.removesuffix("_cleaned")
    #print(fileName)
    # add filename as title
    plt.title(fileName, fontdict=None, loc='center', pad=6)
    plt.tight_layout()

    saveFigLocation = os.path.join(os.getcwd(), "Analysis_output", fileName + "_cleaned")
    plt.savefig(saveFigLocation) #, bbox_inches='tight'

    #plt.show()
    plt.close()

    return None


###############################################################################
#fileName = input("Enter file name (with .csv): ")
#fileName = "BT_ID01_Task1.csv"
#read_file(fileName)

# need to run this on the cleaned file
#fileName = fileName+"_cleaned.csv"
#analyzeAuditTrail(fileName)

#"""
for root,dirs,files in os.walk("Participant_audit_trails"):
    for name in files:
        #print(os.path.join(root, name))
        if "cleaned" not in name:
            print("\n########################################################")
            print("Opening and analyzing: " + name)
            read_file(name)
#"""


"""
# for analyzing one specific file
name = "ID01_BT_Task2.csv"
#name = str(os.getcwd()) + "/Participant_audit_trails/" + name
print(name)
read_file(name)
"""

