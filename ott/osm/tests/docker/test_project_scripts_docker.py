from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

log = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[4]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
IMAGE_NAME = "ghcr.io/opentransittools/osm"
REAL_OSMOSIS_PATH = "/osm/bin/osmosis"

SCRIPT_COMMANDS = {
    "osm_clip_from_pbf": "osm_clip_from_pbf",
    "osm_clip_rename": "osm_clip_rename",
    "osm_update": "osm_update",
    "osm_to_pgsql": "osm_to_pgsql",
    "osm_to_pbf": "osm_to_pbf --osm /data/input/in.osm --pbf /data/output/in.osm.pbf --osmosis_exe /data/bin/osmosis",
    "osm_cull_transit": "osm_cull_transit --osm /data/input/in.osm --osmosis_exe /data/bin/osmosis",
    "osm_stats": "osm_stats --osm /data/input/in.osm",
    "osm_stats_cfg": "osm_stats_cfg",
    "osm_rename": "osm_rename --osm /data/input/in.osm",
    "osm_make_raw": "osm_make_raw",
    "osm_other_exports": "osm_other_exports",
    "osm_abbr_tester": "osm_abbr_tester",
    "osm-intersections": "osm-intersections --osm /data/input/in.osm --csv /data/output/intersections.csv",
    "osm-intersections_cache": "osm-intersections_cache",
}

EXPECTED_EXIT_CODES = {
    "osm_clip_from_pbf": {0, 1},
    "osm_make_raw": {0, 1},
    "osm_update": {0, 1},
}


def _run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def _project_scripts() -> list[str]:
    cfg = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = cfg["project"]["scripts"]
    return list(scripts.keys())


def _docker_available() -> bool:
    probe = _run(["docker", "--version"])
    return probe.returncode == 0


def _branch_tag() -> str:
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT_DIR)
    branch_name = branch.stdout.strip() if branch.returncode == 0 else "local"
    if branch_name == "master":
        return "latest"
    return "".join((ch.lower() if ch.isalnum() or ch in "._-" else "-") for ch in branch_name)


@pytest.fixture(scope="session")
def docker_image() -> str:
    if not _docker_available():
        pytest.skip("docker not available on PATH")

    image_tag = _branch_tag()
    image = f"{IMAGE_NAME}:{image_tag}"
    build_script = ROOT_DIR / "docker" / "buildDocker.sh"
    build_env = {
        **os.environ,
        "BUILD_TARGET": "test",
        "IMAGE_NAME": IMAGE_NAME,
        "TAG": image_tag,
    }
    build = _run([str(build_script)], cwd=ROOT_DIR, env=build_env)
    if build.returncode != 0:
        pytest.fail(f"docker image build failed:\nSTDOUT:\n{build.stdout}\nSTDERR:\n{build.stderr}")
    return image


@pytest.fixture(scope="session")
def docker_workdir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    work_dir = tmp_path_factory.mktemp("docker-api")
    (work_dir / "cache").mkdir()
    (work_dir / "input").mkdir()
    (work_dir / "output").mkdir()
    (work_dir / "bin").mkdir()

    shutil.copy(FIXTURES_DIR / "mock.osm", work_dir / "input" / "in.osm")
    shutil.copy(FIXTURES_DIR / "mock.osm", work_dir / "cache" / "us-west-latest.osm.pbf")
    shutil.copy(FIXTURES_DIR / "app.ini", work_dir / "app.ini")
    shutil.copy(FIXTURES_DIR / "fake_osmosis.sh", work_dir / "bin" / "osmosis")
    shutil.copy(FIXTURES_DIR / "sitecustomize.py", work_dir / "bin" / "sitecustomize.py")
    (work_dir / "bin" / "osmosis").chmod(0o755)
    return work_dir


def _run_script_in_docker(image: str, work_dir: Path, cmd: str) -> subprocess.CompletedProcess[str]:
    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "-e",
        "PYTHONPATH=/data/bin",
        "-v",
        f"{work_dir / 'app.ini'}:/osm/config/app.ini:ro",
        "-v",
        f"{work_dir / 'cache'}:/data/cache",
        "-v",
        f"{work_dir / 'cache'}:/osm/config/data/cache",
        "-v",
        f"{work_dir / 'input'}:/data/input",
        "-v",
        f"{work_dir / 'output'}:/data/output",
        "-v",
        f"{work_dir / 'bin'}:/data/bin",
        image,
        "sh",
        "-lc",
        f"python -m pip install --quiet 'setuptools<81' && {cmd}",
    ]
    log.info("Running in docker: %s", " ".join(docker_cmd))
    return _run(docker_cmd)


def test_command_map_covers_all_project_scripts() -> None:
    scripts = _project_scripts()
    missing = [s for s in scripts if s not in SCRIPT_COMMANDS]
    assert not missing, f"missing command mapping(s): {missing}"


def test_real_osmosis_installed_in_image(docker_image: str) -> None:
    result = _run(
        [
            "docker",
            "run",
            "--rm",
            docker_image,
            "sh",
            "-lc",
            f"test -x {REAL_OSMOSIS_PATH}",
        ]
    )
    assert result.returncode == 0, (
        f"expected executable osmosis at {REAL_OSMOSIS_PATH}\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )


@pytest.mark.parametrize("script_name", _project_scripts())
def test_project_script_via_docker(script_name: str, docker_image: str, docker_workdir: Path) -> None:
    cmd = SCRIPT_COMMANDS[script_name]
    log.info("Testing %s with command: %s", script_name, cmd)
    result = _run_script_in_docker(docker_image, docker_workdir, cmd)

    expected_codes = EXPECTED_EXIT_CODES.get(script_name, {0})
    assert result.returncode in expected_codes, (
        f"{script_name} exited with {result.returncode}, expected {sorted(expected_codes)}\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
