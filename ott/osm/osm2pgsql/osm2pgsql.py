from ott.utils import exe_utils
from ott.utils import file_utils
from ott.utils import db_utils
from ..osm_cache import OsmCache

import os
import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__file__)


class Osm2pgsql(OsmCache):
    """
    run pgsql
    """
    osm2pgsql_exe = None
    psql_exe = None

    db_url = None
    epsg = "3857"

    osm_path = None
    style_path = None
    sql_path = None

    def __init__(self, osm2pgsql_name="osm2pgsql", psql_name="psql"):
        """
        get paths to osm2pgsql binary, as well as (inheritted) paths to .osm file (from app.ini)
        """
        super(Osm2pgsql, self).__init__()

        # step 1: config the path to an osm2pgsql style file and psql table file
        style_file = self.config.get("osm2pgsql_style", def_val="default.style")
        if file_utils.exists(style_file):
            self.style_path = style_file
        else:
            self.style_path = os.path.join(self.this_module_dir, "styles", style_file)

        sql_file = self.config.get("osm2pgsql_sql", def_val="create_osmgwc_tables.sql")
        if file_utils.exists(sql_file):
            self.sql_path = sql_file
        else:
            self.sql_path = os.path.join(self.this_module_dir, "sql", sql_file)

        # step 2: find the osm2pgsql binary ... if not found in your path, the db_url won't be set and nothing will run
        self.osm2pgsql_exe = exe_utils.find_executable(osm2pgsql_name)
        if self.osm2pgsql_exe and self.osm_path:
            self.db_url = self.config.get("url", section="osm_db")
            log.info("'{}' into '{}'".format(self.osm2pgsql_exe, self.db_url))
        else:
            log.warn("NOTE: this won't work, since can't find osm2pgsql binary '{}'".format(osm2pgsql_name))

        # step 3: find psql
        if file_utils.exists(self.sql_path):
            self.psql_exe = exe_utils.find_executable(psql_name)
            if self.psql_exe is None:
                log.warn("NOTE: can't find '{}' binary, so won't be able to run '{}' post process".format(psql_name, sql_file))
        else:
            self.sql_path = None

    def run(self):
        """ run osm2pgsql and (optionally) the psql post-processing script """
        min_size = self.config.get_int("min_size", def_val=100000)
        sized = file_utils.is_min_sized(self.osm_path, min_size)
        if sized and self.db_url:
            # step 1: run osm2pgsql
            db = db_utils.make_url(self.db_url)
            cmd = "{} --create --style {} --proj {} -d {} -H {} -P {} -U {} {}".format(
                self.osm2pgsql_exe, self.style_path, self.epsg, db.database, db.host, db.port, db.username, self.osm_path
            )
            log.info(cmd)
            exe_utils.run_cmd(cmd, shell=True)

            # step 2: if we have a sql post-processing file, run it thru psql
            if self.psql_exe and self.sql_path:
                cmd = "{} -d {} -h {} -p {} -U {} -w -f {}".format(
                    self.psql_exe, db.database, db.host, db.port, db.username, self.sql_path
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
