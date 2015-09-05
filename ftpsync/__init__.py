# make version accessible as 'ftpsync.__version__'
#from ftpsync._version import __version__
"""
Package version number.

http://peak.telecommunity.com/DevCenter/setuptools#specifying-your-project-s-version
http://peak.telecommunity.com/DevCenter/setuptools#tagging-and-daily-build-or-snapshot-releases

Imported by ftpsync.__init__, so it can be accessed as 'ftpsync.__version__'.
Accessed by setup.py using read().

semver would be           '1.0.0-1'
PyPI  would be            '1.0.0b1'
cx_Freeze build need      '1.0.0.0'
cx_Freeze bdist_msi  need '1.0.0'
"""
__version__ = "1.0.4"
