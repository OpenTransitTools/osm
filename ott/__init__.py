from pkgutil import extend_path

# Keep ott as a namespace package without requiring setuptools/pkg_resources.
__path__ = extend_path(__path__, __name__)
