from ott.utils import exe_utils
from ott.utils import file_utils


import logging
log = logging.getLogger(__file__)


class Osm2pgsql(object):
    """ run pgsql
    """
    osm2pgsql_exe = None
    db_url = None

    def __init__(self, db_url='', binary_name='osm2pgsql'):
        """
        """
        exe_path = exe_utils.find_executable(binary_name)
        if exe_path:
            self.way_count = exe_utils
            self.db_url = db_url

    def run(self):
        if self.db_url:
            pass

    @classmethod
    def factory(cls, cfg='app.ini'):
        pass


def main():
    # import pdb; pdb.set_trace()
    pass


if __name__ == '__main__':
    main()
