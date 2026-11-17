#!/bin/bash
# Download Ghostty's dependencies into the sibling Zig checkout for offline builds.
# Run from the source root with zig0.17 installed.
set -euo pipefail

zig_root=$(realpath ../zig)
export ZIG_GLOBAL_CACHE_DIR=$zig_root/build/fetch-cache
export ZIG_LOCAL_CACHE_DIR=$PWD/build/zig-local-cache
export ZIG_LOCAL_PKG_DIR=$zig_root/cache/packages

# zig 0.17's `zig fetch <url>` writes cache archives that `zig build` later rejects with a hash mismatch (the
# archive's root directory is kept); `zig build --fetch=all` fetches the whole dependency tree, writes correct
# archives and unpacks the working copies into the local package directory, which --system reads
zig0.17 build --fetch=all
