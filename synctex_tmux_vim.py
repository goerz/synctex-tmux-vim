#!/usr/bin/env python
"""Jump to a position in a .tex file that is open in vim in a tmux pane."""

__version__ = '1.0.1'
__author__ = "Michael Goerz <mail@michaelgoerz.net>"

import subprocess
import os
import sys
import psutil
import logging


def find_vim(filename, tmux_exec):
    """
    Return tuple (session, window_index, pane_id) of the tmux pane that runs
    'vim [filename]'
    """
    logger = logging.getLogger(__name__)
    tmux_pids = tmux_processes(tmux_exec)
    for (session_name, window_index, pane_id, pid) in tmux_pids:
        logger.debug("Examining tmux sessions %s, windows %d",
                      session_name, window_index)
        if check_process(pid, filename):
            logger.debug("Found vim instance editing %s "
                         +"running in window %d of tmux session %s, "
                         +"in pane %s",
                         filename, window_index, session_name, pane_id)
            return (session_name, window_index, pane_id)
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
    if cmd[0] in ['vim', 'nvim']:
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
        try:
            children = p.get_children()
        except AttributeError:
            children = p.children()
        for child_pid in children:
            result = check_process(child_pid.pid, filename)
            if result:
                return result
        return False


def jump_to(tmux_exec, session_name, window_index, pane_id, line_nr):
    """
    Given a tmux session name, a window index, and a pane id, assume that that
    pane is running vim. Send keystrokes to tmux that cause the vim to jump to
    the given line number.
    """
    logger = logging.getLogger(__name__)

    cmd = [tmux_exec, 'select-window',
            '-t', "%s:%d" % (session_name, window_index)]
    logger.debug("Running command '%s'", " ".join(cmd))
    ret = subprocess.call(cmd)
    logger.debug("subprocess returned with code %d", ret)

    cmd = [tmux_exec, 'select-pane',
            '-t', "%s" % pane_id]
    logger.debug("Running command '%s'", " ".join(cmd))
    ret = subprocess.call(cmd)
    logger.debug("subprocess returned with code %d", ret)

    cmd = [tmux_exec, 'send-keys',
            '-t', "%s:%d" % (session_name, window_index),
            "Escape", "Escape", str(line_nr),  "gg", "zz"]
    logger.debug("Running command '%s'", " ".join(cmd))
    ret = subprocess.call(cmd)
    logger.debug("subprocess returned with code %d", ret)


def tmux_processes(tmux_exec):
    """
    Return a list of tuples (session_name, window_index, pane_id, pid) for
    processes running in tmux sessions
    """
    logger = logging.getLogger(__name__)
    result = []
    tmux_data = subprocess.check_output([tmux_exec, 'list-panes', '-F',
                '#{session_name}:#{window_index}:#{pane_id}:#{pane_pid}',
                '-a'], universal_newlines=True)
    for line in tmux_data.splitlines():
        session_name, window_index, pane_id, pid = line.split(":")
        result.append((session_name, int(window_index), pane_id, int(pid)))
    logger.debug("Detected tmux panes %s", str(result))
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
            session_name, window_index, pane_id = tmux_target
            jump_to(options.tmux, session_name, window_index, pane_id, line_nr)
        else:
            logger.warn('Could not find tmux pane with vim editing %s',
                        filename)
    except Exception:
        logger.error('Could not jump to intended target', exc_info=True)
    logger.debug("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
