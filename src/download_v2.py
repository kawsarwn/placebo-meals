"""Fetch the v2 data into data/.

    python src/download_v2.py

Both datasets come as large archives that are mostly files v2 doesn't need (raw waveforms, meal photos),
so this reads only the needed files out of them with HTTP range requests: D1NAMO's per-second chest strap
summaries and food, glucose and annotation logs, and CGMacros's CSVs. zipfile checks each file's CRC-32 as
it reads it.
"""

import http.client
import io
import threading
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ZENODO = "https://zenodo.org/api/records/5651217/files/{}/content"  # D1NAMO v1.2.0
SENSOR_ZIP = ZENODO.format("healthy_subset_sensor_data.zip")
LOG_ZIP = ZENODO.format("healthy_subset_pictures-glucose-food.zip")
# PhysioNet's AWS mirror of CGMacros v1.0.0, much faster than physionet.org
CGMACROS_ZIP = "https://physionet-open.s3.amazonaws.com/cgmacros/1.0.0/CGMacros_dateshifted365.zip"


def fetch(request, attempts=6):
    # Zenodo drops connections now and then, and answers 429 when asked too often
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=120) as r:
                r.body = r.read()
                return r
        except (http.client.IncompleteRead, urllib.error.URLError, TimeoutError):
            if attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)


class RemoteFile(io.RawIOBase):
    """A seekable read-only view of a remote file, fetched with HTTP range requests."""

    def __init__(self, url):
        r = fetch(urllib.request.Request(url, method="HEAD"))
        self.url, self.size = r.url, int(r.headers["Content-Length"])
        self.pos = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = {0: offset, 1: self.pos + offset, 2: self.size + offset}[whence]
        return self.pos

    def readinto(self, buffer):
        if self.pos >= self.size or len(buffer) == 0:
            return 0
        end = min(self.pos + len(buffer), self.size) - 1
        data = fetch(urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end}"})).body
        buffer[: len(data)] = data
        self.pos += len(data)
        return len(data)


def remote_zip(url):
    # a 1 MB buffer keeps requests few without fetching much past each file
    return zipfile.ZipFile(io.BufferedReader(RemoteFile(url), buffer_size=1 << 20))


def extract(archive, members, dest_root):
    todo = [m for m in members if not (dest_root / m).exists()]
    local = threading.local()

    def one(member):
        if not hasattr(local, "zip"):  # one open archive per worker keeps the request count down
            local.zip = remote_zip(archive)
        data = local.zip.read(member)  # raises BadZipFile on a CRC mismatch
        dest = dest_root / member
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.with_name(dest.name + ".part").write_bytes(data)
        dest.with_name(dest.name + ".part").rename(dest)
        print(f"got  {member}", flush=True)

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(one, todo))
    print(f"{archive}: {len(members) - len(todo)} already here, {len(todo)} fetched", flush=True)


def main():
    from d1namo import PARTICIPANTS

    with remote_zip(SENSOR_ZIP) as z:
        summaries = [n for n in z.namelist()
                     if n.endswith("_Summary.csv") and n.split("/")[1] in PARTICIPANTS]
    logs = [f"healthy_subset_pictures-glucose-food/{pid}/{name}.csv"
            for pid in PARTICIPANTS for name in ("food", "glucose", "annotations")]
    extract(SENSOR_ZIP, summaries, DATA_DIR / "d1namo")
    extract(LOG_ZIP, logs, DATA_DIR / "d1namo")
    with remote_zip(CGMACROS_ZIP) as z:
        tables = [n for n in z.namelist() if n.lower().endswith(".csv")]
    extract(CGMACROS_ZIP, tables, DATA_DIR / "cgmacros")


if __name__ == "__main__":
    main()
