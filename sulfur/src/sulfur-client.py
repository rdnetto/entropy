#!/usr/bin/python2 -O
# -*- coding: utf-8 -*-
"""

    @author: Fabio Erculiani <lxnay@sabayon.org>
    @contact: lxnay@sabayon.org
    @copyright: Fabio Erculiani
    @license: GPL-2

    B{Entropy Package Manager Graphical Client}.

"""
import os
import sys
import signal

import gtk
import gobject

sys.path.insert(0, "../../libraries")
sys.path.insert(1, "../../client")
sys.path.insert(2, "./")
sys.path.insert(3, "/usr/lib/entropy/libraries")
sys.path.insert(4, "/usr/lib/entropy/client")
sys.path.insert(5, "/usr/lib/entropy/sulfur")
import entropy.tools
from sulfur import SulfurApplication
from sulfur.dialogs import ExceptionDialog
from sulfur.setup import const

MAIN_APP = None

def kill_pid(pid):
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass

def kill_threads():
    entropy.tools.kill_threads()
    if MAIN_APP is not None:
        try:
            for pid in MAIN_APP._fork_pids:
                kill_pid(pid)
        except AttributeError:
            pass
        try:
            if MAIN_APP._ugc_pid is not None:
                kill_pid(MAIN_APP._ugc_pid)
        except AttributeError:
            pass

def handle_exception(exc_class, exc_instance, exc_tb):

    # restore original exception handler, to avoid loops
    uninstall_exception_handler()

    if exc_class is KeyboardInterrupt:
        kill_threads()
        print("Quit by User (KeyboardInterrupt)")
        if MAIN_APP is not None:
            MAIN_APP.quit()
        raise SystemExit(0)

    if exc_class is SystemExit:
        kill_threads()
        print("Quit by User (SystemExit)")
        if MAIN_APP is not None:
            MAIN_APP.quit()
        exit_status = exc_instance.code
        raise SystemExit(exit_status)

    t_back = entropy.tools.get_traceback(tb_obj = exc_tb)
    t_back += "\n"
    t_back += ''.join(entropy.tools.print_exception(True, tb_data = exc_tb))

    if "--debug" in sys.argv:
        print(t_back)
        import pdb
        pdb.set_trace()

    my = ExceptionDialog()
    my.show(errmsg = t_back) 
    kill_threads()
    if MAIN_APP is not None:
        MAIN_APP.quit(sysexit = False)

def install_exception_handler():
    sys.excepthook = handle_exception

def uninstall_exception_handler():
    sys.excepthook = sys.__excepthook__

install_exception_handler()
try:
    gtk.window_set_default_icon_from_file(
        const.PIXMAPS_PATH+"/sulfur-icon.png")
except gobject.GError:
    pass

MAIN_APP = SulfurApplication()
MAIN_APP.init()
gobject.threads_init()
gtk.gdk.threads_enter()
gtk.main()
gtk.gdk.threads_leave()
kill_threads()
MAIN_APP.quit()
raise SystemExit(0)
