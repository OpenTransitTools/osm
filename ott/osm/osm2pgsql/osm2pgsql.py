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
    style_path = None
    epsg = "3857"

    def __init__(self, binary_name="osm2pgsql"):
        """
        get paths to osm2pgsql binary, as well as (inheritted) paths to .osm file (from app.ini)
        """
        super(Osm2pgsql, self).__init__()

        # step 1: config the path to an osm2pgsql style file
        style_file = self.config.get("osm2pgsql_style", def_val="default.style")
        self.style_path = os.path.join(self.this_module_dir, "styles", style_file)

        # step 2: find the osm2pgsql binary ... if not found in your path, the db_url won't be set and nothing will run
        self.osm2pgsql_exe = exe_utils.find_executable(binary_name)
        if self.osm2pgsql_exe and self.osm_path:
            self.db_url = self.config.get("url", section="osm_db")
            log.info("'{}' into '{}'".format(self.osm2pgsql_exe, self.db_url))
        else:
            log.warn("NOTE: this won't work, since can't find osm2pgsql binary '{}'".format(binary_name))

    def run(self):
        min_size = self.config.get_int("min_size", def_val=100000)
        sized = file_utils.is_min_sized(self.osm_path, min_size)
        if sized and self.db_url:
            db = db_utils.make_url(self.db_url)
            cmd = "{} --create --style {} --proj {} -d {} -H {} -P {} -U {} {}".format(
                self.osm2pgsql_exe, self.style_path, self.epsg, db.database, db.host, db.port, db.username, self.osm_path
            )
            log.info(cmd)
            exe_utils.run_cmd(cmd, shell=True)
        else:
            if sized is None:
                log.warn("osm2pgsql NOT RUNNING since {} looks smaller than {} smoots.".format(self.osm_path, min_size))
            else:
                log.warn("osm2pgsql NOT RUNNING (Is osm2pgsql in your PATH? Issues with the db url {}?)".format(self.db_url))


def main():
    p = Osm2pgsql()
    p.run()


if __name__ == '__main__':
    main()
