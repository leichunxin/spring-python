#!/usr/bin/python
"""
   Copyright 2006-2008 SpringSource (http://springsource.com), All Rights Reserved

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.       
"""
from datetime import datetime
from glob import glob
import os
import sys
import getopt
import shutil

############################################################################
# Get external properties and load into a dictionary. NOTE: These properties
# files mimic Java props files.
############################################################################

p = {}

# Default settings, before reading the properties file
p["targetDir"] = "target"
p["testDir"] = "%s/test-results/xml" % p["targetDir"]
p["packageDir"] = "%s/artifacts" % p["targetDir"]

# Override defaults with a properties file
inputProperties = [property.split("=") for property in open("springpython.properties").readlines()
                   if not (property.startswith("#") or property.strip() == "")]
filter(p.update, map((lambda prop: {prop[0].strip(): prop[1].strip()}), inputProperties))


############################################################################
# Read the command-line, and assemble commands. Any invalid command, print
# usage info, and EXIT.
############################################################################

def usage():
    """This function is used to print out help either by request, or if an invalid option is used."""
    print
    print "Usage: python build.py [command]"
    print
    print "\t--help\t\t\tprint this help message"
    print "\t--clean\t\t\tclean out this build by deleting the %s directory" % p["targetDir"]
    print "\t--test\t\t\trun the test suite, leaving all artifacts in %s" % p["testDir"]
    print "\t--package\t\tpackage everything up into a tarball for release to sourceforge in %s" % p["packageDir"]
    print "\t--build-stamp [tag]\tfor --package, this specifies a special tag, generating version tag '%s-<tag>'" % p["version"]
    print "\t\t\t\tIf this option isn't used, default will be tag will be '%s-<current time>'" % p["version"]
    print "\t--publish\t\tpublish this release to the deployment server"
    print "\t--register\t\tregister this release with http://pypi.python.org/pypi"
    print "\t--docs-html-multi\t\tgenerate HTML documentation, split up into separate sections"
    print "\t--docs-html-single\t\tgenerate HTML documentation in a single file"
    print "\t--docs-pdf\t\tgenerate PDF documentation"
    print "\t--docs-all\t\tgenerate all documents"
    print

try:
    optlist, args = getopt.getopt(sys.argv[1:],
                                  "hct",
                                  ["help", "clean", "test", "package", "build-stamp=", \
                                   "publish", "register", \
                                   "docs-html-multi", "docs-html-single", "docs-pdf", "docs-all"])
except getopt.GetoptError:
    # print help information and exit:
    print "Invalid command found in %s" % sys.argv
    usage()
    sys.exit(2)

############################################################################
# Pre-generate needed values
############################################################################

# Default build stamp value
buildStamp = "BUILD-%s" % datetime.now().strftime("%Y%m%d%H%M%S")

############################################################################
# Definition of operations this script can do.
############################################################################

def clean(dir):
    print "Removing '%s' directory" % dir
    if os.path.exists(dir):
        shutil.rmtree(dir)

def test(dir):
    os.makedirs(dir)
    os.system("nosetests --with-nosexunit --source-folder=src --where=test/springpythontest --xml-report-folder=%s" % dir)
    
    # TODO(9/5/2008 GLT): Capture coverage data that is visible to bamboo. Does coverage have an API to view .coverage file?
    # With coverage... (copied from former bamboo.sh, not yet tested in this configuration)
    #os.system("nosetests --with-nosexunit --with-coverage --xml-report-folder=build --cover-package=springpython")

def package(dir, version):
    os.makedirs(dir)
    os.system("cd src     ; python setup.py --version %s sdist ; mv dist/* .. ; \\rm -rf dist ; \\rm -f MANIFEST" % version)
    os.system("cd samples ; python setup.py --version %s sdist ; mv dist/* .. ; \\rm -rf dist ; \\rm -f MANIFEST" % version)
    os.system("mv *.tar.gz %s" % dir)

def publish():
    """TODO(8/28/2008 GLT): Implement automated solution for this."""
    print "+++ Upload the tarballs using sftp manually to <user>@frs.sourceforge.net, into dir uploads and create a release."

def register(version):
    """TODO(8/28/2008 GLT): Test this part when making official release and registering to PyPI."""
    os.system("cd src     ; python setup.py --version %s register" % version)
    os.system("cd samples ; python setup.py --version %s register" % version)

# Using glob, generate a list of files, then use map to go over each item, and copy it
# from source to destination.
def copy(src, dest, patterns):
    map(lambda pattern: [shutil.copy(file, dest) for file in glob(src + pattern)], patterns)

def setup(root, stylesheets=True):
    if not os.path.exists(root + "/images/"):
        print "+++ Creating " + root + "/images/"
        os.makedirs(root + "/images/")

    copy(
         p["doc.ref.dir"]+"/src/images/",
         root + "/images/",
         ["*.gif", "*.svg", "*.jpg", "*.png"])
    
    if stylesheets:
        copy(
             p["doc.ref.dir"]+"/styles/",
             root,
             ["*.css", "*.js"])

def docs_multi(version):
    root = p["targetDir"] + "/" + p["dist.ref.dir"] + "/html"

    setup(root)
    
    cur = os.path.abspath(".")
    os.chdir(root)
    ref = cur + "/" + p["doc.ref.dir"]
    os.system("java -classpath " + os.path.pathsep.join(glob(ref + "/lib/*.jar")) + \
        " -Xmx256M -XX:MaxPermSize=128m com.icl.saxon.StyleSheet " + \
        ref+"/src/index.xml " + ref+"/styles/html_chunk.xsl")
    os.chdir(cur)

def docs_single(version):
    root = p["targetDir"] + "/" + p["dist.ref.dir"] + "/html_single"
    
    setup(root)
    
    cur = os.path.abspath(".")
    os.chdir(root)
    ref = cur + "/" + p["doc.ref.dir"]
    os.system("java -classpath " + os.path.pathsep.join(glob(ref + "/lib/*.jar")) + \
        " -Xmx256M -XX:MaxPermSize=128m com.icl.saxon.StyleSheet " + \
        "-o index.html " + ref+"/src/index.xml " + ref+"/styles/html.xsl")
    os.chdir(cur)

def docs_pdf(version):
    root = p["targetDir"] + "/" + p["dist.ref.dir"] + "/pdf"
    
    setup(root, stylesheets=False)
   
    cur = os.path.abspath(".")
    os.chdir(root)
    ref = cur + "/" + p["doc.ref.dir"]
    os.system("java -classpath " + os.path.pathsep.join(glob(ref + "/lib/*.jar")) + \
        " -Xmx256M -XX:MaxPermSize=128m com.icl.saxon.StyleSheet " + \
        "-o docbook_fop.tmp " + ref+"/src/index.xml " + ref+"/styles/fopdf.xsl double.sided=" + p["double.sided"])
    os.system("java -classpath " + os.path.pathsep.join(glob(ref + "/lib/*.jar")) + \
        " -Xmx256M -XX:MaxPermSize=128m org.apache.fop.apps.Fop " + \
        "docbook_fop.tmp springpython-reference.pdf")
    os.remove("docbook_fop.tmp")
    os.chdir(cur)


############################################################################
# Pre-commands. Skim the options, and pick out commands the MUST be
# run before others.
############################################################################

# No matter what order the command are specified in, the build-stamp must be extracted first.
for option in optlist:
    if option[0] == "--build-stamp":
        buildStamp = option[1]   # Override build stamp with user-supplied version
completeVersion = p["version"] + "-" + buildStamp

# Check for help requests, which cause all other options to be ignored. Help can offer version info, which is
# why it comes as the second check
for option in optlist:
    if option[0] in ("--help", "-h"):
        usage()
        sys.exit(1)
        
############################################################################
# Main commands. Skim the options, and run each command as its found.
# Commands are run in the order found ON THE COMMAND LINE.
############################################################################

# Parse the arguments, in order
for option in optlist:
    if option[0] in ("--clean", "-c"):
        clean(p["targetDir"])

    if option[0] in ("--test"):
        test(p["testDir"])

    if option[0] in ("--package"):
        package(p["packageDir"], completeVersion)
	
    if option[0] in ("--publish"):
        publish()

    if option[0] in ("--register"):
        register(completeVersion)

    if option[0] in ("--docs-all"):
        docs_multi(completeVersion)
        docs_single(completeVersion)
        docs_pdf(completeVersion)
        
    if option[0] in ("--docs-html-multi"):
        docs_multi(completeVersion)

    if option[0] in ("--docs-html-single"):
        docs_single(completeVersion)

    if option[0] in ("--docs-pdf"):
        docs_pdf(completeVersion)
    

