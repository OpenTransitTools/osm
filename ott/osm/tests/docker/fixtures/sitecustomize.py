import configparser
import re
from typing import TypeVar

# Compatibility shim for ott.utils on Python 3.12+.
if not hasattr(configparser, "SafeConfigParser"):
    configparser.SafeConfigParser = configparser.ConfigParser

# Compatibility shim for ott.utils on Python 3.14+ (re.T no longer exists).
if not hasattr(re, "T"):
    re.T = TypeVar("T")
