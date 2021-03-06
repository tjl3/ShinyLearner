import os, sys, glob

taskType = sys.argv[1]
validationType = sys.argv[2]
description = sys.argv[3]
fsAlgorithmPaths = glob.glob(sys.argv[4])
selectedFeaturesFilePaths = glob.glob(sys.argv[5])
algorithmColumnName = sys.argv[6]

if len(fsAlgorithmPaths) == 0:
    print "[FAILED] No feature-selection algorithm scripts were found!"
    exit(1)

if len(selectedFeaturesFilePaths) == 0:
    print "[FAILED] No selected-features files were found!"
    exit(1)

def getMeanFeatureRank(algorithmFeatureData, featureName):
    featureIndices = [float(x.index(featureName) + 1) for x in algorithmFeatureData if featureName in x]

    if len(featureIndices) == 0:
        return None

    return sum(featureIndices) / len(featureIndices)

def testMeanFeatureRanks(meanFeatureRanks, featureNames, lowerThreshold, upperThreshold, idText):
    if description.startswith("StrongSignal") and len(meanFeatureRanks) < 5:
        print "[FAILED] Not enough features [%i] were in the feature list for %s. {%s}" % (len(featureNames), description, idText)
        return False

    if description.startswith("NoSignal") and len(meanFeatureRanks) <= 2:
        print "[PASSED] None of the signal features were selected for %s. {%s}" % (description, idText)
        return True

    grandMean = sum(meanFeatureRanks) / len(meanFeatureRanks)

    if grandMean > lowerThreshold and grandMean <= upperThreshold:
        print "[PASSED] The mean feature index for %s and %s was %.1f. {%s}" % (",".join(featureNames), description, grandMean, idText)
        return True
    else:
        print "[FAILED] The mean feature index for %s and %s was %.1f. Expected was between %.1f and %.1f. {%s}" % (",".join(featureNames), description, grandMean, lowerThreshold, upperThreshold, idText)
        return False

failedAlgorithms = set()

for selectedFeaturesFilePath in selectedFeaturesFilePaths:
    data = [line.rstrip().split("\t") for line in file(selectedFeaturesFilePath)]
    headerItems = data.pop(0)
    featuresIndex = headerItems.index("Features")
    algorithmIndex = headerItems.index(algorithmColumnName)

    uniqueAlgorithms = list(set([row[algorithmIndex] for row in data]))

    if len(uniqueAlgorithms) == 0:
        print "[FAILED] No algorithm scripts could be found."
        exit(1)

    for algorithm in uniqueAlgorithms:
        idText = "%s - %s - %s - %s" % (taskType, validationType, selectedFeaturesFilePath, algorithm)
        algorithmFeatureData = [row[featuresIndex].split(",") for row in data if row[algorithmIndex] == algorithm]

        if description.startswith("StrongSignal"):
            lowerThreshold = 0
            upperThreshold = 20
        elif description.startswith("NoSignal"):
            lowerThreshold = 15
            #upperThreshold = len(algorithmFeatureData[0])
            upperThreshold = 100000000

        featureNames = set()
        for i in range(1, 6):
            featureNames.add("Feature%s" % i)
        for i in range(51, 56):
            featureNames.add("Feature%s.Low" % i)
            featureNames.add("Feature%s.Medium" % i)

        meanFeatureRanks = [getMeanFeatureRank(algorithmFeatureData, featureName) for featureName in featureNames]
        meanFeatureRanks = [x for x in meanFeatureRanks if x != None]
        success = testMeanFeatureRanks(meanFeatureRanks, featureNames, lowerThreshold, upperThreshold, idText)

        if not success:
            failedAlgorithms.add(algorithm)

print "\n[TEST SUMMARY]\n"
if len(failedAlgorithms) > 0:
    print "The following algorithm(s) failed at least once:"
    for algorithm in failedAlgorithms:
        print "  %s" % algorithm
    exit(1)
else:
    print "Tests passed!\n"
