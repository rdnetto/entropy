#!/usr/bin/python
'''
    # DESCRIPTION:
    # Variables container

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

import os
import commands
import string
import random
import sys


# Specifications of the content of etpData
# THIS IS THE KEY PART OF ENTROPY BINARY PACKAGES MANAGEMENT
# DO NOT EDIT THIS UNLESS YOU KNOW WHAT YOU'RE DOING !!
etpData = {
    'name': u"", # the Package Name
    'version': u"", # the Package version plus our -etpXX revision
    'description': u"", # the Package description
    'category': u"", # the gentoo category
    'chost': u"", # the CHOST used to compile it
    'cflags': u"", # CFLAGS used
    'cxxflags': u"", # CXXFLAGS used
    'homepage': u"", # home page of the package
    'useflags': u"", # USE flags used
    'license': u"", # License adpoted
    'keywords': u"", # supported ARCHs (by the SRC)
    'binkeywords': u"", # supported ARCHs (by the BIN)
    'branch': u"", # package branch location
    'download': u"", # link to download the binary package
    'digest': u"", # md5 hash of the .tbz2 package
    'sources': u"", # link to the sources
    'slot': u"", # this is filled if the package is slotted
    'content': u"", # content of the package (files)
    'mirrorlinks': u"", # =mirror://openoffice|link1|link2|link3
    'dependencies': u"", # dependencies
    'rundependencies': u"", # runtime dependencies + version
    'conflicts': u"", # blockers
    'etpapi': u"", # Entropy API revision
    'datecreation': u"", # mtime of the .tbz2 file
    'neededlibs': u"", # libraries needed bye the applications in the package
    'size': u"", # the package size
    'versiontag': u"", # particular version tag
    'provide': u"" # like, cups provides dep virtual/lpr
}

# Entropy database SQL initialization Schema and data structure
etpSQLInitDestroyAll = """
DROP TABLE IF EXISTS etpData;
DROP TABLE IF EXISTS baseinfo;
DROP TABLE IF EXISTS extrainfo;
DROP TABLE IF EXISTS content;
DROP TABLE IF EXISTS dependencies;
DROP TABLE IF EXISTS rundependencies;
DROP TABLE IF EXISTS rundependenciesxt;
DROP TABLE IF EXISTS dependenciesreference;
DROP TABLE IF EXISTS provide;
DROP TABLE IF EXISTS conflicts;
DROP TABLE IF EXISTS neededlibs;
DROP TABLE IF EXISTS libraries;
DROP TABLE IF EXISTS mirrorlinks;
DROP TABLE IF EXISTS sources;
DROP TABLE IF EXISTS sourcesreference;
DROP TABLE IF EXISTS useflags;
DROP TABLE IF EXISTS useflagsreference;
DROP TABLE IF EXISTS keywords;
DROP TABLE IF EXISTS binkeywords;
DROP TABLE IF EXISTS keywordsreference;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS licenses;
DROP TABLE IF EXISTS flags;
DROP TABLE IF EXISTS installedtable;
"""

etpSQLInit = """

CREATE TABLE baseinfo (
    idpackage INTEGER PRIMARY KEY,
    atom VARCHAR,
    idcategory INTEGER,
    name VARCHAR,
    version VARCHAR,
    versiontag VARCHAR,
    revision INTEGER,
    branch VARCHAR,
    slot VARCHAR,
    idlicense INTEGER,
    etpapi INTEGER
);

CREATE TABLE extrainfo (
    idpackage INTEGER,
    description VARCHAR,
    homepage VARCHAR,
    download VARCHAR,
    size VARCHAR,
    idflags INTEGER,
    digest VARCHAR,
    datecreation VARCHAR
);

CREATE TABLE content (
    idpackage INTEGER,
    file VARCHAR
);

CREATE TABLE provide (
    idpackage INTEGER,
    atom VARCHAR
);

CREATE TABLE dependencies (
    idpackage INTEGER,
    iddependency INTEGER
);

CREATE TABLE rundependencies (
    idpackage INTEGER,
    iddependency INTEGER
);

CREATE TABLE dependenciesreference (
    iddependency INTEGER PRIMARY KEY,
    dependency VARCHAR
);

CREATE TABLE conflicts (
    idpackage INTEGER,
    conflict VARCHAR
);

CREATE TABLE neededlibs (
    idpackage INTEGER,
    idlibrary INTEGER
);

CREATE TABLE libraries (
    idlibrary INTEGER PRIMARY KEY,
    libraryname VARCHAR
);

CREATE TABLE mirrorlinks (
    mirrorname VARCHAR,
    mirrorlink VARCHAR
);

CREATE TABLE sources (
    idpackage INTEGER,
    idsource INTEGER
);

CREATE TABLE sourcesreference (
    idsource INTEGER PRIMARY KEY,
    source VARCHAR
);

CREATE TABLE useflags (
    idpackage INTEGER,
    idflag INTEGER
);

CREATE TABLE useflagsreference (
    idflag INTEGER PRIMARY KEY,
    flagname VARCHAR
);

CREATE TABLE keywords (
    idpackage INTEGER,
    idkeyword INTEGER
);

CREATE TABLE binkeywords (
    idpackage INTEGER,
    idkeyword INTEGER
);

CREATE TABLE keywordsreference (
    idkeyword INTEGER PRIMARY KEY,
    keywordname VARCHAR
);

CREATE TABLE categories (
    idcategory INTEGER PRIMARY KEY,
    category VARCHAR
);

CREATE TABLE licenses (
    idlicense INTEGER PRIMARY KEY,
    license VARCHAR
);

CREATE TABLE flags (
    idflags INTEGER PRIMARY KEY,
    chost VARCHAR,
    cflags VARCHAR,
    cxxflags VARCHAR
);

CREATE TABLE installedtable (
    idpackage INTEGER,
    repositoryname VARCHAR
);

"""

# Entropy directories specifications
# THIS IS THE KEY PART OF ENTROPY BINARY PACKAGES MANAGEMENT
# DO NOT EDIT THIS UNLESS YOU KNOW WHAT YOU'RE DOING !!
# the ARCHs that we support
ETP_ARCHS = ["x86", "amd64"] # maybe ppc someday
ETP_API = "1"
# ETP_ARCH_CONST setup
if os.uname()[4] == "x86_64":
    ETP_ARCH_CONST = "amd64"
else:
    ETP_ARCH_CONST = "x86"

ETP_REVISION_CONST = "%ETPREV%"
ETP_DIR = "/var/lib/entropy"
ETP_TMPDIR = "/tmp"
ETP_RANDOM = str(random.random())[2:7]
ETP_TMPFILE = "/.random-"+ETP_RANDOM+".tmp"
ETP_REPODIR = "/packages/"+ETP_ARCH_CONST
ETP_PORTDIR = "/portage"
ETP_DISTFILESDIR = "/distfiles"
ETP_DBDIR = "/database/"+ETP_ARCH_CONST
ETP_DBFILE = "packages.db"
ETP_DBCLIENTFILE = "equo.db"
ETP_CLIENT_REPO_DIR = "/client"
ETP_UPLOADDIR = "/upload/"+ETP_ARCH_CONST
ETP_STOREDIR = "/store/"+ETP_ARCH_CONST
ETP_SMARTAPPSDIR = "/smartapps/"+ETP_ARCH_CONST
ETP_CONF_DIR = "/etc/entropy"
ETP_ROOT_DIR = "/"
ETP_LOG_DIR = ETP_DIR+"/"+"logs"
ETP_SYSLOG_DIR = "/var/log/entropy/"
ETP_VAR_DIR = "/var/tmp/entropy/"
ETP_LOGLEVEL_NORMAL = 1
ETP_LOGLEVEL_VERBOSE = 2
ETP_LOGPRI_INFO = "[ INFO ]"
ETP_LOGPRI_WARNING = "[ WARNING ]"
ETP_LOGPRI_ERROR = "[ ERROR ]"

# NEVER APPEND another \n to this file because it will break the md5 check of reagent
ETP_HEADER_TEXT = "# Sabayon Linux (C - 2007) - Entropy Package Specifications (GPLv2)\n"
MAX_ETP_REVISION_COUNT = 99999

etpConst = {
    'packagestmpdir': ETP_DIR+ETP_TMPDIR, # etpConst['packagestmpdir'] --> temp directory
    'packagestmpfile': ETP_DIR+ETP_TMPDIR+ETP_TMPFILE, # etpConst['packagestmpfile'] --> general purpose tmp file
    'packagesbindir': ETP_DIR+ETP_REPODIR, # etpConst['packagesbindir'] --> repository where the packages will be stored
    			# by the clients: to query if a package has been already downloaded
			# by the servers or rsync mirrors: to store already uploaded packages to the main rsync server
    'smartappsdir': ETP_DIR+ETP_SMARTAPPSDIR, # etpConst['smartappsdir'] location where smart apps files are places
    'packagesstoredir': ETP_DIR+ETP_STOREDIR, # etpConst['packagesstoredir'] --> directory where .tbz2 files are stored waiting for being processed by reagent
    'packagessuploaddir': ETP_DIR+ETP_UPLOADDIR, # etpConst['packagessuploaddir'] --> directory where .tbz2 files are stored waiting for being uploaded to our main mirror
    'portagetreedir': ETP_DIR+ETP_PORTDIR, # directory where is stored our local portage tree
    'distfilesdir': ETP_DIR+ETP_PORTDIR+ETP_DISTFILESDIR, # directory where our sources are downloaded
    'overlaysdir': ETP_DIR+ETP_PORTDIR+"/local/layman", # directory where overlays are stored
    'overlays': "", # variable PORTDIR_OVERLAY
    'overlaysconffile': ETP_CONF_DIR+"/layman.cfg", # layman configuration file
    'confdir': ETP_CONF_DIR, # directory where entropy stores its configuration
    'entropyconf': ETP_CONF_DIR+"/entropy.conf", # entropy.conf file
    'repositoriesconf': ETP_CONF_DIR+"/repositories.conf", # repositories.conf file
    'enzymeconf': ETP_CONF_DIR+"/enzyme.conf", # enzyme.conf file
    'activatorconf': ETP_CONF_DIR+"/activator.conf", # activator.conf file
    'reagentconf': ETP_CONF_DIR+"/reagent.conf", # reagent.conf file
    'databaseconf': ETP_CONF_DIR+"/database.conf", # database.conf file
    'spmbackendconf': ETP_CONF_DIR+"/spmbackend.conf", # Source Package Manager backend configuration (Portage now)
    'mirrorsconf': ETP_CONF_DIR+"/mirrors.conf", # mirrors.conf file
    'remoteconf': ETP_CONF_DIR+"/remote.conf", # remote.conf file
    'equoconf': ETP_CONF_DIR+"/equo.conf", # equo.conf file
    'activatoruploaduris': [], # list of URIs that activator can use to upload files (parsed from activator.conf)
    'activatordownloaduris': [], # list of URIs that activator can use to fetch data
    'binaryurirelativepath': "packages/"+ETP_ARCH_CONST+"/", # Relative remote path for the binary repository.
    'etpurirelativepath': "database/"+ETP_ARCH_CONST+"/", # Relative remote path for the .etp repository.
    							  # TO BE REMOVED? CHECK

    'entropyworkdir': ETP_DIR, # Entropy workdir
    'entropyunpackdir': ETP_VAR_DIR, # Entropy workdir

    'etpdatabaserevisionfile': ETP_DBFILE+".revision", # the local/remote database revision file
    'etpdatabasehashfile': ETP_DBFILE+".md5", # its checksum
    'etpdatabaselockfile': ETP_DBFILE+".lock", # the remote database lock file
    'etpdatabasedownloadlockfile': ETP_DBFILE+".download.lock", # the remote database download lock file
    'etpdatabasetaintfile': ETP_DBFILE+".tainted", # when this file exists, the database is not synced anymore with the online one
    'etpdatabasefile': ETP_DBFILE, # Entropy sqlite database file ETP_DIR+ETP_DBDIR+"/packages.db"
    'etpdatabasefilegzip': ETP_DBFILE+".gz", # Entropy sqlite database file (gzipped)
    'packageshashfileext': ".md5", # Extension of the file that contains the checksum of its releated package file
    
    'databaseloglevel': 1, # Database log level (default: 1 - see database.conf for more info)
    'mirrorsloglevel': 1, # Mirrors log level (default: 1 - see mirrors.conf for more info)
    'remoteloglevel': 1, # Remote handlers (/handlers) log level (default: 1 - see remote.conf for more info)
    'enzymeloglevel': 1 , # Enzyme log level (default: 1 - see enzyme.conf for more info)
    'reagentloglevel': 1 , # Reagent log level (default: 1 - see reagent.conf for more info)
    'activatorloglevel': 1, # # Activator log level (default: 1 - see activator.conf for more info)
    'entropyloglevel': 1, # # Entropy log level (default: 1 - see entropy.conf for more info)
    'equologlevel': 1, # # Equo log level (default: 1 - see equo.conf for more info)
    'spmbackendloglevel': 1, # # Source Package Manager backend log level (default: 1 - see entropy.conf for more info)
    'logdir': ETP_LOG_DIR , # Log dir where ebuilds store their shit
    
    'syslogdir': ETP_SYSLOG_DIR, # Entropy system tools log directory
    'mirrorslogfile': ETP_SYSLOG_DIR+"/mirrors.log", # Mirrors operations log file
    'remotelogfile': ETP_SYSLOG_DIR+"/remote.log", # Mirrors operations log file
    'spmbackendlogfile': ETP_SYSLOG_DIR+"/spmbackend.log", # Source Package Manager backend configuration log file
    'databaselogfile': ETP_SYSLOG_DIR+"/database.log", # Database operations log file
    'enzymelogfile': ETP_SYSLOG_DIR+"/enzyme.log", # Enzyme operations log file
    'reagentlogfile': ETP_SYSLOG_DIR+"/reagent.log", # Reagent operations log file
    'activatorlogfile': ETP_SYSLOG_DIR+"/activator.log", # Activator operations log file
    'entropylogfile': ETP_SYSLOG_DIR+"/entropy.log", # Activator operations log file
    'equologfile': ETP_SYSLOG_DIR+"/equo.log", # Activator operations log file
    
    
    'distcc-status': False, # used by Enzyme, if True distcc is enabled
    'distccconf': "/etc/distcc/hosts", # distcc hosts configuration file
    'etpdatabasedir': ETP_DIR+ETP_DBDIR,
    'etpdatabasefilepath': ETP_DIR+ETP_DBDIR+"/"+ETP_DBFILE,
    'etpdatabaseclientdir': ETP_DIR+ETP_CLIENT_REPO_DIR+ETP_DBDIR,
    'etpdatabaseclientfilepath': ETP_DIR+ETP_CLIENT_REPO_DIR+ETP_DBDIR+"/"+ETP_DBCLIENTFILE, # path to equo.db - client side database file
    
    'etpapi': ETP_API, # Entropy database API revision
    'headertext': ETP_HEADER_TEXT, # header text that can be outputted to a file
    'currentarch': ETP_ARCH_CONST, # contains the current running architecture
    'supportedarchs': ETP_ARCHS, # Entropy supported Archs
    'preinstallscript': "preinstall.sh", # used by the client to run some pre-install actions
    'postinstallscript': "postinstall.sh", # used by the client to run some post-install actions
    
    'branches': ["stable","unstable"], # available branches, do not scramble!
    'branch': "unstable", # choosen branch
    'gentoo-compat': False, # Gentoo compatibility (/var/db/pkg + Portage availability)
    'filesystemdirs': ['/bin','/boot','/emul','/etc','/lib','/lib32','/lib64','/opt','/sbin','/usr','/var'], # directory of the filesystem
    'officialrepositoryname': "sabayonlinux.org", # our official repository name
    'packagedbdir': "/db", # directory of the database file in the .tbz2 package
    'packagedbfile': "/data.db", # database file in the directory above
    'packagecontentdir': "/package", # directory of the package file in the .tbz2 package

 }

# Handlers used by entropy to run and retrieve data remotely, using php helpers
etpHandlers = {
    'md5sum': "md5sum.php?arch="+ETP_ARCH_CONST+"&package=", # md5sum handler
}


# Create paths
if not os.path.isdir(etpConst['entropyworkdir']):
    import getpass
    if getpass.getuser() == "root":
	import re
	for x in etpConst:
	    if (type(etpConst[x]) is str):
		
	        if (not etpConst[x]) or (etpConst[x].endswith(".conf")) or (not etpConst[x].startswith("/")) or (etpConst[x].endswith(".cfg")) or (etpConst[x].endswith(".tmp")) or (etpConst[x].find(".db") != -1) or (etpConst[x].find(".log") != -1):
		    continue
		
		if etpConst[x].find("%ARCH%") != -1:
		    for i in ETP_ARCHS:
			try:
			    mdir = re.subn("%ARCH%",i, etpConst[x])[0]
			    os.makedirs(mdir,0755)
                            os.chown(mdir,0,0)
			except OSError:
			    pass
		else:
		    try:
		        os.makedirs(etpConst[x],0755)
		        os.chown(etpConst[x],0,0)
		    except OSError:
			pass
    else:
        print "you need to run this as root at least once."
        sys.exit(100)

# entropy section
if (not os.path.isfile(etpConst['entropyconf'])):
    print "ERROR: "+etpConst['entropyconf']+" does not exist"
    sys.exit(50)
else:
    f = open(etpConst['entropyconf'],"r")
    entropyconf = f.readlines()
    f.close()
    for line in entropyconf:
	if line.startswith("loglevel|") and (len(line.split("loglevel|")) == 2):
	    loglevel = line.split("loglevel|")[1]
	    try:
		loglevel = int(loglevel)
	    except:
		print "ERROR: invalid loglevel in: "+etpConst['entropyconf']
		sys.exit(51)
	    if (loglevel > -1) and (loglevel < 3):
	        etpConst['entropyloglevel'] = loglevel
	    else:
		print "WARNING: invalid loglevel in: "+etpConst['entropyconf']
		import time
		time.sleep(5)


# database section
if (not os.path.isfile(etpConst['databaseconf'])):
    print "ERROR: "+etpConst['databaseconf']+" does not exist"
    sys.exit(50)
else:
    f = open(etpConst['databaseconf'],"r")
    databaseconf = f.readlines()
    f.close()
    for line in databaseconf:
	if line.startswith("loglevel|") and (len(line.split("loglevel|")) == 2):
	    loglevel = line.split("loglevel|")[1]
	    try:
		loglevel = int(loglevel)
	    except:
		print "ERROR: invalid loglevel in: "+etpConst['databaseconf']
		sys.exit(51)
	    if (loglevel > -1) and (loglevel < 3):
	        etpConst['databaseloglevel'] = loglevel
	    else:
		print "WARNING: invalid loglevel in: "+etpConst['databaseconf']
		import time
		time.sleep(5)