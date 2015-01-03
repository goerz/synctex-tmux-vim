synctex-tmux-vim
================

Simple python script that takes a line number and the full path of a text file,
and searches through all tmux sessions for a window running the command
`vim <filename>`. It then sends keystrokes to the tmux session to switch to that
window, and instructs vim to jump to the given line number.

    Usage: synctex_tmux_vim.py [options] <LINE_NR> <TEXFILE>
    
    Jump to a position in a .tex file that is open in vim in a tmux window.
    
    Options:
      -h, --help     show this help message and exit
      --log=LOGFILE  Write logging information to the given file
      --tmux=TMUX    Full path to the tmux executable

The script doesn't try to be overly smart, it just sends keystrokes to vim,

    ESC ESC <line>gg zz

which will hopefully put the line at the center of the screen. It only looks at
the command that was used to start the vim session. If that command ends with
the target file name, it assumes that vim is currently editing that file. If you
opened multiple tabs, splits, buffer, etc., it may do the wrong thing.

Installation
============

The script is intended to be called from a PDF viewer that support [SyncTeX][]
It has been tested with [Skim][].
In Skim, go to Settings > Sync, and in PDF-TeX Sync support, select Preset
"Custom", set the command to point to the full path of the script, and the
arguments to

    %line "%file"

Other viewers should have similar options. If something is wrong, you can get
debug information by setting a log file, e.g.,

    --log=/home/myuser/synctex.log %line "%file"

Specifically, if the tmux executable is not in the PATH that the viewer passes
to this script, you can give the full path as an option,

    --tmux=/usr/local/bin/tmux %line "%file"


Dependencies
============

The script depends on the [psutil][] package.

[SyncTeX]: http://www.tug.org/TUGboat/tb29-3/tb93laurens.pdf
[Skim]: http://skim-app.sourceforge.net
[psutil]: https://pypi.python.org/pypi/psutil
