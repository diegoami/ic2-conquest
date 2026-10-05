#!/bin/bash
# compact function dump: drop Ghidra variable declaration noise
python3 "$(dirname "$0")/fn.py" "$@" | grep -vP '^\d+\t\s+(undefined\d?|int|short|uint|char|byte|ushort|bool|undefined \*|int \*)\s+\**\w+(, ?\w+)*;$' | grep -vP '^\d+\t\s*$' | cut -c1-200
