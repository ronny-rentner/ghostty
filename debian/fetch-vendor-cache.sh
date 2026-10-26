#!/bin/bash
# Fill vendor-zig-cache/ with Ghostty's Zig dependencies, which debian/rules builds from offline.
# Run from the source root with zig0.17 installed.
set -euo pipefail

export ZIG_GLOBAL_CACHE_DIR=$PWD/vendor-zig-cache

# zig 0.17's `zig fetch <url>` writes cache archives that `zig build` later rejects with a hash mismatch (the
# archive's root directory is kept); `zig build --fetch=all` fetches the whole dependency tree, writes correct
# archives and unpacks the working copies into the local package directory, which --system reads
ZIG_LOCAL_PKG_DIR=$ZIG_GLOBAL_CACHE_DIR/p zig0.17 build --fetch=all
