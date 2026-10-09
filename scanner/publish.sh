#!/bin/bash
set -e
R=/Users/ank/projects/image-reuse-tracker
P=$R/.venv/bin/python
if [ "$1" = "--photo" ]; then
  PHOTO="$2"; shift 2
  for u in "$@"; do $P $R/scanner/set_photo.py "$u" "$PHOTO"; done
else
  $P $R/scanner/add_pages.py "$@"
  $P $R/scanner/find_photos.py | tail -1
fi
$P $R/scanner/rebuild_csv.py > /dev/null
$P $R/scanner/build_thumbs.py | tail -1
$P $R/scanner/grab_thumbs.py | tail -1
$P $R/scanner/build_showcase.py | head -2
/usr/bin/git -C $R add -A
/usr/bin/git -C $R commit -q -m "Add pages" || true
/usr/bin/git -C $R push -q origin main
echo "Published. Live in about a minute: https://ank-kumar.github.io/ank-kumar-photo-contributions/"
