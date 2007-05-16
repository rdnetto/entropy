#!/usr/bin/python
'''
    # DESCRIPTION:
    # Entropy Database Interface

    Copyright (C) 2007 Fabio Erculiani

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

# Never do "import portage" here, please use entropyTools binding
# EXIT STATUSES: 300-399

from entropyConstants import *
import entropyTools
from outputTools import *
import mirrorTools
from pysqlite2 import dbapi2 as sqlite
#import commands
#import re
import os
import sys
import string

# Logging initialization
import logTools
dbLog = logTools.LogFile(level=etpConst['databaseloglevel'],filename = etpConst['databaselogfile'])


# TIP OF THE DAY:
# never nest closeDB() and re-init inside a loop !!!!!!!!!!!! NEVER !

def database(options):
    if len(options) == 0:
	print_error(yellow(" * ")+red("Not enough parameters"))
	sys.exit(301)

    if (options[0] == "--initialize"):
	
	# do some check, print some warnings
	print_info(green(" * ")+red("Initializing Entropy database..."), back = True)
	dbLog.log(0,"[DB OP] Called database --initialize")
        # database file: etpConst['etpdatabasefilepath']
        if os.path.isfile(etpConst['etpdatabasefilepath']):
	    print_info(red(" * ")+bold("WARNING")+red(": database file already exists. Overwriting."))
	    rc = entropyTools.askquestion("\n     Do you want to continue ?")
	    if rc == "No":
	        sys.exit(0)
	    os.system("rm -f "+etpConst['etpdatabasefilepath'])
	    dbLog.log(0,"[DB OP] Removed old database file")

	# initialize the database
	dbLog.log(0,"[DB OP] Connecting to the database")
        dbconn = etpDatabase(readOnly = False, noUpload = True)
	dbconn.initializeDatabase()
	
	# sync packages directory
	dbLog.log(0,"Syncing binary packages")
	import activatorTools
	activatorTools.packages(["sync","--ask"])
	
	# now fill the database
	pkglist = os.listdir(etpConst['packagesbindir'])

	print_info(green(" * ")+red("Reinitializing Entropy database using Packages in the repository ..."))
	dbLog.log(0,"[DB OP] Preparing to start reinitialization")
	currCounter = 0
	atomsnumber = len(pkglist)
	import reagentTools
	for pkg in pkglist:
	    dbLog.log(0,"[DB OP] Analyzing "+str(pkg))
	    print_info(green(" * ")+red("Analyzing: ")+bold(pkg), back = True)
	    currCounter += 1
	    print_info(green("  (")+ blue(str(currCounter))+"/"+red(str(atomsnumber))+green(") ")+red("Analyzing ")+bold(pkg)+red(" ..."))
	    etpData = reagentTools.extractPkgData(etpConst['packagesbindir']+"/"+pkg)
	    dbLog.log(3,"[DB OP] etpData status (should be properly filled now):")
	    for i in etpData:
		dbLog.log(3,i+": "+etpData[i])
		
	    # remove shait
	    os.system("rm -rf "+etpConst['packagestmpdir']+"/"+pkg)
	    # fill the db entry
	    dbLog.log(0,"[DB OP] Launching etpDatabase.addPackage()")
	    dbconn.addPackage(etpData)
	    dbconn.commitChanges()
	
	log.close()
	dbconn.closeDB()
	print_info(green(" * ")+red("Entropy database has been reinitialized using binary packages available"))

    # used by reagent
    elif (options[0] == "search"):
	mykeywords = options[1:]
	if (len(mykeywords) == 0):
	    print_error(yellow(" * ")+red("Not enough parameters"))
	    sys.exit(302)
	if (not os.path.isfile(etpConst['etpdatabasefilepath'])):
	    print_error(yellow(" * ")+red("Entropy Datbase does not exist"))
	    sys.exit(303)
	# search tool
	print_info(green(" * ")+red("Searching ..."))
	# open read only
	dbconn = etpDatabase(True)
	foundCounter = 0
	for mykeyword in mykeywords:
	    results = dbconn.searchPackages(mykeyword)
	    
	    # regenerate info list
	    _results = []
	    for result in results:
		rslt = []
		rslt = dbconn.retrievePackageInfo(result,"stable")
		if rslt != []:
		    _results.append(rslt[0])
		rslt = []
		rslt = dbconn.retrievePackageInfo(result,"unstable")
		if rslt != []:
		    _results.append(rslt[0])
	    results = _results
	    
	    for result in results:
		
		foundCounter += 1
		print 
		print_info(green(" * ")+bold(result[0]))   # package atom
		print_info(red("\t Name: ")+blue(result[1]))
		print_info(red("\t Installed version: ")+blue(result[2]))
		if (result[3]):
		    print_info(red("\t Description: ")+result[3])
		print_info(red("\t CHOST: ")+blue(result[5]))
		print_info(red("\t CFLAGS: ")+darkred(result[6]))
		print_info(red("\t CXXFLAGS: ")+darkred(result[7]))
		if (result[8]):
		    print_info(red("\t Website: ")+result[8])
		if (result[9]):
		    print_info(red("\t USE Flags: ")+blue(result[9]))
		print_info(red("\t License: ")+bold(result[10]))
		print_info(red("\t Source keywords: ")+darkblue(result[11]))
		print_info(red("\t Binary keywords: ")+green(result[12]))
		print_info(red("\t Package branch: ")+result[13])
		print_info(red("\t Download relative URL: ")+result[14])
		print_info(red("\t Package Checksum: ")+green(result[15]))
		if (result[16]):
		    print_info(red("\t Sources"))
		    sources = result[16].split()
		    for source in sources:
			print_info(darkred("\t    # Source package: ")+yellow(source))
		if (result[17]):
		    print_info(red("\t Slot: ")+yellow(result[17]))
		#print_info(red("\t Blah: ")+result[18]) # I don't need to print mirrorlinks
		if (result[20]):
		    deps = result[20].split()
		    print_info(red("\t Dependencies"))
		    for dep in deps:
			print_info(darkred("\t    # Depends on: ")+dep)
		#print_info(red("\t Blah: ")+result[20]) --> it's a dup of [21]
		if (result[22]):
		    rundeps = result[22].split()
		    print_info(red("\t Built with runtime dependencies"))
		    for rundep in rundeps:
			print_info(darkred("\t    # Dependency: ")+rundep)
		if (result[23]):
		    print_info(red("\t Conflicts with"))
		    conflicts = result[23].split()
		    for conflict in conflicts:
			print_info(darkred("\t    # Conflict: ")+conflict)
		print_info(red("\t Entry API: ")+green(result[24]))
		print_info(red("\t Entry creation date: ")+str(entropyTools.convertUnixTimeToHumanTime(int(result[25]))))
		if (result[26]):
		    print_info(red("\t Built with needed libraries"))
		    libs = result[26].split()
		    for lib in libs:
			print_info(darkred("\t    # Needed library: ")+lib)
		print_info(red("\t Entry revision: ")+str(result[27]))
		#print result
	dbconn.closeDB()
	if (foundCounter == 0):
	    print_warning(red(" * ")+red("Nothing found."))
	else:
	    print
    
    # used by reagent
    elif (options[0] == "dump-package-info"):
	mypackages = options[1:]
	if (len(mypackages) == 0):
	    print_error(yellow(" * ")+red("Not enough parameters"))
	    sys.exit(302)
	# open read only
	dbconn = etpDatabase(True)
	
	for package in mypackages:
	    print_info(green(" * ")+red("Searching package ")+bold(package)+red(" ..."))
	    if entropyTools.isjustpkgname(package) or (package.find("/") == -1):
		print_warning(yellow(" * ")+red("Package ")+bold(package)+red(" is not a complete atom."))
		continue
	    # open db connection
	    if (not dbconn.isPackageAvailable(package)):
		# package does not exist in the Entropy database
		print_warning(yellow(" * ")+red("Package ")+bold(package)+red(" does not exist in Entropy database."))
	        continue
	    
	    myEtpData = entropyTools.etpData.copy()
	    
	    # dump both branches if exist
	    branches = []
	    if (dbconn.isSpecificPackageAvailable(package, branch = "stable")):
		branches.append("stable")
	    if (dbconn.isSpecificPackageAvailable(package, branch = "unstable")):
		branches.append("unstable")
	    
	    for branch in branches:
	        # reset
	        for i in myEtpData:
	            myEtpData[i] = ""
	        for i in myEtpData:
		    myEtpData[i] = dbconn.retrievePackageVar(package,i, branch)
		
		# sort and print
	        etprevision = str(dbconn.retrievePackageVar(package,"revision", branch))
	        filepath = etpConst['packagestmpdir'] + "/" + dbconn.retrievePackageVar(package,"name",branch) + "-" + dbconn.retrievePackageVar(package,"version",branch)+"-"+"etp"+etprevision+"-"+branch+".etp"
	        f = open(filepath,"w")
	        sortList = []
	        for i in myEtpData:
		    sortList.append(i)
	        sortList = entropyTools.alphaSorter(sortList)
	        for i in sortList:
		    if (myEtpData[i]):
		        f.write(i+": "+myEtpData[i]+"\n")
	        f.flush()
	        f.close()
	        print_info(green("    * ")+red("Dump generated in ")+bold(filepath)+red(" ."))

	dbconn.closeDB()

    # used by reagent
    elif (options[0] == "inject-package-info"):
	if (len(options[1:]) == 0):
	    print_error(yellow(" * ")+red("Not enough parameters"))
	    sys.exit(303)
	mypath = options[1:][0]
	if (not os.path.isfile(mypath)):
	    print_error(yellow(" * ")+red("File does not exist."))
	    sys.exit(303)
	
	# revision is surely bumped
	etpDataOut = entropyTools.parseEtpDump(mypath)
	dbconn = etpDatabase(readOnly = False, noUpload = True)
	updated, revision = dbconn.handlePackage(etpDataOut)
	dbconn.closeDB()

	if (updated) and (revision != 0):
	    print_info(green(" * ")+red("Package ")+bold(etpDataOut['category']+"/"+etpDataOut['name']+"-"+etpDataOut['version'])+red(" entry has been updated. Revision: ")+bold(str(revision)))
	elif (updated) and (revision == 0):
	    print_info(green(" * ")+red("Package ")+bold(etpDataOut['category']+"/"+etpDataOut['name']+"-"+etpDataOut['version'])+red(" entry newly created."))
	else:
	    print_info(green(" * ")+red("Package ")+bold(etpDataOut['category']+"/"+etpDataOut['name']+"-"+etpDataOut['version'])+red(" does not need to be updated. Current revision: ")+bold(str(revision)))
	
	"""
	sortList = []
	for i in etpDataOut:
	    sortList.append(i)
	sortList = entropyTools.alphaSorter(sortList)
	"""
	# print out the changes before doing them?
	
    elif (options[0] == "restore-package-info"):
	mypackages = options[1:]
	if (len(mypackages) == 0):
	    print_error(yellow(" * ")+red("Not enough parameters"))
	    sys.exit(302)

	# sync packages directory
	import activatorTools
	activatorTools.packages(["sync","--ask"])

	dbconn = etpDatabase(readOnly = False, noUpload = True)
	
	# validate entries
	_mypackages = []
	for pkg in mypackages:
	    if (dbconn.isPackageAvailable(pkg)):
		_mypackages.append(pkg)
	mypackages = _mypackages
	
	if len(mypackages) == 0:
	    print_error(yellow(" * ")+red("No valid package found. You must specify category/atom-version."))
	    sys.exit(303)
	
	print_info(green(" * ")+red("Reinitializing Entropy database using Packages in the repository ..."))
	
	# get the file list
	pkglist = []
	for pkg in mypackages:
	    # dump both branches if exist
	    branches = []
	    if (dbconn.isSpecificPackageAvailable(pkg, branch = "stable")):
		branches.append("stable")
	    if (dbconn.isSpecificPackageAvailable(pkg, branch = "unstable")):
		branches.append("unstable")
	    for branch in branches:
		pkgfile = dbconn.retrievePackageVar(pkg,"download",branch)
	        pkgfile = pkgfile.split("/")[len(pkgfile.split("/"))-1]
	        pkglist.append(pkgfile)
	
	# validate files
	_pkglist = []
	for file in pkglist:
	    if (not os.path.isfile(etpConst['packagesbindir']+"/"+file)):
	        print_info(yellow(" * ")+red("Attention: ")+bold(file)+red(" does not exist anymore."))
	    else:
		_pkglist.append(file)
	pkglist = _pkglist
	
	currCounter = 0
	atomsnumber = len(pkglist)
	import reagentTools
	for pkg in pkglist:
	    
	    print_info(green(" * ")+red("Analyzing: ")+bold(pkg), back = True)
	    currCounter += 1
	    print_info(green("  (")+ blue(str(currCounter))+"/"+red(str(atomsnumber))+green(") ")+red("Analyzing ")+bold(pkg)+red(" ..."))
	    etpData = reagentTools.extractPkgData(etpConst['packagesbindir']+"/"+pkg)
	    # remove shait
	    os.system("rm -rf "+etpConst['packagestmpdir']+"/"+pkg)
	    # fill the db entry
	    dbconn.handlePackage(etpData)
	    dbconn.commitChanges()

	dbconn.commitChanges()
	dbconn.closeDB()
	print_info(green(" * ")+red("Successfully restored database information for the chosen packages."))


    elif (options[0] == "create-empty-database"):
	mypath = options[1:]
	if len(mypath) == 0:
	    print_error(yellow(" * ")+red("Not enough parameters"))
	    sys.exit(303)
	if (os.path.dirname(mypath[0]) != '') and (not os.path.isdir(os.path.dirname(mypath[0]))):
	    print_error(green(" * ")+red("Supplied directory does not exist."))
	    sys.exit(304)
	print_info(green(" * ")+red("Initializing an empty database file with Entropy structure ..."),back = True)
	connection = sqlite.connect(mypath[0])
	cursor = connection.cursor()
	cursor.execute(etpSQLInitDestroyAll)
	cursor.execute(etpSQLInit)
	connection.commit()
	cursor.close()
	connection.close()
	print_info(green(" * ")+red("Entropy database file ")+bold(mypath[0])+red(" successfully initialized."))

    elif (options[0] == "stabilize") or (options[0] == "unstabilize"):

	if options[0] == "stabilize":
	    stable = True
	else:
	    stable = False
	
	if (stable):
	    print_info(green(" * ")+red("Collecting packages that would be marked stable ..."), back = True)
	else:
	    print_info(green(" * ")+red("Collecting packages that would be marked unstable ..."), back = True)
	
	myatoms = options[1:]
	if len(myatoms) == 0:
	    print_error(yellow(" * ")+red("Not enough parameters"))
	    sys.exit(303)
	# is world?
	if myatoms[0] == "world":
	    # open db in read only
	    dbconn = etpDatabase(readOnly = True)
	    if (stable):
	        pkglist = dbconn.listUnstablePackages()
	    else:
		pkglist = dbconn.listStablePackages()
	    # This is the list of all the packages available in Entropy
	    dbconn.closeDB()
	else:
	    pkglist = []
	    for atom in myatoms:
		# validate atom
		dbconn = etpDatabase(readOnly = True)
		if (stable):
		    pkg = dbconn.searchPackagesInBranch(atom,"unstable")
		else:
		    pkg = dbconn.searchPackagesInBranch(atom,"stable")
		for x in pkg:
		    pkglist.append(x)
	
	# filter dups
	pkglist = list(set(pkglist))
	# check if atoms were found
	if len(pkglist) == 0:
	    print
	    print_error(yellow(" * ")+red("No packages found."))
	    sys.exit(303)
	
	# show what would be done
	if (stable):
	    print_info(green(" * ")+red("These are the packages that would be marked stable:"))
	else:
	    print_info(green(" * ")+red("These are the packages that would be marked unstable:"))

	for pkg in pkglist:
	    print_info(red("\t (*) ")+bold(pkg))
	
	# ask to continue
	rc = entropyTools.askquestion("     Would you like to continue ?")
	if rc == "No":
	    sys.exit(0)
	
	# now mark them as stable
	print_info(green(" * ")+red("Marking selected packages ..."))

	# open db
	dbconn = etpDatabase(readOnly = False, noUpload = True)
	import re
	for pkg in pkglist:
	    print_info(green(" * ")+red("Marking package: ")+bold(pkg)+red(" ..."), back = True)
	    rc, action = dbconn.stabilizePackage(pkg,stable)
	    # @rc: True if updated, False if not
	    # @action: action taken: "stable" for stabilized package, "unstable" for unstabilized package
	    if (rc):
		
		# change download database parameter name
		download = dbconn.retrievePackageVar(pkg, "download", branch = action)
		# change action with the opposite:
		if action == "stable":
		    # move to unstable
		    oppositeAction = "unstable"
		else:
		    oppositeAction = "stable"
		
		download = re.subn("-"+oppositeAction,"-"+action, download)
		if download[1]: # if the name has been converted
		    # change download parameter in the database entry
		    dbconn.writePackageParameter(pkg, "download", download[0], action)
		
		# FIXME: now change file path, locally and remotely. First, locally
		# FIXME: add the code to:
		# - move the file name locally to stable -> unstable (or vice versa)
		# - move the file name remotely to stable -> unstalbe (or vice versa)
		# - update the md5 file?

	dbconn.commitChanges()
	print_info(green(" * ")+red("All the selected packages have been marked as requested. Have fun."))
	dbconn.closeDB()

    elif (options[0] == "sanity-check"):
	print_info(green(" * ")+red("Running sanity check on the database ... "), back = True)
	dbconn = etpDatabase(readOnly = True)
	dbconn.noopCycle()
	dbconn.closeDB()
	print_info(green(" * ")+red("Database sanity check passed."))

    elif (options[0] == "remove"):

	print_info(green(" * ")+red("Scanning packages that would be removed ..."), back = True)
	
	myatoms = options[1:]
	if len(myatoms) == 0:
	    print_error(yellow(" * ")+red("Not enough parameters"))
	    sys.exit(303)

	pkglist = []
	for atom in myatoms:
	    # validate atom
	    dbconn = etpDatabase(readOnly = True)
	    pkg = dbconn.searchPackages(atom)
	    try:
		for x in pkg:
		    pkglist.append(x[0])
	    except:
		pass

	# filter dups
	pkglist = list(set(pkglist))
	# check if atoms were found
	if len(pkglist) == 0:
	    print
	    print_error(yellow(" * ")+red("No packages found."))
	    sys.exit(303)
	
	print_info(green(" * ")+red("These are the packages that would be removed from the database:"))

	for pkg in pkglist:
	    print_info(red("\t (*) ")+bold(pkg))
	
	# ask to continue
	rc = entropyTools.askquestion("     Would you like to continue ?")
	if rc == "No":
	    sys.exit(0)
	
	# now mark them as stable
	print_info(green(" * ")+red("Removing selected packages ..."))

	# open db
	dbconn = etpDatabase(readOnly = False, noUpload = True)
	for pkg in pkglist:
	    print_info(green(" * ")+red("Removing package: ")+bold(pkg)+red(" ..."), back = True)
	    dbconn.removePackage(pkg)
	dbconn.commitChanges()
	print_info(green(" * ")+red("All the selected packages have been removed as requested. To remove online binary packages, just run Activator."))
	dbconn.closeDB()

    # used by reagent
    elif (options[0] == "statistics"):
	print_info(green(" [LOCAL DB STATISTIC]\t\t")+red("Information"))
	# fetch total packages
	dbconn = etpDatabase(readOnly = True)
	totalpkgs = len(dbconn.listAllPackages())
	totalstablepkgs = len(dbconn.listStablePackages())
	totalunstablepkgs = len(dbconn.listUnstablePackages())
	print_info(green(" Total Installed Packages\t\t")+red(str(totalpkgs)))
	print_info(green(" Total Stable Packages\t\t")+red(str(totalstablepkgs)))
	print_info(green(" Total Unstable Packages\t\t")+red(str(totalunstablepkgs)))
	entropyTools.syncRemoteDatabases(justStats = True)
	dbconn.closeDB()

    # used by reagent
    # FIXME: complete this with some automated magic
    elif (options[0] == "md5check"):

	print_info(green(" * ")+red("Integrity verification of the selected packages:"))

	mypackages = options[1:]
	dbconn = etpDatabase(readOnly = True)
	
	# statistic vars
	pkgMatch = 0
	pkgNotMatch = 0
	pkgDownloadedSuccessfully = 0
	pkgDownloadedError = 0
	worldSelected = False
	
	if (len(mypackages) == 0):
	    # check world
	    # create packages list
	    worldSelected = True
	    pkgs2check = dbconn.listAllPackages()
	elif (mypackages[0] == "world"):
	    # check world
	    # create packages list
	    worldSelected = True
	    pkgs2check = dbconn.listAllPackages()
	else:
	    # catch the names
	    pkgs2check = []
	    for pkg in mypackages:
		results = dbconn.searchPackages(pkg)
		for i in results:
		    pkgs2check.append(i[0])

	# order alphabetically
	if (pkgs2check != []):
	    pkgs2check = entropyTools.alphaSorter(pkgs2check)

	if (not worldSelected):
	    print_info(red("   This is the list of the packages that would be checked:"))
	else:
	    print_info(red("   All the packages in the Entropy Packages repository will be checked."))
	
	toBeDownloaded = []
	availList = []
	for i in pkgs2check:
	
	    branches = []
	    if (dbconn.isSpecificPackageAvailable(i, branch = "stable")):
		branches.append("stable")
	    if (dbconn.isSpecificPackageAvailable(i, branch = "unstable")):
		branches.append("unstable")
	
	    for branch in branches:
		pkgfile = dbconn.retrievePackageVar(i,"download",branch)
	        pkgfile = pkgfile.split("/")[len(pkgfile.split("/"))-1]
	        if (os.path.isfile(etpConst['packagesbindir']+"/"+pkgfile)):
		    if (not worldSelected): print_info(green("   - [PKG AVAILABLE] ")+red(i)+" -> "+bold(pkgfile))
		    availList.append(pkgfile)
	        elif (os.path.isfile(etpConst['packagessuploaddir']+"/"+pkgfile)):
		    if (not worldSelected): print_info(green("   - [RUN ACTIVATOR] ")+darkred(i)+" -> "+bold(pkgfile))
	        else:
		    if (not worldSelected): print_info(green("   - [MUST DOWNLOAD] ")+yellow(i)+" -> "+bold(pkgfile))
		    toBeDownloaded.append(pkgfile)
	
	rc = entropyTools.askquestion("     Would you like to continue ?")
	if rc == "No":
	    sys.exit(0)

	notDownloadedPackages = []
	if (toBeDownloaded != []):
	    print_info(red("   Starting to download missing files..."))
	    for uri in etpConst['activatoruploaduris']:
		
		if (notDownloadedPackages != []):
		    print_info(red("   Trying to search missing or broken files on another mirror ..."))
		    toBeDownloaded = notDownloadedPackages
		    notDownloadedPackages = []
		
		for pkg in toBeDownloaded:
		    rc = entropyTools.downloadPackageFromMirror(uri,pkg)
		    if (rc is None):
			notDownloadedPackages.append(pkg)
		    if (rc == False):
			notDownloadedPackages.append(pkg)
		    if (rc == True):
			pkgDownloadedSuccessfully += 1
			availList.append(pkg)
		
		if (notDownloadedPackages == []):
		    print_info(red("   All the binary packages have been downloaded successfully."))
		    break
	
	    if (notDownloadedPackages != []):
		print_warning(red("   These are the packages that cannot be found online:"))
		for i in notDownloadedPackages:
		    pkgDownloadedError += 1
		    print_warning(red("    * ")+yellow(i))
		print_warning(red("   They won't be checked."))
	
	brokenPkgsList = []
	for pkg in availList:
	    print_info(red("   Checking hash of ")+yellow(pkg)+red(" ..."), back = True)
	    storedmd5 = dbconn.retrievePackageVarFromBinaryPackage(pkg,"digest")
	    result = entropyTools.compareMd5(etpConst['packagesbindir']+"/"+pkg,storedmd5)
	    if (result):
		# match !
		pkgMatch += 1
		#print_info(red("   Package ")+yellow(pkg)+green(" is healthy. Checksum: ")+yellow(storedmd5), back = True)
	    else:
		pkgNotMatch += 1
		print_error(red("   Package ")+yellow(pkg)+red(" is _NOT_ healthy !!!! Stored checksum: ")+yellow(storedmd5))
		brokenPkgsList.append(pkg)

	dbconn.closeDB()

	if (brokenPkgsList != []):
	    print_info(blue(" *  This is the list of the BROKEN packages: "))
	    for bp in brokenPkgsList:
		print_info(red("    * Package file: ")+bold(bp))

	# print stats
	print_info(blue(" *  Statistics: "))
	print_info(yellow("     Number of checked packages:\t\t")+str(pkgMatch+pkgNotMatch))
	print_info(green("     Number of healthy packages:\t\t")+str(pkgMatch))
	print_info(red("     Number of broken packages:\t\t")+str(pkgNotMatch))
	if (pkgDownloadedSuccessfully > 0) or (pkgDownloadedError > 0):
	    print_info(green("     Number of downloaded packages:\t\t")+str(pkgDownloadedSuccessfully+pkgDownloadedError))
	    print_info(green("     Number of happy downloads:\t\t")+str(pkgDownloadedSuccessfully))
	    print_info(red("     Number of failed downloads:\t\t")+str(pkgDownloadedError))

############
# Functions and Classes
#####################################################################################

# this class simply describes the current database status

class databaseStatus:

    def __init__(self):
	self.databaseBumped = False
	self.databaseInfoCached = False
	self.databaseLock = False
	#self.database
	self.databaseDownloadLocl = False
	self.databaseAlreadyTainted = False
	
	if os.path.isfile(etpConst['etpdatabasedir']+"/"+etpConst['etpdatabasetaintfile']):
	    self.databaseAlreadyTainted = True

    def isDatabaseAlreadyBumped(self):
	return self.databaseBumped

    def isDatabaseAlreadyTainted(self):
	return self.databaseAlreadyTainted

    def setDatabaseTaint(self,bool):
	self.databaseAlreadyTainted = bool

    def setDatabaseBump(self,bool):
	self.databaseBumped = bool

    def setDatabaseLock(self):
	self.databaseLock = True

    def unsetDatabaseLock(self):
	self.databaseLock = False

    def getDatabaseLock(self):
	return self.databaseLock

    def setDatabaseDownloadLock(self):
	self.databaseDownloadLock = True

    def unsetDatabaseDownloadLock(self):
	self.databaseDownloadLock = False

    def getDatabaseDownloadLock(self):
	return self.databaseDownloadLock

class etpDatabase:

    def __init__(self, readOnly = False, noUpload = False):
	
	self.readOnly = readOnly
	self.noUpload = noUpload
	
	if (self.readOnly):
	    # if the database is opened readonly, we don't need to lock the online status
	    # FIXME: add code for locking the table
	    self.connection = sqlite.connect(etpConst['etpdatabasefilepath'])
	    self.cursor = self.connection.cursor()
	    # set the table read only
	    return

	# check if the database is locked locally
	if os.path.isfile(etpConst['etpdatabasedir']+"/"+etpConst['etpdatabaselockfile']):
	    print_info(red(" * ")+red(" Entropy database is already locked by you :-)"))
	else:
	    # check if the database is locked REMOTELY
	    print_info(red(" * ")+red(" Locking and Syncing Entropy database ..."), back = True)
	    for uri in etpConst['activatoruploaduris']:
	        ftp = mirrorTools.handlerFTP(uri)
	        ftp.setCWD(etpConst['etpurirelativepath'])
	        if (ftp.isFileAvailable(etpConst['etpdatabaselockfile'])) and (not os.path.isfile(etpConst['etpdatabasedir']+"/"+etpConst['etpdatabaselockfile'])):
		    import time
		    print_info(red(" * ")+bold("WARNING")+red(": online database is already locked. Waiting up to 2 minutes..."), back = True)
		    unlocked = False
		    for x in range(120):
		        time.sleep(1)
		        if (not ftp.isFileAvailable(etpConst['etpdatabaselockfile'])):
			    print_info(red(" * ")+bold("HOORAY")+red(": online database has been unlocked. Locking back and syncing..."))
			    unlocked = True
			    break
		    if (unlocked):
		        break

		    # time over
		    print_info(red(" * ")+bold("ERROR")+red(": online database has not been unlocked. Giving up. Who the hell is working on it? Damn, it's so frustrating for me. I'm a piece of python code with a soul dude!"))
		    # FIXME show the lock status

		    print_info(yellow(" * ")+green("Mirrors status table:"))
		    dbstatus = entropyTools.getMirrorsLock()
		    for db in dbstatus:
		        if (db[1]):
	        	    db[1] = red("Locked")
	    	        else:
	        	    db[1] = green("Unlocked")
	    	        if (db[2]):
	        	    db[2] = red("Locked")
	                else:
	        	    db[2] = green("Unlocked")
	    	        print_info(bold("\t"+entropyTools.extractFTPHostFromUri(db[0])+": ")+red("[")+yellow("DATABASE: ")+db[1]+red("] [")+yellow("DOWNLOAD: ")+db[2]+red("]"))
	    
	            ftp.closeFTPConnection()
	            sys.exit(320)

		
	    # if we arrive here, it is because all the mirrors are unlocked so... damn, LOCK!
	    entropyTools.lockDatabases(True)
	
	    # ok done... now sync the new db, if needed
	    entropyTools.syncRemoteDatabases(self.noUpload)
	
	self.connection = sqlite.connect(etpConst['etpdatabasefilepath'])
	self.cursor = self.connection.cursor()

    def closeDB(self):
	
	# if the class is opened readOnly, close and forget
	if (self.readOnly):
	    #self.connection.rollback()
	    self.cursor.close()
	    self.connection.close()
	    return
	
	# FIXME verify all this shit, for now it works...
	if (entropyTools.dbStatus.isDatabaseAlreadyTainted()) and (not entropyTools.dbStatus.isDatabaseAlreadyBumped()):
	    # bump revision, setting DatabaseBump causes the session to just bump once
	    entropyTools.dbStatus.setDatabaseBump(True)
	    self.revisionBump()
	
	if (not entropyTools.dbStatus.isDatabaseAlreadyTainted()):
	    # we can unlock it, no changes were made
	    entropyTools.lockDatabases(False)
	else:
	    print_info(yellow(" * ")+green("Mirrors have not been unlocked. Run activator."))
	
	self.cursor.close()
	self.connection.close()

    def commitChanges(self):
	if (not self.readOnly):
	    self.connection.commit()
	    self.taintDatabase()
	else:
	    self.discardChanges() # is it ok?

    def taintDatabase(self):
	# taint the database status
	f = open(etpConst['etpdatabasedir']+"/"+etpConst['etpdatabasetaintfile'],"w")
	f.write(etpConst['currentarch']+" database tainted\n")
	f.flush()
	f.close()
	entropyTools.dbStatus.setDatabaseTaint(True)

    def untaintDatabase(self):
	entropyTools.dbStatus.setDatabaseTaint(False)
	# untaint the database status
	os.system("rm -f "+etpConst['etpdatabasedir']+"/"+etpConst['etpdatabasetaintfile'])

    def revisionBump(self):
	if (not os.path.isfile(etpConst['etpdatabasedir']+"/"+etpConst['etpdatabaserevisionfile'])):
	    revision = 0
	else:
	    f = open(etpConst['etpdatabasedir']+"/"+etpConst['etpdatabaserevisionfile'],"r")
	    revision = int(f.readline().strip())
	    revision += 1
	    f.close()
	f = open(etpConst['etpdatabasedir']+"/"+etpConst['etpdatabaserevisionfile'],"w")
	f.write(str(revision)+"\n")
	f.flush()
	f.close()

    def isDatabaseTainted(self):
	if os.path.isfile(etpConst['etpdatabasedir']+"/"+etpConst['etpdatabasetaintfile']):
	    return True
	return False

    def discardChanges(self):
	self.connection.rollback()

    # never use this unless you know what you're doing
    def initializeDatabase(self):
	self.cursor.execute(etpSQLInitDestroyAll)
	self.cursor.execute(etpSQLInit)
	self.commitChanges()

    # this function manages the submitted package
    # if it does not exist, it fires up addPackage
    # otherwise it fires up updatePackage
    def handlePackage(self, etpData, forceBump = False):
	if (not self.isPackageAvailable(etpData['category']+"/"+etpData['name']+"-"+etpData['version'])):
	    update, revision, etpDataUpdated = self.addPackage(etpData)
	else:
	    update, revision, etpDataUpdated = self.updatePackage(etpData,forceBump)
	return update, revision, etpDataUpdated

    # default add an unstable package
    def addPackage(self, etpData, revision = 0, wantedBranch = "unstable"):
	# check if the package is slotted

	# Handle package name
	etpData['download'] = etpData['download'].split(".tbz2")[0]
	# add branch name
	etpData['download'] += "-"+wantedBranch+".tbz2"

	# if a similar package exist, enter here
	searchsimilar = self.searchSimilarPackages(etpData['category']+"/"+etpData['name'], branch = wantedBranch)
	removelist = []
	for oldpkg in searchsimilar:
	    # get the package slot
	    slot = self.retrievePackageVar(oldpkg, "slot", branch = wantedBranch)
	    if (etpData['slot'] == slot):
		# remove!
		removelist.append(oldpkg)
	
	for pkg in removelist:
	    self.removePackage(pkg)
	
	# wantedBranch = etpData['branch']
	self.cursor.execute(
		'INSERT into etpData VALUES '
		'(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
		, (	etpData['category']+"/"+etpData['name']+"-"+etpData['version'],
			etpData['name'],
			etpData['version'],
			etpData['description'],
			etpData['category'],
			etpData['chost'],
			etpData['cflags'],
			etpData['cxxflags'],
			etpData['homepage'],
			etpData['useflags'],
			etpData['license'],
			etpData['keywords'],
			etpData['binkeywords'],
			wantedBranch,
			etpData['download'],
			etpData['digest'],
			etpData['sources'],
			etpData['slot'],
			etpData['content'],
			etpData['mirrorlinks'],
			etpData['dependencies'],
			etpData['rundependencies'],
			etpData['rundependenciesXT'],
			etpData['conflicts'],
			etpData['etpapi'],
			etpData['datecreation'],
			etpData['neededlibs'],
			revision,
			)
	)
	self.commitChanges()
	return True, revision, etpData

    # Update already available atom in db
    # returns True,revision if the package has been updated
    # returns False,revision if not
    # FIXME: this must be fixed to work with branches, supporting multiple packages with the same key but different branch
    def updatePackage(self, etpData, forceBump = False):

	# are there any stable packages?
	searchsimilarStable = self.searchSimilarPackages(etpData['category']+"/"+etpData['name'], branch = "stable")
	# filter the one with the same version
	stableFound = False
	for pkg in searchsimilarStable:
	    # get version
	    dbStoredVer = self.retrievePackageVar(pkg, "version", branch = "stable")
	    if etpData['version'] == dbStoredVer:
	        # found it !
		stablePackage = pkg
		stableFound = True
		break
	
	if (stableFound):
	    
	    # in this case, we should compare etpData['neededlibs'] with the db entry to see if there has been a API breakage
	    dbStoredNeededLibs = self.retrievePackageVar(etpData['category'] + "/" + etpData['name'] + "-" + etpData['version'], "neededlibs", "stable")
	    if (etpData['neededlibs'] == dbStoredNeededLibs):
		# it is safe to keep it as stable because of:
		# - name/version match
		# - same libraries requirements
		# setup etpData['branch'] accordingly
		etpData['branch'] = "stable"


	# get selected package revision
	if (self.isSpecificPackageAvailable(etpData['category'] + "/" + etpData['name'] + "-" + etpData['version'] , etpData['branch'])):
	    curRevision = self.retrievePackageVar(etpData['category'] + "/" + etpData['name'] + "-" + etpData['version'], "revision", etpData['branch'])
	else:
	    curRevision = 0

	# do I really have to update the database entry? If the information are the same, drop all
	oldPkgInfo = etpData['category']+"/"+etpData['name']+"-"+etpData['version']
	rc = self.comparePackagesData(etpData, oldPkgInfo, dbPkgBranch = etpData['branch'])
	if (rc) and (not forceBump):
	    return False, curRevision, etpData # in this case etpData content does not matter

	# OTHERWISE:
	# remove the current selected package, if exists
	if (self.isSpecificPackageAvailable(etpData['category'] + "/" + etpData['name'] + "-" + etpData['version'] , etpData['branch'])):
	    self.removePackage(etpData['category']+"/"+etpData['name']+"-"+etpData['version'], branch = etpData['branch'])

	# bump revision nevertheless
	curRevision += 1

	# add the new one
	self.addPackage(etpData,curRevision,etpData['branch'])
	

    # You must provide the full atom to this function
    # FIXME: this must be fixed to work with branches
    def removePackage(self,key, branch = "unstable"):
	key = entropyTools.removePackageOperators(key)
	self.cursor.execute('DELETE FROM etpData WHERE atom = "'+key+'" AND branch = "'+branch+'"')
	self.commitChanges()

    # WARNING: this function must be kept in sync with Entropy database schema
    # returns True if equal
    # returns False if not
    # FIXME: this must be fixed to work with branches
    def comparePackagesData(self,etpData,dbPkgInfo, dbPkgBranch = "unstable"):
	
	myEtpData = etpData.copy()
	
	# reset before using the myEtpData dictionary
	for i in myEtpData:
	    myEtpData[i] = ""

	# fill content
	for i in myEtpData:
	    myEtpData[i] = self.retrievePackageVar(dbPkgInfo,i,dbPkgBranch)
	
	for i in etpData:
	    if etpData[i] != myEtpData[i]:
		return False
	
	return True

    # You must provide the full atom to this function
    def retrievePackageInfo(self,pkgkey, branch = "unstable"):
	pkgkey = entropyTools.removePackageOperators(pkgkey)
	result = []
	self.cursor.execute('SELECT * FROM etpData WHERE atom = "'+pkgkey+'" AND branch = "'+branch+'"')
	for row in self.cursor:
	    result.append(row)
	return result

    # You must provide the full atom to this function
    def retrievePackageVar(self,pkgkey,pkgvar, branch = "unstable"):
	pkgkey = entropyTools.removePackageOperators(pkgkey)
	result = []
	self.cursor.execute('SELECT "'+pkgvar+'" FROM etpData WHERE atom = "'+pkgkey+'" AND branch = "'+branch+'"')
	for row in self.cursor:
	    result.append(row[0])
	if (result):
	    return result[0]
	else:
	    return ""

    # this function returns the variable selected (using pkgvar) in relation to the
    # package associated to a certain binary package file (.tbz2)
    def retrievePackageVarFromBinaryPackage(self,binaryPkgName,pkgvar):
	# search binary package
	result = []
	self.cursor.execute('SELECT "'+pkgvar+'" FROM etpData WHERE download = "'+etpConst['binaryurirelativepath']+binaryPkgName+'"')
	for row in self.cursor:
	    result.append(row[0])
	if len(result) > 0:
	    return result[0]
	else:
	    return ""

    # You must provide the full atom to this function
    # FIXME: add pkgcat/name split?
    # FIXME: do SELECT atom instead of SELECT * ?
    def isPackageAvailable(self,pkgkey):
	pkgkey = entropyTools.removePackageOperators(pkgkey)
	result = []
	self.cursor.execute('SELECT * FROM etpData WHERE atom LIKE "'+pkgkey+'"')
	for row in self.cursor:
	    result.append(row)
	if result == []:
	    return False
	return True

    # This version is more specific and supports branches
    def isSpecificPackageAvailable(self,pkgkey, branch):
	pkgkey = entropyTools.removePackageOperators(pkgkey)
	result = []
	self.cursor.execute('SELECT atom FROM etpData WHERE atom LIKE "'+pkgkey+'" AND branch = "'+branch+'"')
	for row in self.cursor:
	    result.append(row[0])
	if result == []:
	    return False
	return True

    def searchPackages(self,keyword):
	result = []
	self.cursor.execute('SELECT atom FROM etpData WHERE atom LIKE "%'+keyword+'%"')
	for row in self.cursor:
	    result.append(row[0])
	return result

    def searchPackagesInBranch(self,keyword,branch):
	result = []
	self.cursor.execute('SELECT atom FROM etpData WHERE atom LIKE "%'+keyword+'%" AND branch = "'+branch+'"')
	for row in self.cursor:
	    result.append(row[0])
	return result

    # this function search packages with the same pkgcat/pkgname
    # you must provide something like: media-sound/amarok
    # optionally, you can add version too.
    def searchSimilarPackages(self,atom, branch = "unstable"):
	category = atom.split("/")[0]
	name = atom.split("/")[1]
	result = []
	self.cursor.execute('SELECT atom FROM etpData WHERE category = "'+category+'" AND name = "'+name+'" AND branch = "'+branch+'"')
	for row in self.cursor:
	    result.append(row[0])
	return result

    # NOTE: unstable and stable packages are pulled in
    # so, there might be duplicates! that's normal
    def listAllPackages(self):
	result = []
	self.cursor.execute('SELECT atom FROM etpData')
	for row in self.cursor:
	    result.append(row[0])
	return result

    def listAllPackagesTbz2(self):
        result = []
        pkglist = self.listAllPackages()
        for pkg in pkglist:
	    dlUnstable = self.retrievePackageVar(pkg, "download")
	    dlStable = self.retrievePackageVar(pkg, "download", branch = "stable")
	    if (dlUnstable != ""):
		
		result.append(os.path.basename(dlUnstable))
	    if (dlStable != ""):
		result.append(os.path.basename(dlStable))
        # filter dups?
	if (result):
            result = list(set(result))
	return result

    def listStablePackages(self):
	result = []
	self.cursor.execute('SELECT atom FROM etpData WHERE branch = "stable"')
	for row in self.cursor:
	    result.append(row[0])
	return result

    def listUnstablePackages(self):
	result = []
	self.cursor.execute('SELECT atom FROM etpData WHERE branch = "unstable"')
	for row in self.cursor:
	    result.append(row[0])
	return result

    def searchStablePackages(self,atom):
	category = atom.split("/")[0]
	name = atom.split("/")[1]
	result = []
	self.cursor.execute('SELECT atom FROM etpData WHERE category = "'+category+'" AND name = "'+name+'" AND branch = "stable"')
	for row in self.cursor:
	    result.append(row[0])
	return result

    def searchUnstablePackages(self,atom):
	category = atom.split("/")[0]
	name = atom.split("/")[1]
	result = []
	self.cursor.execute('SELECT atom FROM etpData WHERE category = "'+category+'" AND name = "'+name+'" AND branch = "stable"')
	for row in self.cursor:
	    result.append(row[0])
	return result

    # useful to quickly retrieve (and trash) all the data
    # and look for problems.
    def noopCycle(self):
	self.cursor.execute('SELECT * FROM etpData')

    def stabilizePackage(self,atom,stable = True):
	
	action = "unstable"
	removeaction = "stable"
	if (stable):
	    action = "stable"
	    removeaction = "unstable"
	
	if (self.isSpecificPackageAvailable(atom, removeaction)):
	    # ! Get rid of old entries with the same slot, pkgcat/name that
	    # were already marked "stable"
	    # get its pkgname
	    pkgname = self.retrievePackageVar(atom,"name", branch = removeaction)
	    # get its pkgcat
	    category = self.retrievePackageVar(atom,"category", branch = removeaction)
	    # search packages with similar pkgcat/name marked as stable
	    slot = self.retrievePackageVar(atom,"slot", branch = removeaction)
	    # we need to get rid of them
	    results = self.searchStablePackages(category+"/"+pkgname)
	    removelist = []
	    for result in results:
		# have a look if the slot matches
		#print result
		myslot = self.retrievePackageVar(result,"slot", branch = action)
		if (myslot == slot):
		    removelist.append(result)
	    for pkg in removelist:
		self.removePackage(pkg, branch = action)
	    self.cursor.execute('UPDATE etpData SET branch = "'+action+'" WHERE atom = "'+atom+'" AND branch = "'+removeaction+'"')
	    self.commitChanges()
	    return True,action
	return False,action

    def writePackageParameter(self,atom,field,what,branch):
	self.cursor.execute('UPDATE etpData SET '+field+' = "'+what+'" WHERE atom = "'+atom+'" AND branch = "'+branch+'"')
	self.commitChanges()

