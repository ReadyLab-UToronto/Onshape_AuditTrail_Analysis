import csv
import os
import sys
import numpy as np
import json
#sys.path.append("Analysis_output")


expertIDs = ["01", "04", "05", "06", "09", "10", "11", "13", "14", "19"]
intermediateIDs = ["02", "03", "07", "08", "12", "15", "16", "17", "18"]


experts_task1_list = []
expertLengths_task1_list = []
experts_task2_list = []
expertLengths_task2_list = []

experts_task1_startEnd = []
expertLengths_task1_startEnd = []
experts_task2_startEnd = []
expertLengths_task2_startEnd = []


intermediates_task1_list = []
intermediateLengths_task1_list = []
intermediates_task2_list = []
intermediateLengths_task2_list = []

intermediates_task1_startEnd = []
intermediateLengths_task1_startEnd = []
intermediates_task2_startEnd = []
intermediateLengths_task2_startEnd = []


all_task1_list = []
all_task2_list = []

all_task1_startEnd = []
all_task2_startEnd = []


def codeHMM(fileName):
    # to store the coded series
    codedSeries = []

    filepath = os.path.join(os.getcwd(), "Analysis_output", fileName)
    print(fileName)
    with open(filepath, "r") as jsonFile:
        data = json.load(jsonFile)
    if "List" in fileName:
        for entry in data:
            if entry == "Drawing":
                codedSeries.append(0)
            elif entry == "Create":
                codedSeries.append(1)
            elif entry == "Revise":
                codedSeries.append(2)
            elif entry == "Delete":
                codedSeries.append(3)
            elif entry == "Organize":
                codedSeries.append(4)
            else:
                print("ERROR ", entry)
    elif "StartEnd" in fileName:
        for entry in data:
            if entry == "Refer to Drawing":
                codedSeries.append(0)
            #elif entry == "Close Drawing":
            #    codedSeries.append(1)
            elif entry == "Start Create":
                codedSeries.append(1)
            elif entry == "End Create":
                codedSeries.append(2)
            elif entry == "Start Edit":
                codedSeries.append(3)
            elif entry == "End Edit":
                codedSeries.append(4)
            elif entry == "Delete":
                codedSeries.append(5)
            elif entry == "Organize":
                codedSeries.append(6)
            else:
                print("ERROR ", entry)

    if "List" in fileName:
        #print("LIST")
        if fileName[2:4] in expertIDs and "Task1" in fileName:
            experts_task1_list.append(codedSeries)
            expertLengths_task1_list.append(len(codedSeries))
        elif fileName[2:4] in expertIDs and "Task2" in fileName:
            experts_task2_list.append(codedSeries)
            expertLengths_task2_list.append(len(codedSeries))
        elif fileName[2:4] in intermediateIDs and "Task1" in fileName:
            intermediates_task1_list.append(codedSeries)
            intermediateLengths_task1_list.append(len(codedSeries))
        elif fileName[2:4] in intermediateIDs and "Task2" in fileName:
            intermediates_task2_list.append(codedSeries)
            intermediateLengths_task2_list.append(len(codedSeries))
        else:
            print("Error")
    elif "StartEnd" in fileName:
        #print("StartEnd")
        if fileName[2:4] in expertIDs and "Task1" in fileName:
            experts_task1_startEnd.append(codedSeries)
            expertLengths_task1_startEnd.append(len(codedSeries))
        elif fileName[2:4] in expertIDs and "Task2" in fileName:
            experts_task2_startEnd.append(codedSeries)
            expertLengths_task2_startEnd.append(len(codedSeries))
        elif fileName[2:4] in intermediateIDs and "Task1" in fileName:
            intermediates_task1_startEnd.append(codedSeries)
            intermediateLengths_task1_startEnd.append(len(codedSeries))
        elif fileName[2:4] in intermediateIDs and "Task2" in fileName:
            intermediates_task2_startEnd.append(codedSeries)
            intermediateLengths_task2_startEnd.append((len(codedSeries)))
        else:
            print("Error")
    else:
        print("ERROR")

    print(data)
    print(codedSeries)
    print("")



for root,dirs,files in os.walk("Analysis_output"):
    for name in files:
        #print(os.path.join(root, name))
        if "cleaned_HMM_List" in name:
            #print("\n########################################################")
            #print("Opening and analyzing: " + name)
            #print(name)
            #codeHMM(name)
            pass

        if "cleaned_HMM_StartEnd" in name:
            #print(name)
            codeHMM(name)


jsonFileName = os.path.join(os.getcwd(), "Analysis_output", "HMMdatabase.json")
output = {
    #"Expert Task 1 List": experts_task1_list,
    #"Expert Task 1 Lengths (List)" : expertLengths_task1_list,
    #"Expert Task 2 List" : experts_task2_list,
    #"Expert Task 2 lengths (List)" : expertLengths_task2_list,
    #"Intermediate Task 1 List" : intermediates_task1_list,
    #"Intermediate Task 1 Lengths (List)" :intermediateLengths_task1_list,
    #"Intermediate Task 2 List" : intermediates_task2_list,
    #"Intermediate Task 2 Lengths (List)" :intermediateLengths_task2_list,
    "Expert Task 1 StartEnd": experts_task1_startEnd,
    "Expert Task 1 Lengths (SE)": expertLengths_task1_startEnd,
    "Expert Task 2 StartEnd": experts_task2_startEnd,
    "Expert Task 2 lengths (SE)": expertLengths_task2_startEnd,
    "Intermediate task 1 StartEnd": intermediates_task1_startEnd,
    "Intermediate Task 1 Lengths (SE)": intermediateLengths_task1_startEnd,
    "Intermediate task 2 StartEnd": intermediates_task2_startEnd,
    "Intermediate Task 2 Lengths (SE)": intermediateLengths_task2_startEnd,
}

with open(jsonFileName, 'w') as outfile:
    # indent=0 prints each list item as a new line, makes it easier to visually read
    """
    for item in output:
        outfile.write(json.dumps(item, indent=0))
        outfile.write("\n")
    """
    json.dump(output, outfile, default=str)

"""
print("Expert task 1 (List): ")
print(experts_task1_list)
print(expertLengths_task1_list)
print("Expert task 2 (List):")
print(experts_task2_list)
print(expertLengths_task2_list)
print("Intermediate task 1 (List): ")
print(intermediates_task1_list)
print(intermediateLengths_task1_list)
print("Intermediate task 2 (List): ")
print(intermediates_task2_list)
print(intermediateLengths_task2_list)
"""

print("")

print("Expert task 1 (SE): ")
print(experts_task1_startEnd)
print(expertLengths_task1_startEnd)
print("Expert task 2 (SE):")
print(experts_task2_startEnd)
print(expertLengths_task2_startEnd)
print("Intermediate task 1 (SE): ")
print(intermediates_task1_startEnd)
print(intermediateLengths_task1_startEnd)
print("Intermediate task 2 (SE): ")
print(intermediates_task2_startEnd)
print(intermediateLengths_task2_startEnd)


