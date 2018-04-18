from ott.utils import exe_utils
from ott.utils import file_utils
from ott.utils import db_utils


import logging
logging.basicConfig()
log = logging.getLogger(__file__)


class Osm2pgsql(object):
    """ run pgsql
    """
    osm2pgsql_exe = None
    db_url = None
    osm_path = None

    def __init__(self, db_url='postgresql://ott@127.0.0.1:5432/ott', binary_name='osm2pgsql', osm_path='planet.osm'):
        """
        """
        exe_path = exe_utils.find_executable(binary_name)
        if exe_path:
            self.osm2pgsql_exe = exe_path
            self.db_url = db_url
            log.info("'{}' into '{}'".format(binary_name, db_url))
        else:
            log.info("NOTE: this won't work, since can't find osm2pgsql binary '{}'".format(binary_name))

    def run(self):
        if self.osm_path and self.db_url:
            db = db_utils.make_url(self.db_url)
            cmd = "{} -c -d {} -H {} -P {} -U {} {}".format(self.osm2pgsql_exe, db.database, db.host, db.port, db.username, self.osm_path)
            log.info(cmd)
            exe_utils.run_cmd(cmd, shell=True)

    @classmethod
    def factory(cls, cfg='app.ini'):
        self._config = ConfigUtil.factory(section=section)
        pass


def main():
    p = Osm2pgsql()
    p.run()


if __name__ == '__main__':
    main()
