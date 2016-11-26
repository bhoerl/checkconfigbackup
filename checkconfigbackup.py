#!/usr/bin/env python

import os
import time
import smtplib
import string
from difflib import SequenceMatcher


def getSize(fileobject):
    fileobject.seek(0,2) # move the cursor to the end of the file
    size = fileobject.tell()
    return size


def gen_backup_path(backup_path):

    # generate initial backup-file name: backup_path/hostname/0001.cfg
    configname = 1
    configbackup = "{0:0>4d}".format(configname);
    newfile = backup_path + configbackup + ".cfg"

    # if backup-file exists count +1 to generate new backup-file name
    while os.path.isfile(newfile):
        configname += 1
        configbackup = "{0:0>4d}".format(configname);
        newfile = backup_path + configbackup + ".cfg"

    # backup-file name -1 is the last backup
    configname -= 1
    lastconfigbackup = "{0:0>4d}".format(configname);
    lastfile = backup_path + lastconfigbackup + ".cfg"

    # backup-file name -2 is the past backup
    configname -= 1
    lastconfigbackup = "{0:0>4d}".format(configname);
    pastfile = backup_path + lastconfigbackup + ".cfg"

    return[lastfile, pastfile]


def main():

    now = time.time()
    week_ago = now - 60*60*24*7
    msg_ratio = ""
    msg_too_small = ""
    msg_too_old = ""
    rootdir = "/opt/omd/sites/nws/Konfigurationsbackup/"

    for backupdir in os.listdir(rootdir):
        try:
            fullbackupdir = rootdir + backupdir + "/"
            fcurrent = fullbackupdir + "current.cfg"
            if os.path.isfile(fcurrent):
                f = open(fcurrent, 'rb')
                if getSize(f) < 1024:
                    msg_too_small += "\nFile smaller than 1KB: " + fcurrent
                if os.path.getmtime(fcurrent) < week_ago:
                    msg_too_old += "\nFile older than 1 week: " + fcurrent
                lastfile, pastfile = gen_backup_path(fullbackupdir)
                text1 = open(lastfile).read()
                text2 = open(pastfile).read()
                m = SequenceMatcher(None, text1, text2)
                # m.ratio is very slow but big improvement if script is executed with pypy
                if m.ratio() < 0.5:
                    msg_ratio += "\nFile changed more than 50 percent. Ratio: " + str(m.ratio())
                    msg_ratio += " " + lastfile
                    msg_ratio += " " + pastfile
                    msg_ratio += getSize(lastfile) - getSize(pastfile)
                    #print "\nFile changed more than 50 percent. Ratio: " + str(m.ratio())
                    #print " " + lastfile
                    #print " " + pastfile
                    #print getSize(lastfile) - getSize(pastfile)
        except:
            #print "Error: " + fullbackupdir
            pass

    if not msg_ratio:
        msg_ratio = "\nNo files found with too big a difference.\n"
    if not msg_too_small:
        msg_too_small = "\nNo small files found.\n"
    if not msg_too_old:
        msg_too_old = "\nNo old files found.\n"

    BODY = string.join((
            "From: nagios@mydomain.com",
            "To: noc@mydomain.com",
            "Subject: Check Configbackup File Integrity" ,
            "",
            msg_too_small + "\n" + msg_too_old + "\n" + msg_ratio
            ), "\r\n")
    server = smtplib.SMTP("MY-SMTP-SERVER")
    server.sendmail("nagios@mydomain.com", ["noc@mydomain.com"], BODY)
    server.quit()

if __name__ == '__main__':
    main()
