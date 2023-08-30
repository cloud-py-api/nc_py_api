import math
import os
import zipfile
from datetime import datetime
from io import BytesIO
from random import choice, randbytes
from string import ascii_lowercase
from tempfile import NamedTemporaryFile
from zlib import adler32

import pytest
from PIL import Image

from nc_py_api import FsNode, NextcloudException


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


def test_list_user_root(nc):
    user_root = nc.files.listdir()
    assert user_root
    for obj in user_root:
        assert obj.user == nc.user
        assert obj.has_extra
        assert obj.name
        assert obj.user_path
        assert obj.file_id
        assert obj.etag
    root_node = FsNode(full_path=f"files/{nc.user}/")
    user_root2 = nc.files.listdir(root_node)
    assert user_root == user_root2


def test_list_user_root_self_exclude(nc):
    user_root = nc.files.listdir()
    user_root_with_self = nc.files.listdir(exclude_self=False)
    assert len(user_root_with_self) == 1 + len(user_root)
    self_res = [i for i in user_root_with_self if not i.user_path][0]
    for i in user_root:
        assert self_res != i
    assert self_res.has_extra
    assert self_res.file_id
    assert self_res.user == nc.user
    assert self_res.name
    assert self_res.etag
    assert self_res.full_path == f"files/{nc.user}/"


def test_list_empty_child_dir(nc):
    nc.files.makedirs("empty_child_folder")
    try:
        assert not len(nc.files.listdir("empty_child_folder"))
        result = nc.files.listdir("empty_child_folder", exclude_self=False)
        assert len(result)
        result = result[0]
        assert result.file_id
        assert result.user == nc.user
        assert result.name == "empty_child_folder"
        assert result.etag
        assert result.full_path == f"files/{nc.user}/empty_child_folder/"
    finally:
        nc.files.delete("empty_child_folder")


def test_list_dir_wrong_args(nc_any):
    with pytest.raises(ValueError):
        nc_any.files.listdir(depth=0, exclude_self=True)


def test_by_path(nc_any):
    result = nc_any.files.by_path("")
    result2 = nc_any.files.by_path("/")
    assert isinstance(result, FsNode)
    assert isinstance(result2, FsNode)
    assert result == result2
    assert result.is_dir == result2.is_dir
    assert result.is_dir
    assert result.user == result2.user
    assert result.user == nc_any.user


def test_file_download(nc):
    content = randbytes(64)
    new_file = nc.files.upload("test_file.txt", content=content)
    srv_admin_manual1 = nc.files.download(new_file)
    srv_admin_manual2 = nc.files.download("/test_file.txt")
    assert srv_admin_manual1 == srv_admin_manual2
    assert srv_admin_manual1 == content


@pytest.mark.parametrize("data_type", ("str", "bytes"))
@pytest.mark.parametrize("chunk_size", (15, 32, 64, None))
def test_file_download2stream(nc, data_type, chunk_size):
    srv_admin_manual_buf = MyBytesIO()
    content = "".join(choice(ascii_lowercase) for _ in range(64)) if data_type == "str" else randbytes(64)
    nc.files.upload("test_file.txt", content=content)
    old_headers = nc.response_headers
    if chunk_size is not None:
        nc.files.download2stream("/test_file.txt", srv_admin_manual_buf, chunk_size=chunk_size)
    else:
        nc.files.download2stream("/test_file.txt", srv_admin_manual_buf)
    assert nc.response_headers != old_headers
    assert nc.files.download("test_file.txt") == srv_admin_manual_buf.getbuffer()
    if chunk_size is None:
        assert srv_admin_manual_buf.n_write_calls == 1
    else:
        assert srv_admin_manual_buf.n_write_calls == math.ceil(64 / chunk_size)


def test_file_download2file(nc):
    content = randbytes(64)
    nc.files.upload("tmp.bin", content)
    with NamedTemporaryFile() as tmp_file:
        nc.files.download2stream("tmp.bin", tmp_file.name)
        assert tmp_file.read() == content


def test_file_download2stream_invalid_type(nc_any):
    for test_type in (
        b"13",
        int(55),
    ):
        with pytest.raises(TypeError):
            nc_any.files.download2stream("xxx", test_type)


def test_file_upload_stream_invalid_type(nc_any):
    for test_type in (
        b"13",
        int(55),
    ):
        with pytest.raises(TypeError):
            nc_any.files.upload_stream("xxx", test_type)


def test_file_download_not_found(nc):
    with pytest.raises(NextcloudException):
        nc.files.download("file that does not exist on the server")
    with pytest.raises(NextcloudException):
        nc.files.listdir("non existing path")


def test_file_download2stream_not_found(nc):
    buf = BytesIO()
    with pytest.raises(NextcloudException):
        nc.files.download2stream("file that does not exist on the server", buf)
    with pytest.raises(NextcloudException):
        nc.files.download2stream("non existing path", buf)


def test_file_upload(nc):
    file_name = "12345.txt"
    result = nc.files.upload(file_name, content=b"\x31\x32")
    assert nc.files.by_id(result).info.size == 2
    assert nc.files.download(file_name) == b"\x31\x32"
    result = nc.files.upload(f"/{file_name}", content=b"\x31\x32\x33")
    assert not result.has_extra
    result = nc.files.by_path(result)
    assert result.info.size == 3
    assert result.is_updatable
    assert not result.is_creatable
    assert nc.files.download(file_name) == b"\x31\x32\x33"
    nc.files.upload(file_name, content="life is good")
    assert nc.files.download(file_name).decode("utf-8") == "life is good"


@pytest.mark.parametrize("chunk_size", (63, 64, 65, None))
def test_file_upload_chunked(nc, chunk_size):
    file_name = "chunked.bin"
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


def test_file_upload_file(nc):
    content = randbytes(64)
    with NamedTemporaryFile() as tmp_file:
        tmp_file.write(content)
        tmp_file.flush()
        nc.files.upload_stream("tmp.bin", tmp_file.name)
    assert nc.files.download("tmp.bin") == content


@pytest.mark.parametrize(
    "path", ("chunked_zero.bin", "chunked_zero.bin/", "chunked_zero.bin//", "/chunked_zero.bin", "/chunked_zero.bin/")
)
def test_file_upload_chunked_zero_size(nc_any, path):
    buf_upload = MyBytesIO()
    nc_any.files.delete("chunked_zero.bin", not_fail=True)
    result = nc_any.files.upload_stream(path, fp=buf_upload)
    assert nc_any.files.download("chunked_zero.bin") == b""
    assert not nc_any.files.by_path(result.user_path).info.size
    assert not result.is_dir
    assert result.full_path.startswith("files/")
    assert result.name == "chunked_zero.bin"


@pytest.mark.parametrize("path", ("12345.txt", "12345.txt/", "12345.txt//", "/12345.txt", "/12345.txt/"))
def test_file_upload_empty(nc_any, path):
    nc_any.files.delete("12345.txt", not_fail=True)
    result = nc_any.files.upload(path, content="")
    assert nc_any.files.download("12345.txt") == b""
    assert not result.is_dir
    assert result.name == "12345.txt"
    assert result.full_path.startswith("files/")


def test_file_delete(nc_any):
    file_name = "12345.txt"
    nc_any.files.upload(file_name, content="")
    nc_any.files.delete(file_name)
    with pytest.raises(NextcloudException):
        nc_any.files.delete(file_name)
    nc_any.files.delete(file_name, not_fail=True)


@pytest.mark.parametrize("dir_name", ("1 2", "Яё", "відео та картинки", "复杂 目录 Í", "Björn", "João"))
def test_mkdir(nc, dir_name):
    nc.files.delete(dir_name, not_fail=True)
    result = nc.files.mkdir(dir_name)
    assert result.is_dir
    assert not result.has_extra
    with pytest.raises(NextcloudException):
        nc.files.mkdir(dir_name)
    nc.files.delete(dir_name)
    with pytest.raises(NextcloudException):
        nc.files.delete(dir_name)


def test_mkdir_invalid_args(nc):
    with pytest.raises(NextcloudException) as exc_info:
        nc.files.makedirs("zzzzz/    /zzzzzzzz", exist_ok=True)
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


def test_no_favorites(nc_any):
    favorites = nc_any.files.listfav()
    for favorite in favorites:
        nc_any.files.setfav(favorite.user_path, False)
    assert not nc_any.files.listfav()


def test_favorites(nc_any):
    favorites = nc_any.files.listfav()
    for favorite in favorites:
        nc_any.files.setfav(favorite.user_path, False)
    files = ("fav1.txt", "fav2.txt", "fav3.txt")
    for n in files:
        nc_any.files.upload(n, content=n)
        nc_any.files.setfav(n, True)
    favorites = nc_any.files.listfav()
    assert len(favorites) == 3
    for favorite in favorites:
        assert isinstance(favorite, FsNode)
        nc_any.files.setfav(favorite, False)
    assert len(nc_any.files.listfav()) == 0
    for n in files:
        nc_any.files.delete(n)


def test_copy_file(nc_any):
    src = "test_file.txt"
    dest = "nc_admin_man_999.pdf"
    uploaded_file = nc_any.files.upload(src, content=randbytes(64))
    assert uploaded_file.file_id
    nc_any.files.delete(dest, not_fail=True)
    copied_file = nc_any.files.copy(src, dest)
    assert copied_file.file_id
    assert not copied_file.is_dir
    try:
        assert nc_any.files.download(src) == nc_any.files.download(dest)
        with pytest.raises(NextcloudException):
            nc_any.files.copy(src, dest)
        copied_file = nc_any.files.copy(src, dest, overwrite=True)
        assert copied_file.file_id
        assert not copied_file.is_dir
    finally:
        nc_any.files.delete(dest)


def test_move_file(nc):
    src = "src move test file"
    dest = "dest move test file"
    content = b"content of the file"
    content2 = b"content of the file-second part"
    nc.files.upload(src, content=content)
    nc.files.delete(dest, not_fail=True)
    result = nc.files.move(src, dest)
    assert result.etag
    assert result.file_id
    assert not result.is_dir
    assert nc.files.download(dest) == content
    with pytest.raises(NextcloudException):
        nc.files.download(src)
    nc.files.upload(src, content=content2)
    with pytest.raises(NextcloudException):
        nc.files.move(src, dest)
    result = nc.files.move(src, dest, overwrite=True)
    assert result.etag
    assert result.file_id
    assert not result.is_dir
    with pytest.raises(NextcloudException):
        nc.files.download(src)
    assert nc.files.download(dest) == content2
    nc.files.delete(dest)


@pytest.mark.parametrize("op_type", ("move", "copy"))
def test_move_copy_dir(nc_any, op_type):
    dir_name = "test_dir"
    dest_dir_name = f"{dir_name} dest"
    nc_any.files.delete(dir_name, not_fail=True)
    nc_any.files.delete(dest_dir_name, not_fail=True)
    nc_any.files.mkdir(dir_name)
    files = ("file1.txt", "file2.txt", "file3.txt")
    for n in files:
        nc_any.files.upload(f"{dir_name}/{n}", content=n)
    result = (
        nc_any.files.move(dir_name, dest_dir_name) if op_type == "move" else nc_any.files.copy(dir_name, dest_dir_name)
    )
    assert result.file_id
    assert result.is_dir
    assert nc_any.files.by_path(result).is_dir
    assert len(nc_any.files.listdir(dest_dir_name)) == 3
    if op_type == "move":
        with pytest.raises(NextcloudException):
            nc_any.files.delete(dir_name)
    else:
        nc_any.files.delete(dir_name)
    nc_any.files.delete(dest_dir_name)


def test_find_files_listdir_depth(nc_any):
    nc_any.files.delete("test_root_folder", not_fail=True)
    im1 = BytesIO()
    im2 = BytesIO()
    im3 = BytesIO()
    Image.linear_gradient("L").resize((768, 768)).save(im1, format="PNG")
    Image.linear_gradient("L").resize((1024, 1024)).save(im2, format="GIF")
    Image.linear_gradient("L").resize((8192, 8192)).save(im3, format="JPEG")
    for i in (im1, im2, im3):
        i.seek(0)
    nc_any.files.mkdir("test_root_folder")
    nc_any.files.mkdir("test_root_folder/child_folder")
    nc_any.files.upload("test_root_folder/image1.png", content=im1.read())
    nc_any.files.upload("test_root_folder/test_root_very_unique_name768.txt", content="content!")
    nc_any.files.upload("test_root_folder/child_folder/image2.gif", content=im2.read())
    nc_any.files.upload("test_root_folder/child_folder/image3.jpg", content=im3.read())
    nc_any.files.upload("test_root_folder/child_folder/test.txt", content="content!")
    result = nc_any.files.find(["and", "gt", "size", 1 * 1024, "like", "mime", "image/%"], path="test_root_folder")
    assert len(result) == 3
    result2 = nc_any.files.find(["and", "gt", "size", 1 * 1024, "like", "mime", "image/%"], path="/test_root_folder")
    assert len(result2) == 3
    assert result == result2
    result = nc_any.files.find(["and", "gt", "size", 40 * 1024, "like", "mime", "image/%"], path="test_root_folder")
    assert len(result) == 2
    result = nc_any.files.find(["and", "gt", "size", 100 * 1024, "like", "mime", "image/%"], path="test_root_folder")
    assert len(result) == 1
    result = nc_any.files.find(["and", "gt", "size", 1024 * 1024, "like", "mime", "image/%"], path="test_root_folder")
    assert len(result) == 0
    result = nc_any.files.find(
        ["or", "and", "gt", "size", 0, "like", "mime", "image/%", "like", "mime", "text/%"], path="test_root_folder"
    )
    assert len(result) == 5
    result = nc_any.files.find(["eq", "name", "test_root_very_unique_name768.txt"])
    assert len(result) == 1
    result = nc_any.files.find(["like", "name", "test_root_very_unique_name76%"])
    assert len(result) == 1
    result = nc_any.files.find(
        ["eq", "name", "test_root_very_unique_name768.txt"], path="test_root_folder/child_folder"
    )
    assert not result
    result = nc_any.files.find(["like", "name", "test_root_very_unique_name76%"], path="test_root_folder/child_folder")
    assert not result
    result = nc_any.files.find(["gte", "size", 0], path="test_root_folder")
    assert len(result) == 6  # 1 sub dir + 3 images + 2 text files
    result = nc_any.files.find(["like", "mime", "text/%"], path="test_root_folder")
    assert len(result) == 2
    result = nc_any.files.listdir("test_root_folder/", depth=1)
    result2 = nc_any.files.listdir("test_root_folder/")
    assert result == result2
    assert len(result) == 3
    result = nc_any.files.listdir("test_root_folder/", depth=2)
    result2 = nc_any.files.listdir("test_root_folder/", depth=-1)
    assert result == result2
    assert len(result) == 6


def test_fs_node_fields(nc_any):
    nc_any.files.delete("test_root_folder", not_fail=True)
    nc_any.files.mkdir("test_root_folder")
    nc_any.files.upload("test_root_folder/5_bytes.txt", content="12345")
    nc_any.files.setfav("test_root_folder/5_bytes.txt", True)
    nc_any.files.upload("test_root_folder/0_bytes.bin", content="")
    nc_any.files.mkdir("test_root_folder/empty_child_folder")
    nc_any.files.mkdir("test_root_folder/child_folder")
    for i in range(10):
        nc_any.files.upload(f"test_root_folder/child_folder/{i}.txt", content=f"{i}")
    results = nc_any.files.listdir("test_root_folder")
    assert len(results) == 4
    for _, result in enumerate(results):
        assert result.user == "admin"
        if result.name == "0_bytes.bin":
            assert result.user_path == "test_root_folder/0_bytes.bin"
            assert not result.is_dir
            assert result.full_path == "files/admin/test_root_folder/0_bytes.bin"
            assert not result.info.size
            assert not result.info.content_length
            assert result.info.permissions == "RGDNVW"
            assert not result.info.favorite
        elif result.name == "5_bytes.txt":
            assert result.user_path == "test_root_folder/5_bytes.txt"
            assert not result.is_dir
            assert result.full_path == "files/admin/test_root_folder/5_bytes.txt"
            assert result.info.size == 5
            assert result.info.content_length == 5
            assert result.info.permissions == "RGDNVW"
            assert result.info.favorite
        elif result.name == "child_folder":
            assert result.user_path == "test_root_folder/child_folder/"
            assert result.is_dir
            assert result.full_path == "files/admin/test_root_folder/child_folder/"
            assert result.info.size == 10
            assert result.info.content_length == 0
            assert result.info.permissions == "RGDNVCK"
            assert not result.info.favorite
        elif result.name == "empty_child_folder":
            assert result.user_path == "test_root_folder/empty_child_folder/"
            assert result.is_dir
            assert result.full_path == "files/admin/test_root_folder/empty_child_folder/"
            assert result.info.size == 0
            assert result.info.content_length == 0
            assert result.info.permissions == "RGDNVCK"
            assert not result.info.favorite
        else:
            raise ValueError(f"Unknown value:{result.name}")
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
    nc_any.files.delete("abc", not_fail=True)
    result = nc_any.files.makedirs("abc/def")
    assert result.is_dir
    with pytest.raises(NextcloudException) as exc_info:
        nc_any.files.makedirs("abc/def")
    assert exc_info.value.status_code == 405
    result = nc_any.files.makedirs("abc/def", exist_ok=True)
    assert result is None
    nc_any.files.delete("abc")


def test_fs_node_str(nc_any):
    nc_any.files.makedirs("test_root_folder", exist_ok=True)
    nc_any.files.upload("test_file_name.txt", content=b"123")
    try:
        fs_node1 = nc_any.files.by_path("test_root_folder")
        fs_node2 = nc_any.files.by_path("test_file_name.txt")
        str_fs_node1 = str(fs_node1)
        assert str_fs_node1.find("Dir") != -1
        assert str_fs_node1.find("test_root_folder") != -1
        assert str_fs_node1.find(f"id={fs_node1.file_id}") != -1
        str_fs_node2 = str(fs_node2)
        assert str_fs_node2.find("File") != -1
        assert str_fs_node2.find("test_file_name.txt") != -1
        assert str_fs_node2.find(f"id={fs_node2.file_id}") != -1
    finally:
        nc_any.files.delete("test_root_folder")
        nc_any.files.delete("test_file_name.txt")


def test_download_as_zip(nc):
    nc.files.makedirs("test_root_folder/test_subfolder", exist_ok=True)
    try:
        nc.files.mkdir("test_root_folder/test_subfolder2")
        nc.files.upload("test_root_folder/0.txt", content="")
        nc.files.upload("test_root_folder/1.txt", content="123")
        nc.files.upload("test_root_folder/test_subfolder/0.txt", content="")
        old_headers = nc.response_headers
        result = nc.files.download_directory_as_zip("test_root_folder")
        assert nc.response_headers != old_headers
        try:
            with zipfile.ZipFile(result, "r") as zip_ref:
                assert zip_ref.filelist[0].filename == "test_root_folder/"
                assert not zip_ref.filelist[0].file_size
                assert zip_ref.filelist[1].filename == "test_root_folder/0.txt"
                assert not zip_ref.filelist[1].file_size
                assert zip_ref.filelist[2].filename == "test_root_folder/1.txt"
                assert zip_ref.filelist[2].file_size == 3
                assert zip_ref.filelist[3].filename == "test_root_folder/test_subfolder/"
                assert not zip_ref.filelist[3].file_size
                assert zip_ref.filelist[4].filename == "test_root_folder/test_subfolder/0.txt"
                assert not zip_ref.filelist[4].file_size
                assert zip_ref.filelist[5].filename == "test_root_folder/test_subfolder2/"
                assert not zip_ref.filelist[5].file_size
                assert len(zip_ref.filelist) == 6
        finally:
            os.remove(result)
        old_headers = nc.response_headers
        result = nc.files.download_directory_as_zip("test_root_folder/test_subfolder", "2.zip")
        assert nc.response_headers != old_headers
        try:
            assert str(result) == "2.zip"
            with zipfile.ZipFile(result, "r") as zip_ref:
                assert zip_ref.filelist[0].filename == "test_subfolder/"
                assert not zip_ref.filelist[0].file_size
                assert zip_ref.filelist[1].filename == "test_subfolder/0.txt"
                assert not zip_ref.filelist[1].file_size
                assert len(zip_ref.filelist) == 2
        finally:
            os.remove("2.zip")
        result = nc.files.download_directory_as_zip("test_root_folder/test_subfolder2", "empty_folder.zip")
        try:
            assert str(result) == "empty_folder.zip"
            with zipfile.ZipFile(result, "r") as zip_ref:
                assert zip_ref.filelist[0].filename == "test_subfolder2/"
                assert not zip_ref.filelist[0].file_size
                assert len(zip_ref.filelist) == 1
        finally:
            os.remove("empty_folder.zip")
    finally:
        nc.files.delete("test_root_folder")


def test_fs_node_is_xx(nc_any):
    nc_any.files.delete("test_root_folder", not_fail=True)
    nc_any.files.makedirs("test_root_folder", exist_ok=True)
    try:
        folder = nc_any.files.listdir("test_root_folder", exclude_self=False)[0]
        assert folder.is_dir
        assert folder.is_creatable
        assert folder.is_readable
        assert folder.is_deletable
        assert folder.is_shareable
        assert folder.is_updatable
        assert not folder.is_mounted
        assert not folder.is_shared
    finally:
        nc_any.files.delete("test_root_folder")


def test_fs_node_last_modified_time():
    fs_node = FsNode("", last_modified="wrong time")
    assert fs_node.info.last_modified == datetime(1970, 1, 1)
    fs_node = FsNode("", last_modified="Sat, 29 Jul 2023 11:56:31")
    assert fs_node.info.last_modified == datetime(2023, 7, 29, 11, 56, 31)
    fs_node = FsNode("", last_modified=datetime(2022, 4, 5, 1, 2, 3))
    assert fs_node.info.last_modified == datetime(2022, 4, 5, 1, 2, 3)


def test_trashbin(nc):
    r = nc.files.trashbin_list()
    assert isinstance(r, list)
    new_file = nc.files.upload("nc_py_api_temp.txt", content=b"")
    nc.files.delete(new_file)
    # minimum one object now in a trashbin
    r = nc.files.trashbin_list()
    assert r
    # clean up trashbin
    nc.files.trashbin_cleanup()
    # no objects should be in trashbin
    r = nc.files.trashbin_list()
    assert not r
    new_file = nc.files.upload("nc_py_api_temp.txt", content=b"")
    nc.files.delete(new_file)
    # one object now in a trashbin
    r = nc.files.trashbin_list()
    assert len(r) == 1
    # check types of FsNode properties
    i: FsNode = r[0]
    assert i.info.in_trash is True
    assert i.info.trashbin_filename.find("nc_py_api_temp.txt") != -1
    assert i.info.trashbin_original_location == "nc_py_api_temp.txt"
    assert isinstance(i.info.trashbin_deletion_time, int)
    # restore that object
    nc.files.trashbin_restore(r[0])
    # no files in trashbin
    r = nc.files.trashbin_list()
    assert not r
    # move a restored object to trashbin again
    nc.files.delete(new_file)
    # one object now in a trashbin
    r = nc.files.trashbin_list()
    assert len(r) == 1
    # remove one object from a trashbin
    nc.files.trashbin_delete(r[0])
    # NextcloudException with status_code 404
    with pytest.raises(NextcloudException) as e:
        nc.files.trashbin_delete(r[0])
    assert e.value.status_code == 404
    nc.files.trashbin_delete(r[0], not_fail=True)
    # no files in trashbin
    r = nc.files.trashbin_list()
    assert not r


def test_file_versions(nc):
    if nc.check_capabilities("files.versioning"):
        pytest.skip("Need 'Versions' App to be enabled.")
    for i in (0, 1):
        nc.files.delete("nc_py_api_file_versions_test.txt", not_fail=True)
        nc.files.upload("nc_py_api_file_versions_test.txt", content=b"22")
        new_file = nc.files.upload("nc_py_api_file_versions_test.txt", content=b"333")
        if i:
            new_file = nc.files.by_id(new_file)
        versions = nc.files.get_versions(new_file)
        assert versions
        nc.files.restore_version(versions[0])
        assert nc.files.download(new_file) == b"22"
        nc.files.delete(new_file)
