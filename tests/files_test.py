from io import BytesIO
from random import randbytes, choice
from string import ascii_lowercase
from zlib import adler32
import math

import pytest

from PIL import Image
from nc_py_api import NextcloudException

from gfixture import NC_TO_TEST


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


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_list_root(nc):
    files_root = nc.files.listdir(root=True)
    assert files_root
    for obj in files_root:
        assert not obj.user
        assert obj.full_path == obj.path


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_list_user_root(nc):
    user_root = nc.files.listdir()
    assert user_root
    for obj in user_root:
        assert obj.user
        assert obj.info["nc_id"]
        assert obj.info["fileid"]


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_file_download(nc):
    content = randbytes(64)
    nc.files.upload("test_file.txt", content=content)
    srv_admin_manual1 = nc.files.download("test_file.txt")
    srv_admin_manual2 = nc.files.download("/test_file.txt")
    assert srv_admin_manual1 == srv_admin_manual2
    assert srv_admin_manual1 == content


@pytest.mark.parametrize("nc", NC_TO_TEST)
@pytest.mark.parametrize("data_type", ("str", "bytes"))
@pytest.mark.parametrize("chunk_size", (15, 32, 64, None))
def test_file_download2stream(nc, data_type, chunk_size):
    srv_admin_manual_buf = MyBytesIO()
    if data_type == "str":
        content = ''.join(choice(ascii_lowercase) for i in range(64))
    else:
        content = randbytes(64)
    nc.files.upload("test_file.txt", content=content)
    if chunk_size is not None:
        nc.files.download2stream("/test_file.txt", srv_admin_manual_buf, chunk_size=chunk_size)
    else:
        nc.files.download2stream("/test_file.txt", srv_admin_manual_buf)
    assert nc.files.download("test_file.txt") == srv_admin_manual_buf.getbuffer()
    if chunk_size is None:
        assert srv_admin_manual_buf.n_write_calls == 1
    else:
        assert srv_admin_manual_buf.n_write_calls == math.ceil(64 / chunk_size)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_file_download_not_found(nc):
    with pytest.raises(NextcloudException):
        nc.files.download("file that does not exist on the server")
    with pytest.raises(NextcloudException):
        nc.files.listdir("non existing path")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_file_download2stream_not_found(nc):
    buf = BytesIO()
    with pytest.raises(NextcloudException):
        nc.files.download2stream("file that does not exist on the server", buf)
    with pytest.raises(NextcloudException):
        nc.files.download2stream("non existing path", buf)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_file_upload(nc):
    file_name = "12345.txt"
    nc.files.upload(file_name, content=b'\x31\x32')
    assert nc.files.download(file_name) == b'\x31\x32'
    nc.files.upload(f"/{file_name}", content=b'\x31\x32\x33')
    assert nc.files.download(file_name) == b'\x31\x32\x33'
    nc.files.upload(file_name, content="life is good")
    assert nc.files.download(file_name).decode("utf-8") == "life is good"


@pytest.mark.parametrize("nc", NC_TO_TEST)
@pytest.mark.parametrize("chunk_size", (63, 64, 65, None))
def test_file_upload_chunked(nc, chunk_size):
    file_name = "chunked.bin"
    buf_upload = MyBytesIO()
    random_bytes = randbytes(64)
    buf_upload.write(random_bytes)
    buf_upload.seek(0)
    if chunk_size is None:
        nc.files.upload_stream(file_name, fp=buf_upload)
    else:
        nc.files.upload_stream(file_name, fp=buf_upload, chunk_size=chunk_size)
    if chunk_size is None:
        assert buf_upload.n_read_calls == 2
    else:
        assert buf_upload.n_read_calls == 1 + math.ceil(64 / chunk_size)
    buf_download = BytesIO()
    nc.files.download2stream(file_name, fp=buf_download)
    buf_upload.seek(0)
    buf_download.seek(0)
    upload_crc = adler32(buf_upload.read())
    download_crc = adler32(buf_download.read())
    assert upload_crc == download_crc


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_file_upload_chunked_zero_size(nc):
    file_name = "chunked_zero.bin"
    buf_upload = MyBytesIO()
    nc.files.upload_stream(file_name, fp=buf_upload)
    assert nc.files.download(file_name) == b""


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_file_upload_empty(nc):
    nc.files.upload("12345.txt", content="")
    assert not nc.files.download("12345.txt")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_file_delete(nc):
    file_name = "12345.txt"
    nc.files.upload(file_name, content="")
    nc.files.delete(file_name)
    with pytest.raises(NextcloudException):
        nc.files.delete(file_name)
    nc.files.delete(file_name, not_fail=True)


@pytest.mark.parametrize("nc", NC_TO_TEST)
@pytest.mark.parametrize("dir_name", ("1 2", "Яё", "відео та картинки", "复杂 目录 Í", "Björn", "João"))
def test_mkdir(nc, dir_name):
    nc.files.mkdir(dir_name)
    with pytest.raises(NextcloudException):
        nc.files.mkdir(dir_name)
    nc.files.delete(dir_name)
    with pytest.raises(NextcloudException):
        nc.files.delete(dir_name)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_no_favorites(nc):
    favorites = nc.files.listfav()
    for favorite in favorites:
        nc.files.setfav(favorite.path, False)
    assert not nc.files.listfav()


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_favorites(nc):
    favorites = nc.files.listfav()
    for favorite in favorites:
        nc.files.setfav(favorite.path, False)
    files = ("fav1.txt", "fav2.txt", "fav3.txt")
    for n in files:
        nc.files.upload(n, content=n)
        nc.files.setfav(n, True)
    assert len(nc.files.listfav()) == 3
    for n in files:
        nc.files.delete(n)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_copy_file(nc):
    src = "test_file.txt"
    dest = "nc_admin_man_999.pdf"
    nc.files.upload(src, content=randbytes(64))
    nc.files.copy(src, dest)
    assert nc.files.download(src) == nc.files.download(dest)
    with pytest.raises(NextcloudException):
        nc.files.copy(src, dest)
    nc.files.copy(src, dest, overwrite=True)
    nc.files.delete(dest)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_move_file(nc):
    src = "src move test file"
    dest = "dest move test file"
    content = b"content of the file"
    content2 = b"content of the file-second part"
    nc.files.upload(src, content=content)
    nc.files.move(src, dest)
    assert nc.files.download(dest) == content
    with pytest.raises(NextcloudException):
        nc.files.download(src)
    nc.files.upload(src, content=content2)
    with pytest.raises(NextcloudException):
        nc.files.move(src, dest)
    nc.files.move(src, dest, overwrite=True)
    with pytest.raises(NextcloudException):
        nc.files.download(src)
    assert nc.files.download(dest) == content2
    nc.files.delete(dest)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_move_dir(nc):
    dir_name = "test_dir"
    dest_dir_name = f"{dir_name} dest"
    nc.files.delete(dir_name, not_fail=True)
    nc.files.delete(dest_dir_name, not_fail=True)
    nc.files.mkdir(dir_name)
    files = ("file1.txt", "file2.txt", "file3.txt")
    for n in files:
        nc.files.upload(f"{dir_name}/{n}", content=n)
    nc.files.move(dir_name, dest_dir_name)
    assert len(nc.files.listdir(dest_dir_name)) == 3
    with pytest.raises(NextcloudException):
        nc.files.delete(dir_name)
    nc.files.delete(dest_dir_name)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_find_files(nc):
    nc.files.delete("test_root_folder", not_fail=True)
    im1 = BytesIO()
    im2 = BytesIO()
    im3 = BytesIO()
    Image.linear_gradient("L").resize((768, 768)).save(im1, format="PNG")
    Image.linear_gradient("L").resize((1024, 1024)).save(im2, format="GIF")
    Image.linear_gradient("L").resize((8192, 8192)).save(im3, format="JPEG")
    for i in (im1, im2, im3):
        i.seek(0)
    nc.files.mkdir("test_root_folder")
    nc.files.mkdir("test_root_folder/child_folder")
    nc.files.upload("test_root_folder/image1.png", content=im1.read())
    nc.files.upload("test_root_folder/test_root.txt", content="content!")
    nc.files.upload("test_root_folder/child_folder/image2.gif", content=im2.read())
    nc.files.upload("test_root_folder/child_folder/image3.jpg", content=im3.read())
    nc.files.upload("test_root_folder/child_folder/test.txt", content="content!")
    result = nc.files.find(["and", "gt", "size", 1 * 1024, "like", "mime", "image/%"], path="test_root_folder")
    assert len(result) == 3
    result = nc.files.find(["and", "gt", "size", 40 * 1024, "like", "mime", "image/%"], path="test_root_folder")
    assert len(result) == 2
    result = nc.files.find(["and", "gt", "size", 100 * 1024, "like", "mime", "image/%"], path="test_root_folder")
    assert len(result) == 1
    result = nc.files.find(["and", "gt", "size", 1024 * 1024, "like", "mime", "image/%"], path="test_root_folder")
    assert len(result) == 0
    result = nc.files.find(["gte", "size", 0], path="test_root_folder")
    assert len(result) == 6  # 1 sub dir + 3 images + 2 text files
    result = nc.files.find(["like", "mime", "text/%"], path="test_root_folder")
    assert len(result) == 2


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_fs_node_fields(nc):
    nc.files.delete("test_root_folder", not_fail=True)
    nc.files.mkdir("test_root_folder")
    nc.files.upload("test_root_folder/5_bytes.txt", content="12345")
    nc.files.setfav("test_root_folder/5_bytes.txt", True)
    nc.files.upload("test_root_folder/0_bytes.bin", content="")
    nc.files.mkdir("test_root_folder/empty_child_folder")
    nc.files.mkdir("test_root_folder/child_folder")
    for i in range(10):
        nc.files.upload(f"test_root_folder/child_folder/{i}.txt", content=f"{i}")
    results = nc.files.listdir("test_root_folder")
    assert len(results) == 4
    for i, result in enumerate(results):
        assert result.user == "admin"
        if result.name == "0_bytes.bin":
            assert result.path == 'test_root_folder/0_bytes.bin'
            assert not result.is_dir
            assert result.full_path == 'admin/test_root_folder/0_bytes.bin'
            assert not result.info["size"]
            assert not result.info["content_length"]
            assert result.info["permissions"] == "RGDNVW"
            assert not result.info["favorite"]
        elif result.name == "5_bytes.txt":
            assert result.path == 'test_root_folder/5_bytes.txt'
            assert not result.is_dir
            assert result.full_path == 'admin/test_root_folder/5_bytes.txt'
            assert result.info["size"] == 5
            assert result.info["content_length"] == 5
            assert result.info["permissions"] == "RGDNVW"
            assert result.info["favorite"]
        elif result.name == "child_folder":
            assert result.path == 'test_root_folder/child_folder/'
            assert result.is_dir
            assert result.full_path == 'admin/test_root_folder/child_folder/'
            assert result.info["size"] == 10
            assert result.info["content_length"] == 0
            assert result.info["permissions"] == "RGDNVCK"
            assert not result.info["favorite"]
        elif result.name == "empty_child_folder":
            assert result.path == 'test_root_folder/empty_child_folder/'
            assert result.is_dir
            assert result.full_path == 'admin/test_root_folder/empty_child_folder/'
            assert result.info["size"] == 0
            assert result.info["content_length"] == 0
            assert result.info["permissions"] == "RGDNVCK"
            assert not result.info["favorite"]
        else:
            raise ValueError(f"Unknown value:{result.name}")
        res_by_id = nc.files.by_id(result.info["fileid"])
        assert res_by_id
        res_by_path = nc.files.by_path(result.path)
        assert res_by_path
        assert res_by_id.info == res_by_path.info == result.info
        assert res_by_id.full_path == res_by_path.full_path == result.full_path
        assert res_by_id.user == res_by_path.user == result.user
        assert res_by_id.last_modified == res_by_path.last_modified == result.last_modified


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_makedirs(nc):
    try:
        nc.files.delete("abc")
    except NextcloudException:
        pass
    nc.files.makedirs("abc/def")
    with pytest.raises(NextcloudException) as exc_info:
        nc.files.makedirs("abc/def")
    assert exc_info.value.status_code == 405
    nc.files.makedirs("abc/def", exist_ok=True)
    nc.files.delete("abc")
