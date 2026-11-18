from pathlib import Path
import hashlib
import shutil
import tarfile
from urllib.request import urlretrieve


def prepare():
    base = Path(__file__).resolve().parent
    root = base / "CUB_200_2011"
    archive = base / "CUB_200_2011.tgz"
    if (root / ".ready").exists():
        install_attributes(base, root)
        return
    if not archive.exists():
        print("CUB 새 사진 다운로드 중…")
        tmp = archive.with_suffix(".part")
        urlretrieve("https://huggingface.co/datasets/XiN0919/FGVC/resolve/main/CUB_200_2011.tgz", tmp)
        tmp.replace(archive)
    digest = hashlib.md5()
    with archive.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != "97eceeb196236b17998738112f37df78":
        raise ValueError("다운로드가 불완전합니다. CUB_200_2011.tgz 파일을 삭제하고 다시 실행하면 다운로드를 재시도합니다.")
    if not (root / ".ready").exists():
        with tarfile.open(archive, "r:gz") as tar:
            for member in tar:
                path = Path(member.name)
                if not member.isfile() or path.is_absolute() or ".." in path.parts:
                    continue
                if not path.parts or path.parts[0] != root.name:
                    continue
                path = base / path
                path.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as src, path.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
        (root / ".ready").touch()
    install_attributes(base, root)


def install_attributes(base, root):
    source = base / "data/cub_attributes.txt"
    target = root / "attributes/attributes.txt"
    content = source.read_bytes()
    if target.exists() and target.read_bytes() == content:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".part")
    temp.write_bytes(content)
    temp.replace(target)


if __name__ == "__main__":
    prepare()
    print("데이터 준비 완료")
