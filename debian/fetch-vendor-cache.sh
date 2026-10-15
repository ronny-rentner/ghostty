#!/bin/bash
# Fill vendor-zig-cache/ with Ghostty's Zig dependencies, which debian/rules builds from offline.
# Run from the source root with zig0.16 installed.
set -euo pipefail

export ZIG_GLOBAL_CACHE_DIR=$PWD/vendor-zig-cache

while IFS= read -r url; do
    case "$url" in
        # the build links these from Debian (zig build --system enables their system integration)
        */freetype-*|*/harfbuzz-*|*/fontconfig-*|*/libpng-*|*/zlib-*|*/libxml2-*|*/oniguruma-*|*/gtk4-layer-shell-*)
            continue ;;
    esac
    zig0.16 fetch "$url"
done < build.zig.zon.txt

# zig 0.16 keeps fetched packages as tarballs, but --system reads unpacked directories
cd "$ZIG_GLOBAL_CACHE_DIR/p"
for tarball in *.tar.gz; do
    tar -xzf "$tarball"
done
