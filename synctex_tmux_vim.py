#!/Users/diss/Diss/venv/bin/python
"""Jump to a position in a .tex file that is open in vim in a tmux window."""

__version__ = 1.0.0
__author__ = "Michael Goerz <mail@michaelgoerz.net>"

import subprocess
import os
import sys
import psutil
import logging


def find_vim(filename, tmux_exec):
    """
    Return tuple (session, window_index) of the tmux window that runs
    'vim [filename]'
    """
    logger = logging.getLogger(__name__)
    tmux_pids = tmux_processes(tmux_exec)
    for (session_name, window_index, pid) in tmux_pids:
        logger.debug("Examining tmux sessions %s, windows %d",
                      session_name, window_index)
        if check_process(pid, filename):
            logger.debug("Found vim instance editing %s "
                         +"running in window %d of tmux session %s",
                         filename, window_index, session_name)
            return (session_name, window_index)
    return None


def check_process(pid, filename):
    """
    Return True if the process with pid has a subprocess 'vim [filename]',
    with the given filename
    """
    logger = logging.getLogger(__name__)
    filename = os.path.abspath(filename)
    p = psutil.Process(pid)
    cwd = p.cwd()
    cmd = p.cmdline()
    if cmd[0] == 'vim':
        open_file = os.path.abspath(os.path.join(cwd, cmd[-1]))
        if open_file == filename:
            logger.debug("Process %d is running vim, with correct filename %s",
                         pid, open_file)
            return True
        else:
            logger.debug("Process %d is running vim, but with filename %s",
                         pid, open_file)
    else:
        logger.debug("Process %d is not running vim", pid)
        for child_pid in p.get_children():
            result = check_process(child_pid.pid, filename)
            if result:
                return result
        return False


def jump_to(tmux_exec, session_name, window_index, line_nr):
    """
    Given a tmux session name and window index, assume that that window is
    running vim. Send keystrokes to tmux that cause the vim to jump to the
    given line number.
    """
    logger = logging.getLogger(__name__)

    cmd1 = [tmux_exec, 'select-window',
            '-t', "%s:%d" % (session_name, window_index)]
    logger.debug("Running command '%s'", " ".join(cmd1))
    ret1 = subprocess.call(cmd1)
    logger.debug("subprocess returned with code %d", ret1)

    cmd2 = [tmux_exec, 'send-keys',
            '-t', "%s:%d" % (session_name, window_index),
            "Escape", "Escape", str(line_nr),  "gg", "zz"]
    logger.debug("Running command '%s'", " ".join(cmd2))
    ret2 = subprocess.call(cmd2)
    logger.debug("subprocess returned with code %d", ret2)


def tmux_processes(tmux_exec):
    """
    Return a list of tuples (session_name, window_index, pid) for processes
    running in tmux sessions
    """
    logger = logging.getLogger(__name__)
    result = []
    tmux_data = subprocess.check_output([tmux_exec, 'list-windows', '-F',
                '#{session_name}:#{window_index}:#{pane_pid}', '-a'])
    for line in tmux_data.splitlines():
        session_name, window_index, pid = line.split(":")
        result.append((session_name, int(window_index), int(pid)))
    logger.debug("Detected tmux windows %s", str(result))
    return result


def main(argv=None):
    """Main function"""
    from optparse import OptionParser
    if argv is None:
        argv = sys.argv
    arg_parser = OptionParser(
    usage = "usage: %prog [options] <LINE_NR> <TEXFILE>",
    description = __doc__)
    arg_parser.add_option(
        '--log', action='store', dest='logfile',
        help="Write logging information to the given file")
    arg_parser.add_option(
        '--tmux', action='store', dest='tmux', default='tmux',
        help="Full path to the tmux executable")
    options, args = arg_parser.parse_args(argv)
    if len(args) != 3:
        arg_parser.error("incorrect number of arguments")
    try:
        line_nr  = int(args[1])
    except ValueError:
        arg_parser.error("invalid LINE_NR: %s" % args[1])
    filename = args[2]
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    console_log = logging.StreamHandler()
    console_log.setLevel(logging.ERROR)
    logger.addHandler(console_log)
    if options.logfile:
        logh = logging.FileHandler(options.logfile,"a")
        logh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logh.setFormatter(formatter)
        logger.addHandler(logh)
    try:
        logger.debug("START with LINE_NR=%d, TEXFILE=%s", line_nr, filename)
        tmux_target = find_vim(filename, options.tmux)
        if tmux_target is not None:
            session_name, window_index = tmux_target
            jump_to(options.tmux, session_name, window_index, line_nr)
        else:
            logger.warn('Could not find tmux window with vim editing %s',
                        filename)
    except Exception, e:
        logger.error('Could not jump to intended target', exc_info=True)
    logger.debug("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
