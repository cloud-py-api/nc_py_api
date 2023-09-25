import os
import sys
from subprocess import PIPE, run
from unittest import mock

import nc_py_api


def test_timeouts():
    project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_file = os.path.join(project_dir, ".env")
    env_backup_file = os.path.join(project_dir, ".env.backup")
    if os.path.exists(env_file):
        os.rename(env_file, env_backup_file)
    try:
        check_command = [sys.executable, "-c", "import nc_py_api\nassert nc_py_api.options.NPA_TIMEOUT is None"]
        with open(env_file, "w") as env_f:
            env_f.write("NPA_TIMEOUT=None")
        r = run(check_command, stderr=PIPE, env={}, cwd=project_dir, check=False)
        assert not r.stderr
        check_command = [sys.executable, "-c", "import nc_py_api\nassert nc_py_api.options.NPA_TIMEOUT == 11"]
        with open(env_file, "w") as env_f:
            env_f.write("NPA_TIMEOUT=11")
        r = run(check_command, stderr=PIPE, env={}, cwd=project_dir, check=False)
        assert not r.stderr
        check_command = [sys.executable, "-c", "import nc_py_api\nassert nc_py_api.options.NPA_TIMEOUT_DAV is None"]
        with open(env_file, "w") as env_f:
            env_f.write("NPA_TIMEOUT_DAV=None")
        r = run(check_command, stderr=PIPE, env={}, cwd=project_dir, check=False)
        assert not r.stderr
        check_command = [sys.executable, "-c", "import nc_py_api\nassert nc_py_api.options.NPA_TIMEOUT_DAV == 11"]
        with open(env_file, "w") as env_f:
            env_f.write("NPA_TIMEOUT_DAV=11")
        r = run(check_command, stderr=PIPE, env={}, cwd=project_dir, check=False)
        assert not r.stderr
        check_command = [sys.executable, "-c", "import nc_py_api\nassert nc_py_api.options.NPA_NC_CERT is False"]
        with open(env_file, "w") as env_f:
            env_f.write("NPA_NC_CERT=False")
        r = run(check_command, stderr=PIPE, env={}, cwd=project_dir, check=False)
        assert not r.stderr
        check_command = [sys.executable, "-c", "import nc_py_api\nassert nc_py_api.options.NPA_NC_CERT == ''"]
        with open(env_file, "w") as env_f:
            env_f.write('NPA_NC_CERT=""')
        r = run(check_command, stderr=PIPE, env={}, cwd=project_dir, check=False)
        assert not r.stderr
    finally:
        if os.path.exists(env_backup_file):
            os.rename(env_backup_file, env_file)


def test_xdebug_session(nc_any):
    nc_py_api.options.XDEBUG_SESSION = "12345"
    new_nc = nc_py_api.Nextcloud() if isinstance(nc_any, nc_py_api.Nextcloud) else nc_py_api.NextcloudApp()
    assert new_nc._session.adapter.cookies["XDEBUG_SESSION"] == "12345"


@mock.patch("nc_py_api.options.CHUNKED_UPLOAD_V2", False)
def test_chunked_upload(nc_any):
    new_nc = nc_py_api.Nextcloud() if isinstance(nc_any, nc_py_api.Nextcloud) else nc_py_api.NextcloudApp()
    assert new_nc._session.cfg.options.upload_chunk_v2 is False


def test_chunked_upload2(nc_any):
    new_nc = (
        nc_py_api.Nextcloud(chunked_upload_v2=False)
        if isinstance(nc_any, nc_py_api.Nextcloud)
        else nc_py_api.NextcloudApp(chunked_upload_v2=False)
    )
    assert new_nc._session.cfg.options.upload_chunk_v2 is False
    new_nc = nc_py_api.Nextcloud() if isinstance(nc_any, nc_py_api.Nextcloud) else nc_py_api.NextcloudApp()
    assert new_nc._session.cfg.options.upload_chunk_v2 is True
