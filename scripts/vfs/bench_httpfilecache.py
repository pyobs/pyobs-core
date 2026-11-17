"""Benchmark image transfers through an HttpFileCache via the pyobs VFS.

See docs/source/recipes/httpfilecache.rst for how to read the results.

Start a cache on one machine:

    python bench_httpfilecache.py serve 37099

and run the client on another one (or the same one):

    python bench_httpfilecache.py client http://server:37099/ 5

The client uploads and downloads a synthetic 6248x4176 uint16 frame (about 52 MB), both as raw
bytes and via write_image/read_image, and prints median and minimum times. Use a port that is
not used by a production cache.
"""

import argparse
import asyncio
import io
import logging
import statistics
import time
from typing import Any

import numpy as np


async def serve(port: int) -> None:
    from pyobs.modules.utils import HttpFileCache

    cache = HttpFileCache(port=port, cache_size=5, max_file_size=200)
    await cache.open()
    print(f"Serving on port {port}, stop with Ctrl+C.", flush=True)
    try:
        await asyncio.Event().wait()
    finally:
        await cache.close()


def print_stats(name: str, times: list[float], nbytes: int) -> None:
    med = statistics.median(times)
    print(f"{name:30s} median {med * 1000:6.0f} ms  min {min(times) * 1000:6.0f} ms  ({nbytes / med / 1e6:5.0f} MB/s)")


async def client(url: str, runs: int, width: int, height: int) -> None:
    from pyobs.images import Image
    from pyobs.vfs import VirtualFileSystem

    vfs = VirtualFileSystem(
        roots={"cache": {"class": "pyobs.vfs.HttpFile", "download": url, "upload": url, "timeout": 120}}
    )

    # synthetic uint16 frame like a camera delivers it, noise around a bias level
    # (Image is annotated for float data only, but cameras pass integer data as well)
    rng = np.random.default_rng(1)
    data: Any = rng.normal(500, 6, (height, width)).astype(np.uint16)
    img = Image(data)
    with io.BytesIO() as bio:
        img.writeto(bio)
        raw = bio.getvalue()
    nbytes = len(raw)
    print(f"URL {url}, {nbytes / 1e6:.1f} MB, {runs} runs")

    keys = [
        "upload bytes",
        "download bytes",
        "serialize Image->FITS",
        "parse FITS->Image",
        "write_image (ser+upload)",
        "read_image (down+parse)",
    ]
    t: dict[str, list[float]] = {k: [] for k in keys}
    for i in range(runs):
        s = time.perf_counter()
        await vfs.write_bytes(f"/cache/bytes{i}.fits", raw)
        t[keys[0]].append(time.perf_counter() - s)

        s = time.perf_counter()
        async with vfs.open_file(f"/cache/bytes{i}.fits", "rb") as f:
            data = await f.read()
        t[keys[1]].append(time.perf_counter() - s)
        if data != raw:
            raise RuntimeError("Downloaded data differs from uploaded data.")

        s = time.perf_counter()
        with io.BytesIO() as bio:
            img.writeto(bio)
            bio.getvalue()
        t[keys[2]].append(time.perf_counter() - s)

        s = time.perf_counter()
        Image.from_bytes(raw)
        t[keys[3]].append(time.perf_counter() - s)

        s = time.perf_counter()
        await vfs.write_image(f"/cache/image{i}.fits", img)
        t[keys[4]].append(time.perf_counter() - s)

        s = time.perf_counter()
        await vfs.read_image(f"/cache/image{i}.fits")
        t[keys[5]].append(time.perf_counter() - s)

    for k in keys:
        print_stats(k, t[k], nbytes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="mode", required=True)
    p_serve = sub.add_parser("serve", help="run an HttpFileCache")
    p_serve.add_argument("port", type=int)
    p_client = sub.add_parser("client", help="upload/download a synthetic frame")
    p_client.add_argument("url", help="URL of the cache, e.g. http://server:37099/")
    p_client.add_argument("runs", type=int, nargs="?", default=5)
    p_client.add_argument("--width", type=int, default=6248)
    p_client.add_argument("--height", type=int, default=4176)
    args = parser.parse_args()

    # the cache logs every stored/served file
    logging.disable(logging.INFO)

    try:
        if args.mode == "serve":
            asyncio.run(serve(args.port))
        else:
            asyncio.run(client(args.url, args.runs, args.width, args.height))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
