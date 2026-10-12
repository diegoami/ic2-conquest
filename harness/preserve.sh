# Source me. Rule 6 helpers for harness/new_game.sh: nothing measured is overwritten or lost. Offline-tested by tests/test_new_game_sh_keeps_saves.py.

# supersede_autos <game folder>: move every AUTO* file into a genuinely new `superseded-<stamp>[-n]/` folder (mkdir without -p fails on an
# existing one, so a name is never reused), `mv -n` never replaces, and each file is checked to be in the new folder afterwards.
# Returns non-zero (and prints why) if anything could not be preserved; the caller must then not launch the game.
# preserve_ls <dir>: the directory listing used to decide whether there is anything to preserve. A function so a test can inject a failure
# (review round 4, R1/R3); a listing that fails is never read as "nothing to preserve".
preserve_ls() { ls -A -- "$1"; }

supersede_autos() {
  local g=$1 stamp n=0 d f listing
  [ -d "$g" ] || { echo "game folder $g is not a directory" >&2; return 1; }
  listing=$(preserve_ls "$g") || { echo "cannot list the game folder $g (permissions?): refusing to continue" >&2; return 1; }
  printf '%s\n' "$listing" | grep -q '^AUTO' || return 0   # listed successfully and no AUTO* file: nothing to preserve
  stamp=$(date +%Y%m%d-%H%M%S); d="$g/superseded-$stamp"
  until mkdir "$d" 2>/dev/null; do n=$((n+1)); d="$g/superseded-$stamp-$n"; [ $n -gt 999 ] && { echo "cannot allocate a superseded folder" >&2; return 1; }; done
  for f in "$g"/AUTO*; do
    [ -e "$f" ] || { echo "$f listed but cannot be accessed" >&2; return 1; }
    [ -f "$f" ] || continue
    mv -n "$f" "$d/" || { echo "cannot move $f aside" >&2; return 1; }
    [ -e "$f" ] || [ -e "$d/$(basename "$f")" ] || { echo "$f not found in $d" >&2; return 1; }
    [ ! -e "$f" ] || { echo "$f still in the game folder (not moved)" >&2; return 1; }
  done
}

# copy_out_unique <src glob dir> <out dir> <name>: copy the AUTO*.SAV files of the game folder to <out dir>/<name>; if that name exists,
# <name>.1, .2 ... (never replaces: cp -n plus an existence check). Prints the destination used.
copy_out_unique() {
  local g=$1 out=$2 name=$3 dest n=0
  mkdir -p "$out" || return 1
  dest="$out/$name"
  while [ -e "$dest" ]; do n=$((n+1)); dest="$out/$name.$n"; done
  cp -n "$g"/AUTO*.SAV "$dest" || return 1
  echo "$dest"
}
