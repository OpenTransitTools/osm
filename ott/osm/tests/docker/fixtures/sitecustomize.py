import configparser

# Compatibility shim for ott.utils on Python 3.12+.
if not hasattr(configparser, "SafeConfigParser"):
    configparser.SafeConfigParser = configparser.ConfigParser
