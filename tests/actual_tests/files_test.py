import contextlib
import math
import os
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from random import choice, randbytes
from string import ascii_lowercase
from tempfile import NamedTemporaryFile
from zlib import adler32

import pytest

from nc_py_api import FsNode, LockType, NextcloudException, NextcloudExceptionNotFound


class MyBytesIO(BytesIO):
    def __init__(self):
        self.n_read_calls = 0
        self.n_write_calls = 0
        super().__init__()

    def read(self, *args, **kwargs):
        self.n_read_calls += 1
        return super().read(*args, **kwargs)

    def write(self, *args, **kwargs):
        self.n_write_calls += 1
        return super().write(*args, **kwargs)


def _test_list_user_root(user_root: list[FsNode], user: str):
    assert user_root
    for obj in user_root:
        assert obj.user == user
        assert obj.has_extra
        assert obj.name
        assert obj.user_path
        assert obj.file_id
        assert obj.etag


def test_list_user_root(nc):
    user_root = nc.files.listdir()
    _test_list_user_root(user_root, nc.user)
    root_node = FsNode(full_path=f"files/{nc.user}/")
    user_root2 = nc.files.listdir(root_node)
    assert user_root == user_root2


@pytest.mark.asyncio(scope="session")
async def test_list_user_root_async(anc):
    user_root = await anc.files.listdir()
    _test_list_user_root(user_root, await anc.user)
    root_node = FsNode(full_path=f"files/{await anc.user}/")
    user_root2 = await anc.files.listdir(root_node)
    assert user_root == user_root2


def _test_list_user_root_self_exclude(user_root: list[FsNode], user_root_with_self: list[FsNode], user: str):
    assert len(user_root_with_self) == 1 + len(user_root)
    self_res = next(i for i in user_root_with_self if not i.user_path)
    for i in user_root:
        assert self_res != i
    assert self_res.has_extra
    assert self_res.file_id
    assert self_res.user == user
    assert self_res.name
    assert self_res.etag
    assert self_res.full_path == f"files/{user}/"


def test_list_user_root_self_exclude(nc):
    user_root = nc.files.listdir()
    user_root_with_self = nc.files.listdir(exclude_self=False)
    _test_list_user_root_self_exclude(user_root, user_root_with_self, nc.user)


@pytest.mark.asyncio(scope="session")
async def test_list_user_root_self_exclude_async(anc):
    user_root = await anc.files.listdir()
    user_root_with_self = await anc.files.listdir(exclude_self=False)
    _test_list_user_root_self_exclude(user_root, user_root_with_self, await anc.user)


def _test_list_empty_dir(result: list[FsNode], user: str):
    assert len(result)
    result = result[0]
    assert result.file_id
    assert result.user == user
    assert result.name == "test_empty_dir"
    assert result.etag
    assert result.full_path == f"files/{user}/test_empty_dir/"


def test_list_empty_dir(nc_any):
    assert not len(nc_any.files.listdir("test_empty_dir"))
    result = nc_any.files.listdir("test_empty_dir", exclude_self=False)
    _test_list_empty_dir(result, nc_any.user)


@pytest.mark.asyncio(scope="session")
async def test_list_empty_dir_async(anc_any):
    assert not len(await anc_any.files.listdir("test_empty_dir"))
    result = await anc_any.files.listdir("test_empty_dir", exclude_self=False)
    _test_list_empty_dir(result, await anc_any.user)


def test_list_spec_dir(nc_any):
    r = nc_any.files.listdir("test_###_dir", exclude_self=False)
    assert r[0].full_path.find("test_###_dir") != -1


@pytest.mark.asyncio(scope="session")
async def test_list_spec_dir_async(anc_any):
    r = await anc_any.files.listdir("test_###_dir", exclude_self=False)
    assert r[0].full_path.find("test_###_dir") != -1


def test_list_dir_wrong_args(nc_any):
    with pytest.raises(ValueError):
        nc_any.files.listdir(depth=0, exclude_self=True)


@pytest.mark.asyncio(scope="session")
async def test_list_dir_wrong_args_async(anc_any):
    with pytest.raises(ValueError):
        await anc_any.files.listdir(depth=0, exclude_self=True)


def _test_by_path(result: FsNode, result2: FsNode, user: str):
    assert isinstance(result, FsNode)
    assert isinstance(result2, FsNode)
    assert result == result2
    assert result.is_dir == result2.is_dir
    assert result.is_dir
    assert result.user == result2.user
    assert result.user == user


def test_by_path(nc_any):
    result = nc_any.files.by_path("")
    result2 = nc_any.files.by_path("/")
    _test_by_path(result, result2, nc_any.user)


@pytest.mark.asyncio(scope="session")
async def test_by_path_async(anc_any):
    result = await anc_any.files.by_path("")
    result2 = await anc_any.files.by_path("/")
    _test_by_path(result, result2, await anc_any.user)


def test_file_download(nc_any):
    assert nc_any.files.download("test_empty_text.txt") == b""
    assert nc_any.files.download("/test_12345_text.txt") == b"12345"


@pytest.mark.asyncio(scope="session")
async def test_file_download_async(anc_any):
    assert await anc_any.files.download("test_empty_text.txt") == b""
    assert await anc_any.files.download("/test_12345_text.txt") == b"12345"


@pytest.mark.parametrize("data_type", ("str", "bytes"))
@pytest.mark.parametrize("chunk_size", (15, 32, 64, None))
def test_file_download2stream(nc, data_type, chunk_size):
    bytes_io_fp = MyBytesIO()
    content = "".join(choice(ascii_lowercase) for _ in range(64)) if data_type == "str" else randbytes(64)
    nc.files.upload("/test_dir_tmp/download2stream", content=content)
    old_headers = nc.response_headers
    if chunk_size is not None:
        nc.files.download2stream("/test_dir_tmp/download2stream", bytes_io_fp, chunk_size=chunk_size)
    else:
        nc.files.download2stream("/test_dir_tmp/download2stream", bytes_io_fp)
    assert nc.response_headers != old_headers
    assert nc.files.download("/test_dir_tmp/download2stream") == bytes_io_fp.getbuffer()
    if chunk_size is None:
        assert bytes_io_fp.n_write_calls == 1
    else:
        assert bytes_io_fp.n_write_calls == math.ceil(64 / chunk_size)


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("data_type", ("str", "bytes"))
@pytest.mark.parametrize("chunk_size", (15, 32, 64, None))
async def test_file_download2stream_async(anc, data_type, chunk_size):
    bytes_io_fp = MyBytesIO()
    content = "".join(choice(ascii_lowercase) for _ in range(64)) if data_type == "str" else randbytes(64)
    await anc.files.upload("/test_dir_tmp/download2stream_async", content=content)
    old_headers = anc.response_headers
    if chunk_size is not None:
        await anc.files.download2stream("/test_dir_tmp/download2stream_async", bytes_io_fp, chunk_size=chunk_size)
    else:
        await anc.files.download2stream("/test_dir_tmp/download2stream_async", bytes_io_fp)
    assert anc.response_headers != old_headers
    assert await anc.files.download("/test_dir_tmp/download2stream_async") == bytes_io_fp.getbuffer()
    if chunk_size is None:
        assert bytes_io_fp.n_write_calls == 1
    else:
        assert bytes_io_fp.n_write_calls == math.ceil(64 / chunk_size)


def test_file_download2file(nc_any, rand_bytes):
    with NamedTemporaryFile() as tmp_file:
        nc_any.files.download2stream("test_64_bytes.bin", tmp_file.name)
        assert tmp_file.read() == rand_bytes


@pytest.mark.asyncio(scope="session")
async def test_file_download2file_async(anc_any, rand_bytes):
    with NamedTemporaryFile() as tmp_file:
        await anc_any.files.download2stream("test_64_bytes.bin", tmp_file.name)
        assert tmp_file.read() == rand_bytes


def test_file_download2stream_invalid_type(nc_any):
    for test_type in (
        b"13",
        int(55),
    ):
        with pytest.raises(TypeError):
            nc_any.files.download2stream("xxx", test_type)


@pytest.mark.asyncio(scope="session")
async def test_file_download2stream_invalid_type_async(anc_any):
    for test_type in (
        b"13",
        int(55),
    ):
        with pytest.raises(TypeError):
            await anc_any.files.download2stream("xxx", test_type)


def test_file_upload_stream_invalid_type(nc_any):
    for test_type in (
        b"13",
        int(55),
    ):
        with pytest.raises(TypeError):
            nc_any.files.upload_stream("xxx", test_type)


@pytest.mark.asyncio(scope="session")
async def test_file_upload_stream_invalid_type_async(anc_any):
    for test_type in (
        b"13",
        int(55),
    ):
        with pytest.raises(TypeError):
            await anc_any.files.upload_stream("xxx", test_type)


def test_file_download_not_found(nc_any):
    with pytest.raises(NextcloudException):
        nc_any.files.download("file that does not exist on the server")
    with pytest.raises(NextcloudException):
        nc_any.files.listdir("non existing path")


@pytest.mark.asyncio(scope="session")
async def test_file_download_not_found_async(anc_any):
    with pytest.raises(NextcloudException):
        await anc_any.files.download("file that does not exist on the server")
    with pytest.raises(NextcloudException):
        await anc_any.files.listdir("non existing path")


def test_file_download2stream_not_found(nc_any):
    buf = BytesIO()
    with pytest.raises(NextcloudException):
        nc_any.files.download2stream("file that does not exist on the server", buf)
    with pytest.raises(NextcloudException):
        nc_any.files.download2stream("non existing path", buf)


@pytest.mark.asyncio(scope="session")
async def test_file_download2stream_not_found_async(anc_any):
    buf = BytesIO()
    with pytest.raises(NextcloudException):
        await anc_any.files.download2stream("file that does not exist on the server", buf)
    with pytest.raises(NextcloudException):
        await anc_any.files.download2stream("non existing path", buf)


def test_file_upload(nc_any):
    file_name = "test_dir_tmp/12345.txt"
    result = nc_any.files.upload(file_name, content=b"\x31\x32")
    assert nc_any.files.by_id(result).info.size == 2
    assert nc_any.files.download(file_name) == b"\x31\x32"
    result = nc_any.files.upload(f"/{file_name}", content=b"\x31\x32\x33")
    assert not result.has_extra
    result = nc_any.files.by_path(result)
    assert result.info.size == 3
    assert result.is_updatable
    assert not result.is_creatable
    assert nc_any.files.download(file_name) == b"\x31\x32\x33"
    nc_any.files.upload(file_name, content="life is good")
    assert nc_any.files.download(file_name).decode("utf-8") == "life is good"


@pytest.mark.asyncio(scope="session")
async def test_file_upload_async(anc_any):
    file_name = "test_dir_tmp/12345_async.txt"
    result = await anc_any.files.upload(file_name, content=b"\x31\x32")
    assert (await anc_any.files.by_id(result)).info.size == 2
    assert await anc_any.files.download(file_name) == b"\x31\x32"
    result = await anc_any.files.upload(f"/{file_name}", content=b"\x31\x32\x33")
    assert not result.has_extra
    result = await anc_any.files.by_path(result)
    assert result.info.size == 3
    assert result.is_updatable
    assert not result.is_creatable
    assert await anc_any.files.download(file_name) == b"\x31\x32\x33"
    await anc_any.files.upload(file_name, content="life is good")
    assert (await anc_any.files.download(file_name)).decode("utf-8") == "life is good"


@pytest.mark.parametrize("chunk_size", (63, 64, 65, None))
def test_file_upload_chunked(nc, chunk_size):
    file_name = "/test_dir_tmp/chunked.bin"
    buf_upload = MyBytesIO()
    random_bytes = randbytes(64)
    buf_upload.write(random_bytes)
    buf_upload.seek(0)
    if chunk_size is None:
        result = nc.files.upload_stream(file_name, fp=buf_upload)
    else:
        result = nc.files.upload_stream(file_name, fp=buf_upload, chunk_size=chunk_size)
    if chunk_size is None:
        assert buf_upload.n_read_calls == 2
    else:
        assert buf_upload.n_read_calls == 1 + math.ceil(64 / chunk_size)
    assert nc.files.by_id(result.file_id).info.size == 64
    buf_download = BytesIO()
    nc.files.download2stream(file_name, fp=buf_download)
    buf_upload.seek(0)
    buf_download.seek(0)
    upload_crc = adler32(buf_upload.read())
    download_crc = adler32(buf_download.read())
    assert upload_crc == download_crc


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("chunk_size", (63, 64, 65, None))
async def test_file_upload_chunked_async(anc, chunk_size):
    file_name = "/test_dir_tmp/chunked_async.bin"
    buf_upload = MyBytesIO()
    random_bytes = randbytes(64)
    buf_upload.write(random_bytes)
    buf_upload.seek(0)
    if chunk_size is None:
        result = await anc.files.upload_stream(file_name, fp=buf_upload)
    else:
        result = await anc.files.upload_stream(file_name, fp=buf_upload, chunk_size=chunk_size)
    if chunk_size is None:
        assert buf_upload.n_read_calls == 2
    else:
        assert buf_upload.n_read_calls == 1 + math.ceil(64 / chunk_size)
    assert (await anc.files.by_id(result.file_id)).info.size == 64
    buf_download = BytesIO()
    await anc.files.download2stream(file_name, fp=buf_download)
    buf_upload.seek(0)
    buf_download.seek(0)
    upload_crc = adler32(buf_upload.read())
    download_crc = adler32(buf_download.read())
    assert upload_crc == download_crc


@pytest.mark.parametrize("dest_path", ("test_dir_tmp/test_file_upload_file", "test_###_dir/test_file_upload_file"))
def test_file_upload_file(nc_any, dest_path):
    content = randbytes(113)
    with NamedTemporaryFile() as tmp_file:
        tmp_file.write(content)
        tmp_file.flush()
        r = nc_any.files.upload_stream(dest_path, tmp_file.name)
    assert nc_any.files.download(dest_path) == content
    assert nc_any.files.by_id(r.file_id).full_path.find(dest_path) != -1


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("dest_path", ("test_dir_tmp/test_file_upload_file", "test_###_dir/test_file_upload_file"))
async def test_file_upload_file_async(anc_any, dest_path):
    content = randbytes(113)
    with NamedTemporaryFile() as tmp_file:
        tmp_file.write(content)
        tmp_file.flush()
        r = await anc_any.files.upload_stream(dest_path, tmp_file.name)
    assert await anc_any.files.download(dest_path) == content
    assert (await anc_any.files.by_id(r.file_id)).full_path.find(dest_path) != -1


@pytest.mark.parametrize(
    "dest_path", ("test_dir_tmp/upl_chunk_v2", "test_dir_tmp/upl_chunk_v2_ü", "test_dir_tmp/upl_chunk_v2_11###33")
)
def test_file_upload_chunked_v2(nc_any, dest_path):
    with NamedTemporaryFile() as tmp_file:
        tmp_file.seek(7 * 1024 * 1024)
        tmp_file.write(b"\0")
        tmp_file.flush()
        r = nc_any.files.upload_stream(dest_path, tmp_file.name)
    assert len(nc_any.files.download(dest_path)) == 7 * 1024 * 1024 + 1
    assert nc_any.files.by_id(r.file_id).full_path.find(dest_path) != -1


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "dest_path",
    ("test_dir_tmp/upl_chunk_v2_async", "test_dir_tmp/upl_chunk_v2_ü_async", "test_dir_tmp/upl_chunk_v2_11###33"),
)
async def test_file_upload_chunked_v2_async(anc_any, dest_path):
    with NamedTemporaryFile() as tmp_file:
        tmp_file.seek(7 * 1024 * 1024)
        tmp_file.write(b"\0")
        tmp_file.flush()
        r = await anc_any.files.upload_stream(dest_path, tmp_file.name)
    assert len(await anc_any.files.download(dest_path)) == 7 * 1024 * 1024 + 1
    assert (await anc_any.files.by_id(r.file_id)).full_path.find(dest_path) != -1


@pytest.mark.parametrize("file_name", ("test_file_upload_del", "test_file_upload_del/", "test_file_upload_del//"))
def test_file_upload_zero_size(nc_any, file_name):
    nc_any.files.delete(f"/test_dir_tmp/{file_name}", not_fail=True)
    with pytest.raises(NextcloudException):
        nc_any.files.delete(f"/test_dir_tmp/{file_name}")
    result = nc_any.files.upload(f"/test_dir_tmp/{file_name}", content="")
    assert nc_any.files.download(f"/test_dir_tmp/{file_name}") == b""
    assert result.is_dir is False
    assert result.name == "test_file_upload_del"
    assert result.full_path.startswith("files/")
    nc_any.files.delete(f"/test_dir_tmp/{file_name}", not_fail=True)


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("file_name", ("test_file_upload_del", "test_file_upload_del/", "test_file_upload_del//"))
async def test_file_upload_zero_size_async(anc_any, file_name):
    await anc_any.files.delete(f"/test_dir_tmp/{file_name}", not_fail=True)
    with pytest.raises(NextcloudException):
        await anc_any.files.delete(f"/test_dir_tmp/{file_name}")
    result = await anc_any.files.upload(f"/test_dir_tmp/{file_name}", content="")
    assert await anc_any.files.download(f"/test_dir_tmp/{file_name}") == b""
    assert result.is_dir is False
    assert result.name == "test_file_upload_del"
    assert result.full_path.startswith("files/")
    await anc_any.files.delete(f"/test_dir_tmp/{file_name}", not_fail=True)


@pytest.mark.parametrize("file_name", ("chunked_zero", "chunked_zero/", "chunked_zero//"))
def test_file_upload_chunked_zero_size(nc_any, file_name):
    nc_any.files.delete(f"/test_dir_tmp/{file_name}", not_fail=True)
    buf_upload = MyBytesIO()
    result = nc_any.files.upload_stream(f"test_dir_tmp/{file_name}", fp=buf_upload)
    assert nc_any.files.download(f"test_dir_tmp/{file_name}") == b""
    assert not nc_any.files.by_path(result.user_path).info.size
    assert result.is_dir is False
    assert result.full_path.startswith("files/")
    assert result.name == "chunked_zero"
    nc_any.files.delete(f"/test_dir_tmp/{file_name}", not_fail=True)


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("file_name", ("chunked_zero", "chunked_zero/", "chunked_zero//"))
async def test_file_upload_chunked_zero_size_async(anc_any, file_name):
    await anc_any.files.delete(f"/test_dir_tmp/{file_name}", not_fail=True)
    buf_upload = MyBytesIO()
    result = await anc_any.files.upload_stream(f"test_dir_tmp/{file_name}", fp=buf_upload)
    assert await anc_any.files.download(f"test_dir_tmp/{file_name}") == b""
    assert not (await anc_any.files.by_path(result.user_path)).info.size
    assert result.is_dir is False
    assert result.full_path.startswith("files/")
    assert result.name == "chunked_zero"
    await anc_any.files.delete(f"/test_dir_tmp/{file_name}", not_fail=True)


@pytest.mark.parametrize("dir_name", ("1 2", "Яё", "відео та картинки", "复杂 目录 Í", "Björn", "João", "1##3"))
def test_mkdir(nc_any, dir_name):
    nc_any.files.delete(dir_name, not_fail=True)
    result = nc_any.files.mkdir(dir_name)
    assert result.is_dir
    assert not result.has_extra
    result_by_id = nc_any.files.by_id(result.file_id)
    with pytest.raises(NextcloudException):
        nc_any.files.mkdir(dir_name)
    nc_any.files.delete(dir_name)
    with pytest.raises(NextcloudException):
        nc_any.files.delete(dir_name)
    assert result_by_id.full_path == result.full_path


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("dir_name", ("1 2", "Яё", "відео та картинки", "复杂 目录 Í", "Björn", "João", "1##3"))
async def test_mkdir_async(anc_any, dir_name):
    await anc_any.files.delete(dir_name, not_fail=True)
    result = await anc_any.files.mkdir(dir_name)
    assert result.is_dir
    assert not result.has_extra
    result_by_id = await anc_any.files.by_id(result.file_id)
    with pytest.raises(NextcloudException):
        await anc_any.files.mkdir(dir_name)
    await anc_any.files.delete(dir_name)
    with pytest.raises(NextcloudException):
        await anc_any.files.delete(dir_name)
    assert result_by_id.full_path == result.full_path


def test_mkdir_invalid_args(nc_any):
    with pytest.raises(NextcloudException) as exc_info:
        nc_any.files.makedirs("test_dir_tmp/    /zzzzzzzz", exist_ok=True)
    assert exc_info.value.status_code != 405


@pytest.mark.asyncio(scope="session")
async def test_mkdir_invalid_args_async(anc_any):
    with pytest.raises(NextcloudException) as exc_info:
        await anc_any.files.makedirs("test_dir_tmp/    /zzzzzzzz", exist_ok=True)
    assert exc_info.value.status_code != 405


def test_mkdir_delete_with_end_slash(nc_any):
    nc_any.files.delete("dir_with_slash", not_fail=True)
    result = nc_any.files.mkdir("dir_with_slash/")
    assert result.is_dir
    assert result.name == "dir_with_slash"
    assert result.full_path.startswith("files/")
    nc_any.files.delete("dir_with_slash/")
    with pytest.raises(NextcloudException):
        nc_any.files.delete("dir_with_slash")


@pytest.mark.asyncio(scope="session")
async def test_mkdir_delete_with_end_slash_async(anc_any):
    await anc_any.files.delete("dir_with_slash", not_fail=True)
    result = await anc_any.files.mkdir("dir_with_slash/")
    assert result.is_dir
    assert result.name == "dir_with_slash"
    assert result.full_path.startswith("files/")
    await anc_any.files.delete("dir_with_slash/")
    with pytest.raises(NextcloudException):
        await anc_any.files.delete("dir_with_slash")


def test_favorites(nc_any):
    favorites = nc_any.files.list_by_criteria(["favorite"])
    favorites = [i for i in favorites if i.name != "test_generated_image.png"]
    for favorite in favorites:
        nc_any.files.setfav(favorite.user_path, False)
    favorites = nc_any.files.list_by_criteria(["favorite"])
    favorites = [i for i in favorites if i.name != "test_generated_image.png"]
    assert not favorites
    files = ("test_dir_tmp/fav1.txt", "test_dir_tmp/fav2.txt", "test_dir_tmp/fav##3.txt")
    for n in files:
        nc_any.files.upload(n, content=n)
        nc_any.files.setfav(n, True)
    favorites = nc_any.files.list_by_criteria(["favorite"])
    favorites = [i for i in favorites if i.name != "test_generated_image.png"]
    assert len(favorites) == 3
    for favorite in favorites:
        assert isinstance(favorite, FsNode)
        nc_any.files.setfav(favorite, False)
    favorites = nc_any.files.list_by_criteria(["favorite"])
    favorites = [i for i in favorites if i.name != "test_generated_image.png"]
    assert not favorites


@pytest.mark.asyncio(scope="session")
async def test_favorites_async(anc_any):
    favorites = await anc_any.files.list_by_criteria(["favorite"])
    favorites = [i for i in favorites if i.name != "test_generated_image.png"]
    for favorite in favorites:
        await anc_any.files.setfav(favorite.user_path, False)
    favorites = await anc_any.files.list_by_criteria(["favorite"])
    favorites = [i for i in favorites if i.name != "test_generated_image.png"]
    assert not favorites
    files = ("test_dir_tmp/fav1.txt", "test_dir_tmp/fav2.txt", "test_dir_tmp/fav##3.txt")
    for n in files:
        await anc_any.files.upload(n, content=n)
        await anc_any.files.setfav(n, True)
    favorites = await anc_any.files.list_by_criteria(["favorite"])
    favorites = [i for i in favorites if i.name != "test_generated_image.png"]
    assert len(favorites) == 3
    for favorite in favorites:
        assert isinstance(favorite, FsNode)
        await anc_any.files.setfav(favorite, False)
    favorites = await anc_any.files.list_by_criteria(["favorite"])
    favorites = [i for i in favorites if i.name != "test_generated_image.png"]
    assert not favorites


@pytest.mark.parametrize(
    "dest_path",
    ("test_dir_tmp/test_64_bytes.bin", "test_dir_tmp/test_64_bytes_ü.bin", "test_###_dir/test_64_bytes_ü.bin"),
)
def test_copy_file(nc_any, rand_bytes, dest_path):
    copied_file = nc_any.files.copy("test_64_bytes.bin", dest_path)
    assert copied_file.file_id
    assert copied_file.is_dir is False
    assert nc_any.files.download(dest_path) == rand_bytes
    with pytest.raises(NextcloudException):
        nc_any.files.copy("test_64_bytes.bin", dest_path)
    copied_file = nc_any.files.copy("test_12345_text.txt", dest_path, overwrite=True)
    assert copied_file.file_id
    assert copied_file.is_dir is False
    assert nc_any.files.download(dest_path) == b"12345"
    nc_any.files.delete(copied_file)


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "dest_path",
    ("test_dir_tmp/test_64_bytes.bin", "test_dir_tmp/test_64_bytes_ü.bin", "test_###_dir/test_64_bytes_ü.bin"),
)
async def test_copy_file_async(anc_any, rand_bytes, dest_path):
    copied_file = await anc_any.files.copy("test_64_bytes.bin", dest_path)
    assert copied_file.file_id
    assert copied_file.is_dir is False
    assert await anc_any.files.download(dest_path) == rand_bytes
    with pytest.raises(NextcloudException):
        await anc_any.files.copy("test_64_bytes.bin", dest_path)
    copied_file = await anc_any.files.copy("test_12345_text.txt", dest_path, overwrite=True)
    assert copied_file.file_id
    assert copied_file.is_dir is False
    assert await anc_any.files.download(dest_path) == b"12345"
    await anc_any.files.delete(copied_file)


@pytest.mark.parametrize(
    "dest_path",
    ("test_dir_tmp/dest move test file", "test_dir_tmp/dest move test file-ä", "test_###_dir/dest move test file-ä"),
)
def test_move_file(nc_any, dest_path):
    src = "test_dir_tmp/src move test file"
    content = b"content of the file"
    content2 = b"content of the file-second part"
    nc_any.files.upload(src, content=content)
    nc_any.files.delete(dest_path, not_fail=True)
    result = nc_any.files.move(src, dest_path)
    assert result.etag
    assert result.file_id
    assert result.is_dir is False
    assert nc_any.files.download(dest_path) == content
    with pytest.raises(NextcloudException):
        nc_any.files.download(src)
    nc_any.files.upload(src, content=content2)
    with pytest.raises(NextcloudException):
        nc_any.files.move(src, dest_path)
    result = nc_any.files.move(src, dest_path, overwrite=True)
    assert result.etag
    assert result.file_id
    assert result.is_dir is False
    with pytest.raises(NextcloudException):
        nc_any.files.download(src)
    assert nc_any.files.download(dest_path) == content2
    nc_any.files.delete(dest_path)


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "dest_path",
    ("test_dir_tmp/dest move test file", "test_dir_tmp/dest move test file-ä", "test_###_dir/dest move test file-ä"),
)
async def test_move_file_async(anc_any, dest_path):
    src = "test_dir_tmp/src move test file"
    content = b"content of the file"
    content2 = b"content of the file-second part"
    await anc_any.files.upload(src, content=content)
    await anc_any.files.delete(dest_path, not_fail=True)
    result = await anc_any.files.move(src, dest_path)
    assert result.etag
    assert result.file_id
    assert result.is_dir is False
    assert await anc_any.files.download(dest_path) == content
    with pytest.raises(NextcloudException):
        await anc_any.files.download(src)
    await anc_any.files.upload(src, content=content2)
    with pytest.raises(NextcloudException):
        await anc_any.files.move(src, dest_path)
    result = await anc_any.files.move(src, dest_path, overwrite=True)
    assert result.etag
    assert result.file_id
    assert result.is_dir is False
    with pytest.raises(NextcloudException):
        await anc_any.files.download(src)
    assert await anc_any.files.download(dest_path) == content2
    await anc_any.files.delete(dest_path)


def test_move_copy_dir(nc_any):
    result = nc_any.files.copy("/test_dir/subdir", "test_dir_tmp/test_copy_dir")
    assert result.file_id
    assert result.is_dir
    assert nc_any.files.by_path(result).is_dir
    assert len(nc_any.files.listdir("test_dir_tmp/test_copy_dir")) == len(nc_any.files.listdir("test_dir/subdir"))
    result = nc_any.files.move("test_dir_tmp/test_copy_dir", "test_dir_tmp/test_move_dir")
    with pytest.raises(NextcloudException):
        nc_any.files.listdir("test_dir_tmp/test_copy_dir")
    assert result.file_id
    assert result.is_dir
    assert nc_any.files.by_path(result).is_dir
    assert len(nc_any.files.listdir("test_dir_tmp/test_move_dir")) == 4
    nc_any.files.delete("test_dir_tmp/test_move_dir")


@pytest.mark.asyncio(scope="session")
async def test_move_copy_dir_async(anc_any):
    result = await anc_any.files.copy("/test_dir/subdir", "test_dir_tmp/test_copy_dir")
    assert result.file_id
    assert result.is_dir
    assert (await anc_any.files.by_path(result)).is_dir
    assert len(await anc_any.files.listdir("test_dir_tmp/test_copy_dir")) == len(
        await anc_any.files.listdir("test_dir/subdir")
    )
    result = await anc_any.files.move("test_dir_tmp/test_copy_dir", "test_dir_tmp/test_move_dir")
    with pytest.raises(NextcloudException):
        await anc_any.files.listdir("test_dir_tmp/test_copy_dir")
    assert result.file_id
    assert result.is_dir
    assert (await anc_any.files.by_path(result)).is_dir
    assert len(await anc_any.files.listdir("test_dir_tmp/test_move_dir")) == 4
    await anc_any.files.delete("test_dir_tmp/test_move_dir")


def test_find_files_listdir_depth(nc_any):
    result = nc_any.files.find(["and", "gt", "size", 0, "like", "mime", "image/%"], path="test_dir")
    assert len(result) == 2
    result2 = nc_any.files.find(["and", "gt", "size", 0, "like", "mime", "image/%"], path="/test_dir")
    assert len(result2) == 2
    assert result == result2
    result = nc_any.files.find(["and", "gt", "size", 0, "like", "mime", "image/%"], path="test_dir/subdir/")
    assert len(result) == 1
    result = nc_any.files.find(["and", "gt", "size", 0, "like", "mime", "image/%"], path="test_dir/subdir")
    assert len(result) == 1
    result = nc_any.files.find(["and", "gt", "size", 1024 * 1024, "like", "mime", "image/%"], path="test_dir")
    assert len(result) == 0
    result = nc_any.files.find(
        ["or", "and", "gt", "size", 0, "like", "mime", "image/%", "like", "mime", "text/%"], path="test_dir"
    )
    assert len(result) == 6
    result = nc_any.files.find(["eq", "name", "test_12345_text.txt"], path="test_dir")
    assert len(result) == 2
    result = nc_any.files.find(["like", "name", "test_%"], path="/test_dir")
    assert len(result) == 9
    assert not nc_any.files.find(["eq", "name", "no such file"], path="test_dir")
    assert not nc_any.files.find(["like", "name", "no%such%file"], path="test_dir")
    result = nc_any.files.find(["like", "mime", "text/%"], path="test_dir")
    assert len(result) == 4


def test_listdir_depth(nc_any):
    result = nc_any.files.listdir("test_dir/", depth=1)
    result2 = nc_any.files.listdir("test_dir")
    assert result == result2
    assert len(result) == 6
    result = nc_any.files.listdir("test_dir/", depth=2)
    result2 = nc_any.files.listdir("test_dir", depth=-1)
    assert result == result2
    assert len(result) == 10


@pytest.mark.asyncio(scope="session")
async def test_listdir_depth_async(anc_any):
    result = await anc_any.files.listdir("test_dir/", depth=1)
    result2 = await anc_any.files.listdir("test_dir")
    assert result == result2
    assert len(result) == 6
    result = await anc_any.files.listdir("test_dir/", depth=2)
    result2 = await anc_any.files.listdir("test_dir", depth=-1)
    assert result == result2
    assert len(result) == 10


def test_fs_node_fields(nc_any):
    results = nc_any.files.listdir("/test_dir")
    assert len(results) == 6
    for _, result in enumerate(results):
        assert result.user == "admin"
        if result.name == "subdir":
            assert result.user_path == "test_dir/subdir/"
            assert result.is_dir
            assert result.full_path == "files/admin/test_dir/subdir/"
            assert result.info.size == 2364
            assert result.info.content_length == 0
            assert result.info.permissions == "RGDNVCK"
            assert result.info.favorite is False
            assert not result.info.mimetype
        elif result.name == "test_empty_child_dir":
            assert result.user_path == "test_dir/test_empty_child_dir/"
            assert result.is_dir
            assert result.full_path == "files/admin/test_dir/test_empty_child_dir/"
            assert result.info.size == 0
            assert result.info.content_length == 0
            assert result.info.permissions == "RGDNVCK"
            assert result.info.favorite is False
            assert not result.info.mimetype
        elif result.name == "test_generated_image.png":
            assert result.user_path == "test_dir/test_generated_image.png"
            assert not result.is_dir
            assert result.full_path == "files/admin/test_dir/test_generated_image.png"
            assert result.info.size > 900
            assert result.info.size == result.info.content_length
            assert result.info.permissions == "RGDNVW"
            assert result.info.favorite is True
            assert result.info.mimetype == "image/png"
        elif result.name == "test_empty_text.txt":
            assert result.user_path == "test_dir/test_empty_text.txt"
            assert not result.is_dir
            assert result.full_path == "files/admin/test_dir/test_empty_text.txt"
            assert not result.info.size
            assert not result.info.content_length
            assert result.info.permissions == "RGDNVW"
            assert result.info.favorite is False
            assert result.info.mimetype == "text/plain"

        res_by_id = nc_any.files.by_id(result.file_id)
        assert res_by_id
        res_by_path = nc_any.files.by_path(result.user_path)
        assert res_by_path
        assert res_by_id.info == res_by_path.info == result.info
        assert res_by_id.full_path == res_by_path.full_path == result.full_path
        assert res_by_id.user == res_by_path.user == result.user
        assert res_by_id.etag == res_by_path.etag == result.etag
        assert res_by_id.info.last_modified == res_by_path.info.last_modified == result.info.last_modified


def test_makedirs(nc_any):
    nc_any.files.delete("/test_dir_tmp/abc", not_fail=True)
    result = nc_any.files.makedirs("/test_dir_tmp/abc/def", exist_ok=True)
    assert result.is_dir
    with pytest.raises(NextcloudException) as exc_info:
        nc_any.files.makedirs("/test_dir_tmp/abc/def")
    assert exc_info.value.status_code == 405
    result = nc_any.files.makedirs("/test_dir_tmp/abc/def", exist_ok=True)
    assert result is None


@pytest.mark.asyncio(scope="session")
async def test_makedirs_async(anc_any):
    await anc_any.files.delete("/test_dir_tmp/abc", not_fail=True)
    result = await anc_any.files.makedirs("/test_dir_tmp/abc/def", exist_ok=True)
    assert result.is_dir
    with pytest.raises(NextcloudException) as exc_info:
        await anc_any.files.makedirs("/test_dir_tmp/abc/def")
    assert exc_info.value.status_code == 405
    result = await anc_any.files.makedirs("/test_dir_tmp/abc/def", exist_ok=True)
    assert result is None


def test_fs_node_str(nc_any):
    fs_node1 = nc_any.files.by_path("test_empty_dir_in_dir")
    str_fs_node1 = str(fs_node1)
    assert str_fs_node1.find("Dir") != -1
    assert str_fs_node1.find("test_empty_dir_in_dir") != -1
    assert str_fs_node1.find(f"id={fs_node1.file_id}") != -1
    fs_node2 = nc_any.files.by_path("test_12345_text.txt")
    str_fs_node2 = str(fs_node2)
    assert str_fs_node2.find("File") != -1
    assert str_fs_node2.find("test_12345_text.txt") != -1
    assert str_fs_node2.find(f"id={fs_node2.file_id}") != -1


def _test_download_as_zip(result: Path, n: int):
    if n == 1:
        with zipfile.ZipFile(result, "r") as zip_ref:
            assert zip_ref.filelist[0].filename == "test_dir/"
            assert not zip_ref.filelist[0].file_size
            assert zip_ref.filelist[1].filename == "test_dir/subdir/"
            assert not zip_ref.filelist[1].file_size
            assert zip_ref.filelist[2].filename == "test_dir/subdir/test_12345_text.txt"
            assert zip_ref.filelist[2].file_size == 5
            assert zip_ref.filelist[3].filename == "test_dir/subdir/test_64_bytes.bin"
            assert zip_ref.filelist[3].file_size == 64
            assert len(zip_ref.filelist) == 11
    elif n == 2:
        with zipfile.ZipFile(result, "r") as zip_ref:
            assert zip_ref.filelist[0].filename == "test_empty_dir_in_dir/"
            assert not zip_ref.filelist[0].file_size
            assert zip_ref.filelist[1].filename == "test_empty_dir_in_dir/test_empty_child_dir/"
            assert not zip_ref.filelist[1].file_size
            assert len(zip_ref.filelist) == 2
    else:
        with zipfile.ZipFile(result, "r") as zip_ref:
            assert zip_ref.filelist[0].filename == "test_empty_dir/"
            assert not zip_ref.filelist[0].file_size
            assert len(zip_ref.filelist) == 1


def test_download_as_zip(nc):
    old_headers = nc.response_headers
    result = nc.files.download_directory_as_zip("test_dir")
    assert nc.response_headers != old_headers
    try:
        _test_download_as_zip(result, 1)
    finally:
        os.remove(result)
    old_headers = nc.response_headers
    result = nc.files.download_directory_as_zip("test_empty_dir_in_dir", "2.zip")
    assert nc.response_headers != old_headers
    try:
        assert str(result) == "2.zip"
        _test_download_as_zip(result, 2)
    finally:
        os.remove("2.zip")
    result = nc.files.download_directory_as_zip("/test_empty_dir", "empty_folder.zip")
    try:
        assert str(result) == "empty_folder.zip"
        _test_download_as_zip(result, 3)
    finally:
        os.remove("empty_folder.zip")


@pytest.mark.asyncio(scope="session")
async def test_download_as_zip_async(anc):
    old_headers = anc.response_headers
    result = await anc.files.download_directory_as_zip("test_dir")
    assert anc.response_headers != old_headers
    try:
        _test_download_as_zip(result, 1)
    finally:
        os.remove(result)
    old_headers = anc.response_headers
    result = await anc.files.download_directory_as_zip("test_empty_dir_in_dir", "2.zip")
    assert anc.response_headers != old_headers
    try:
        assert str(result) == "2.zip"
        _test_download_as_zip(result, 2)
    finally:
        os.remove("2.zip")
    result = await anc.files.download_directory_as_zip("/test_empty_dir", "empty_folder.zip")
    try:
        assert str(result) == "empty_folder.zip"
        _test_download_as_zip(result, 3)
    finally:
        os.remove("empty_folder.zip")


def test_fs_node_is_xx(nc_any):
    folder = nc_any.files.listdir("test_empty_dir", exclude_self=False)[0]
    assert folder.is_dir
    assert folder.is_creatable
    assert folder.is_readable
    assert folder.is_deletable
    assert folder.is_shareable
    assert folder.is_updatable
    assert not folder.is_mounted
    assert not folder.is_shared


def test_fs_node_last_modified_time():
    fs_node = FsNode("", last_modified="wrong time")
    assert fs_node.info.last_modified == datetime(1970, 1, 1)
    fs_node = FsNode("", last_modified="Sat, 29 Jul 2023 11:56:31")
    assert fs_node.info.last_modified == datetime(2023, 7, 29, 11, 56, 31)
    fs_node = FsNode("", last_modified=datetime(2022, 4, 5, 1, 2, 3))
    assert fs_node.info.last_modified == datetime(2022, 4, 5, 1, 2, 3)


@pytest.mark.parametrize(
    "file_path", ("test_dir_tmp/trashbin_test", "test_dir_tmp/trashbin_test-ä", "test_dir_tmp/trashbin_test-1##3")
)
def test_trashbin(nc_any, file_path):
    r = nc_any.files.trashbin_list()
    assert isinstance(r, list)
    new_file = nc_any.files.upload(file_path, content=b"")
    nc_any.files.delete(new_file)
    # minimum one object now in a trashbin
    r = nc_any.files.trashbin_list()
    assert r
    # clean up trashbin
    nc_any.files.trashbin_cleanup()
    # no objects should be in trashbin
    r = nc_any.files.trashbin_list()
    assert not r
    new_file = nc_any.files.upload(file_path, content=b"")
    nc_any.files.delete(new_file)
    # one object now in a trashbin
    r = nc_any.files.trashbin_list()
    assert len(r) == 1
    # check types of FsNode properties
    i: FsNode = r[0]
    assert i.info.in_trash is True
    assert i.info.trashbin_filename.find("trashbin_test") != -1
    assert i.info.trashbin_original_location == file_path
    assert isinstance(i.info.trashbin_deletion_time, int)
    # restore that object
    nc_any.files.trashbin_restore(r[0])
    # no files in trashbin
    r = nc_any.files.trashbin_list()
    assert not r
    # move a restored object to trashbin again
    nc_any.files.delete(new_file)
    # one object now in a trashbin
    r = nc_any.files.trashbin_list()
    assert len(r) == 1
    # remove one object from a trashbin
    nc_any.files.trashbin_delete(r[0])
    # NextcloudException with status_code 404
    with pytest.raises(NextcloudException) as e:
        nc_any.files.trashbin_delete(r[0])
    assert e.value.status_code == 404
    nc_any.files.trashbin_delete(r[0], not_fail=True)
    # no files in trashbin
    r = nc_any.files.trashbin_list()
    assert not r


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "file_path", ("test_dir_tmp/trashbin_test", "test_dir_tmp/trashbin_test-ä", "test_dir_tmp/trashbin_test-1##3")
)
async def test_trashbin_async(anc_any, file_path):
    r = await anc_any.files.trashbin_list()
    assert isinstance(r, list)
    new_file = await anc_any.files.upload(file_path, content=b"")
    await anc_any.files.delete(new_file)
    # minimum one object now in a trashbin
    r = await anc_any.files.trashbin_list()
    assert r
    # clean up trashbin
    await anc_any.files.trashbin_cleanup()
    # no objects should be in trashbin
    r = await anc_any.files.trashbin_list()
    assert not r
    new_file = await anc_any.files.upload(file_path, content=b"")
    await anc_any.files.delete(new_file)
    # one object now in a trashbin
    r = await anc_any.files.trashbin_list()
    assert len(r) == 1
    # check types of FsNode properties
    i: FsNode = r[0]
    assert i.info.in_trash is True
    assert i.info.trashbin_filename.find("trashbin_test") != -1
    assert i.info.trashbin_original_location == file_path
    assert isinstance(i.info.trashbin_deletion_time, int)
    # restore that object
    await anc_any.files.trashbin_restore(r[0])
    # no files in trashbin
    r = await anc_any.files.trashbin_list()
    assert not r
    # move a restored object to trashbin again
    await anc_any.files.delete(new_file)
    # one object now in a trashbin
    r = await anc_any.files.trashbin_list()
    assert len(r) == 1
    # remove one object from a trashbin
    await anc_any.files.trashbin_delete(r[0])
    # NextcloudException with status_code 404
    with pytest.raises(NextcloudException) as e:
        await anc_any.files.trashbin_delete(r[0])
    assert e.value.status_code == 404
    await anc_any.files.trashbin_delete(r[0], not_fail=True)
    # no files in trashbin
    r = await anc_any.files.trashbin_list()
    assert not r


@pytest.mark.parametrize(
    "dest_path",
    ("/test_dir_tmp/file_versions.txt", "/test_dir_tmp/file_versions-ä.txt", "test_dir_tmp/file_versions-1##3"),
)
def test_file_versions(nc_any, dest_path):
    if nc_any.check_capabilities("files.versioning"):
        pytest.skip("Need 'Versions' App to be enabled.")
    for i in (0, 1):
        nc_any.files.delete(dest_path, not_fail=True)
        nc_any.files.upload(dest_path, content=b"22")
        new_file = nc_any.files.upload(dest_path, content=b"333")
        if i:
            new_file = nc_any.files.by_id(new_file)
        versions = nc_any.files.get_versions(new_file)
        assert versions
        version_str = str(versions[0])
        assert version_str.find("File version") != -1
        assert version_str.find("bytes size") != -1
        nc_any.files.restore_version(versions[0])
        assert nc_any.files.download(new_file) == b"22"


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "dest_path",
    ("/test_dir_tmp/file_versions.txt", "/test_dir_tmp/file_versions-ä.txt", "test_dir_tmp/file_versions-1##3"),
)
async def test_file_versions_async(anc_any, dest_path):
    if await anc_any.check_capabilities("files.versioning"):
        pytest.skip("Need 'Versions' App to be enabled.")
    for i in (0, 1):
        await anc_any.files.delete(dest_path, not_fail=True)
        await anc_any.files.upload(dest_path, content=b"22")
        new_file = await anc_any.files.upload(dest_path, content=b"333")
        if i:
            new_file = await anc_any.files.by_id(new_file)
        versions = await anc_any.files.get_versions(new_file)
        assert versions
        version_str = str(versions[0])
        assert version_str.find("File version") != -1
        assert version_str.find("bytes size") != -1
        await anc_any.files.restore_version(versions[0])
        assert await anc_any.files.download(new_file) == b"22"


def test_create_update_delete_tag(nc_any):
    with contextlib.suppress(NextcloudExceptionNotFound):
        nc_any.files.delete_tag(nc_any.files.tag_by_name("test_nc_py_api"))
    with contextlib.suppress(NextcloudExceptionNotFound):
        nc_any.files.delete_tag(nc_any.files.tag_by_name("test_nc_py_api2"))
    nc_any.files.create_tag("test_nc_py_api", True, True)
    tag = nc_any.files.tag_by_name("test_nc_py_api")
    assert isinstance(tag.tag_id, int)
    assert tag.display_name == "test_nc_py_api"
    assert tag.user_visible is True
    assert tag.user_assignable is True
    nc_any.files.update_tag(tag, "test_nc_py_api2", False, False)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_any.files.tag_by_name("test_nc_py_api")
    tag = nc_any.files.tag_by_name("test_nc_py_api2")
    assert tag.display_name == "test_nc_py_api2"
    assert tag.user_visible is False
    assert tag.user_assignable is False
    for i in nc_any.files.list_tags():
        assert str(i).find("name=") != -1
    nc_any.files.delete_tag(tag)
    with pytest.raises(ValueError):
        nc_any.files.update_tag(tag)


@pytest.mark.asyncio(scope="session")
async def test_create_update_delete_tag_async(anc_any):
    with contextlib.suppress(NextcloudExceptionNotFound):
        await anc_any.files.delete_tag(await anc_any.files.tag_by_name("test_nc_py_api"))
    with contextlib.suppress(NextcloudExceptionNotFound):
        await anc_any.files.delete_tag(await anc_any.files.tag_by_name("test_nc_py_api2"))
    await anc_any.files.create_tag("test_nc_py_api", True, True)
    tag = await anc_any.files.tag_by_name("test_nc_py_api")
    assert isinstance(tag.tag_id, int)
    assert tag.display_name == "test_nc_py_api"
    assert tag.user_visible is True
    assert tag.user_assignable is True
    await anc_any.files.update_tag(tag, "test_nc_py_api2", False, False)
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_any.files.tag_by_name("test_nc_py_api")
    tag = await anc_any.files.tag_by_name("test_nc_py_api2")
    assert tag.display_name == "test_nc_py_api2"
    assert tag.user_visible is False
    assert tag.user_assignable is False
    for i in await anc_any.files.list_tags():
        assert str(i).find("name=") != -1
    await anc_any.files.delete_tag(tag)
    with pytest.raises(ValueError):
        await anc_any.files.update_tag(tag)


def test_assign_unassign_tag(nc_any):
    with contextlib.suppress(NextcloudExceptionNotFound):
        nc_any.files.delete_tag(nc_any.files.tag_by_name("test_nc_py_api"))
    with contextlib.suppress(NextcloudExceptionNotFound):
        nc_any.files.delete_tag(nc_any.files.tag_by_name("test_nc_py_api2"))
    nc_any.files.create_tag("test_nc_py_api", True, False)
    nc_any.files.create_tag("test_nc_py_api2", False, False)
    tag1 = nc_any.files.tag_by_name("test_nc_py_api")
    assert tag1.user_visible is True
    assert tag1.user_assignable is False
    tag2 = nc_any.files.tag_by_name("test_nc_py_api2")
    assert tag2.user_visible is False
    assert tag2.user_assignable is False
    new_file = nc_any.files.upload("/test_dir_tmp/tag_test.txt", content=b"")
    new_file = nc_any.files.by_id(new_file)
    assert len(nc_any.files.list_by_criteria(tags=[tag1])) == 0
    nc_any.files.assign_tag(new_file, tag1)
    assert len(nc_any.files.list_by_criteria(tags=[tag1])) == 1
    assert len(nc_any.files.list_by_criteria(["favorite"], tags=[tag1])) == 0
    assert len(nc_any.files.list_by_criteria(tags=[tag1, tag2.tag_id])) == 0
    nc_any.files.assign_tag(new_file, tag2.tag_id)
    assert len(nc_any.files.list_by_criteria(tags=[tag1, tag2.tag_id])) == 1
    nc_any.files.unassign_tag(new_file, tag1)
    assert len(nc_any.files.list_by_criteria(tags=[tag1])) == 0
    nc_any.files.assign_tag(new_file, tag1)
    with pytest.raises(ValueError):
        nc_any.files.list_by_criteria()


@pytest.mark.asyncio(scope="session")
async def test_assign_unassign_tag_async(anc_any):
    with contextlib.suppress(NextcloudExceptionNotFound):
        await anc_any.files.delete_tag(await anc_any.files.tag_by_name("test_nc_py_api"))
    with contextlib.suppress(NextcloudExceptionNotFound):
        await anc_any.files.delete_tag(await anc_any.files.tag_by_name("test_nc_py_api2"))
    await anc_any.files.create_tag("test_nc_py_api", True, False)
    await anc_any.files.create_tag("test_nc_py_api2", False, False)
    tag1 = await anc_any.files.tag_by_name("test_nc_py_api")
    assert tag1.user_visible is True
    assert tag1.user_assignable is False
    tag2 = await anc_any.files.tag_by_name("test_nc_py_api2")
    assert tag2.user_visible is False
    assert tag2.user_assignable is False
    new_file = await anc_any.files.upload("/test_dir_tmp/tag_test.txt", content=b"")
    new_file = await anc_any.files.by_id(new_file)
    assert len(await anc_any.files.list_by_criteria(tags=[tag1])) == 0
    await anc_any.files.assign_tag(new_file, tag1)
    assert len(await anc_any.files.list_by_criteria(tags=[tag1])) == 1
    assert len(await anc_any.files.list_by_criteria(["favorite"], tags=[tag1])) == 0
    assert len(await anc_any.files.list_by_criteria(tags=[tag1, tag2.tag_id])) == 0
    await anc_any.files.assign_tag(new_file, tag2.tag_id)
    assert len(await anc_any.files.list_by_criteria(tags=[tag1, tag2.tag_id])) == 1
    await anc_any.files.unassign_tag(new_file, tag1)
    assert len(await anc_any.files.list_by_criteria(tags=[tag1])) == 0
    await anc_any.files.assign_tag(new_file, tag1)
    with pytest.raises(ValueError):
        await anc_any.files.list_by_criteria()


def __check_lock_info(fs_node: FsNode):
    assert isinstance(fs_node.lock_info.owner, str)
    assert isinstance(fs_node.lock_info.owner_display_name, str)
    assert isinstance(fs_node.lock_info.type, LockType)
    assert isinstance(fs_node.lock_info.lock_creation_time, datetime)
    assert isinstance(fs_node.lock_info.lock_ttl, int)
    assert isinstance(fs_node.lock_info.owner_editor, str)


def test_file_locking(nc_any):
    if nc_any.check_capabilities("files.locking"):
        pytest.skip("Files Locking App is not installed")
    test_file = nc_any.files.upload("/test_dir/test_lock", content="")
    assert nc_any.files.by_id(test_file).lock_info.is_locked is False
    with pytest.raises(NextcloudException) as e:
        nc_any.files.unlock(test_file)
    assert e.value.status_code == 412
    nc_any.files.lock(test_file)
    locked_file = nc_any.files.by_id(test_file)
    assert locked_file.lock_info.is_locked is True
    __check_lock_info(locked_file)
    nc_any.files.unlock(test_file)
    with pytest.raises(NextcloudException) as e:
        nc_any.files.unlock(test_file)
    assert e.value.status_code == 412


@pytest.mark.asyncio(scope="session")
async def test_file_locking_async(anc_any):
    if await anc_any.check_capabilities("files.locking"):
        pytest.skip("Files Locking App is not installed")
    test_file = await anc_any.files.upload("/test_dir/test_lock_async", content="")
    assert (await anc_any.files.by_id(test_file)).lock_info.is_locked is False
    with pytest.raises(NextcloudException) as e:
        await anc_any.files.unlock(test_file)
    assert e.value.status_code == 412
    await anc_any.files.lock(test_file)
    locked_file = await anc_any.files.by_id(test_file)
    assert locked_file.lock_info.is_locked is True
    __check_lock_info(locked_file)
    await anc_any.files.unlock(test_file)
    with pytest.raises(NextcloudException) as e:
        await anc_any.files.unlock(test_file)
    assert e.value.status_code == 412
