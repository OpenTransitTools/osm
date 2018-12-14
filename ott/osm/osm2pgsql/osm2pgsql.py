from ott.utils import exe_utils
from ott.utils import file_utils
from ott.utils import db_utils
from ..osm_cache import OsmCache


import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__file__)


class Osm2pgsql(OsmCache):
    """
    run pgsql
    """
    osm2pgsql_exe = None
    db_url = None
    osm_path = None

    def __init__(self, binary_name='osm2pgsql'):
        """
        get paths to osm2pgsql binary, as well as (inheritted) paths to .osm file (from app.ini)
        """
        super(Osm2pgsql, self).__init__()

        self.osm2pgsql_exe = exe_utils.find_executable(binary_name)
        if self.osm2pgsql_exe and self.osm_path:
            self.db_url = self.config.get('osm_url', section='db')
            log.info("'{}' into '{}'".format(self.osm2pgsql_exe, self.db_url))
        else:
            log.info("NOTE: this won't work, since can't find osm2pgsql binary '{}'".format(binary_name))

    def run(self):
        if self.osm_path and self.db_url:
            db = db_utils.make_url(self.db_url)
            cmd = "{} -c -d {} -H {} -P {} -U {} {}".format(self.osm2pgsql_exe, db.database, db.host, db.port, db.username, self.osm_path)
            log.info(cmd)
            exe_utils.run_cmd(cmd, shell=True)


def main():
    p = Osm2pgsql()
    p.run()


if __name__ == '__main__':
    main()
