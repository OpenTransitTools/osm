from ott.utils import exe_utils
from ott.utils import file_utils


import logging
logging.basicConfig()
log = logging.getLogger(__file__)


class Osm2pgsql(object):
    """ run pgsql
    """
    osm2pgsql_exe = None
    db_url = None

    def __init__(self, db_url='postgresql://ott@127.0.0.1:5432/ott', binary_name='osm2pgsql'):
        """
        """
        exe_path = exe_utils.find_executable(binary_name)
        if exe_path:
            self.osm2pgsql_exe = exe_utils
            self.db_url = db_url
            log.info("'{}' into '{}'".format(binary_name, db_url))
            print exe_utils
        else:
            log.info("NOTE: this won't work, since can't find osm2pgsql binary '{}'".format(binary_name))


    def run(self):
        if self.db_url:
            pass

    @classmethod
    def factory(cls, cfg='app.ini'):
        self._config = ConfigUtil.factory(section=section)
        pass


def main():
    Osm2pgsql()


if __name__ == '__main__':
    main()
