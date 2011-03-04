"""
 Make sure you delete the Build directory if you are
 reconfiguring which files are being distributed
 as there may be old relics in there that get installed.

 Listing two packages in the list below, means that two folders
 i.e. packages will be created in C:\Python22\Lib\site-packages
"""

from distutils.core import setup
setup (name = "foo2",
       version = "1.0beta0.4",
       author = "Andy Bulka",
       author_email = "abulka@netspace.net.au",
       description = "test of package foo - playing with distutils.",
       keywords = "test package distutils",
       license = "GPL? i.e. free as long as author acknowledged and derivitave source is also open source.",
       packages=['foo2','foo2a'])


"""
http://python.active-venture.com/dist/setup-script.html

The packages option tells the Distutils to process
(build, distribute, install, etc.) all pure Python
modules found in each package mentioned in the packages
list. In order to do this, of course, there has to be
a correspondence between package names and directories
in the filesystem. The default correspondence is the
most obvious one, i.e. package distutils is found in
the directory distutils relative to the distribution
root. Thus, when you say packages = ['foo'] in your
setup script, you are promising that the Distutils
will find a file foo/__init__.py (which might be
spelled differently on your system, but you get
the idea) relative to the directory where your
setup script lives. If you break this promise, the
Distutils will issue a warning but still process the
broken package anyways.
"""