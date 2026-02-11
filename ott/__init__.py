try:
    # Legacy namespace package support when pkg_resources is available.
    __import__("pkg_resources").declare_namespace(__name__)
except ModuleNotFoundError:
    # Fallback for modern environments where pkg_resources is absent.
    from pkgutil import extend_path

    __path__ = extend_path(__path__, __name__)
