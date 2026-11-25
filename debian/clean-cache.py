#!/usr/bin/env python3
"""Trace the Debian build and remove unused compiled cache outputs."""

import os
import re
import shutil
import subprocess
from contextlib import ExitStack
from pathlib import Path


CACHE_NAMES = ("zig-local-cache", "zig-global-cache")
OUTPUT_PATH = re.compile(r'(zig-(?:local|global)-cache)/o/([0-9a-f]+)(?=[/\s"<>]|$)')
DIRECTORY_ARGUMENT = re.compile(r'(?:[0-9]+|AT_FDCWD)<([^>]+)>, "([^"]*)"')


def used_outputs(trace):
    used = {name: set() for name in CACHE_NAMES}
    with trace.open() as lines:
        for line in lines:
            for name, digest in OUTPUT_PATH.findall(line):
                used[name].add(digest)
            # openat and related calls can pass paths relative to directory descriptors.
            for directory, path in DIRECTORY_ARGUMENT.findall(line):
                for name, digest in OUTPUT_PATH.findall(os.path.normpath(os.path.join(directory, path))):
                    used[name].add(digest)
    if any(not entries for entries in used.values()):
        raise RuntimeError("Trace did not identify outputs in both caches; nothing pruned")
    return used


def prune_outputs(build, used):
    removed = 0
    for name in CACHE_NAMES:
        for entry in (build / name / "o").iterdir():
            if entry.name not in used[name]:
                shutil.rmtree(entry)
                removed += 1
    return removed


def main():
    os.chdir(Path(__file__).resolve().parent.parent)
    build = Path("build")
    if not all((build / name / "o").is_dir() for name in CACHE_NAMES):
        raise SystemExit("Build Ghostty before cleaning its cache")
    if shutil.which("strace") is None:
        raise SystemExit("Install the strace package before cleaning the cache")

    trace = build / "cache-access.trace"
    with ExitStack() as cleanup:
        cleanup.callback(trace.unlink, missing_ok=True)
        cleanup.callback(subprocess.run, ["dpkg-source", "--after-build", "."], check=True)
        cleanup.callback(subprocess.run, ["debian/rules", "clean"], check=True)
        subprocess.run(["dpkg-source", "--before-build", "."], check=True)
        subprocess.run(["dh_prep"], check=True)
        subprocess.run([
            "strace", "-f", "-yy", "-s", "4096", "-e", "trace=%file", "-o", str(trace),
            "debian/rules", "override_dh_auto_install",
        ], check=True)
        removed = prune_outputs(build, used_outputs(trace))
        print(f"Removed {removed} unused cache output directories", flush=True)
        subprocess.run(["du", "-sh", *(str(build / name) for name in CACHE_NAMES)], check=True)


if __name__ == "__main__":
    main()
