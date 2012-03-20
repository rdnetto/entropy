# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Fabio Erculiani

Authors:
  Fabio Erculiani

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; version 3.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
"""
import os
from threading import Lock, Semaphore

from gi.repository import Gtk, GLib, GObject, GdkPixbuf

from rigo.enums import Icons
from rigo.models.application import Application, ApplicationMetadata

from entropy.const import const_debug_write, const_debug_enabled


class AppListStore(Gtk.ListStore):

    # column types
    COL_TYPES = (GObject.TYPE_PYOBJECT,)

    # column id
    COL_ROW_DATA = 0

    # default icon size returned by Application.get_icon()
    ICON_SIZE = 48
    _MISSING_ICON = None
    _MISSING_ICON_MUTEX = Lock()
    _ICON_CACHE = {}

    __gsignals__ = {
        # Redraw signal, requesting UI update
        # for given pkg_match object
        "redraw-request"  : (GObject.SignalFlags.RUN_LAST,
                             None,
                             (GObject.TYPE_PYOBJECT, ),
                             ),
    }

    def __init__(self, entropy_client, entropy_ws, view, icons):
        Gtk.ListStore.__init__(self)
        self._view = view
        self._entropy = entropy_client
        self._entropy_ws = entropy_ws
        self._icons = icons
        self.set_column_types(self.COL_TYPES)

        # Startup Entropy Package Metadata daemon
        ApplicationMetadata.start()

    def clear(self):
        """
        Clear ListStore content (and Icon Cache).
        """
        outcome = Gtk.ListStore.clear(self)
        AppListStore._ICON_CACHE.clear()
        return outcome

    @property
    def _missing_icon(self):
        """
        Return the missing icon Gtk.Image() if needed.
        """
        if AppListStore._MISSING_ICON is not None:
            return AppListStore._MISSING_ICON
        with AppListStore._MISSING_ICON_MUTEX:
            if AppListStore._MISSING_ICON is not None:
                return AppListStore._MISSING_ICON
            _missing_icon = self._icons.load_icon(
            Icons.MISSING_APP, AppListStore.ICON_SIZE, 0)
            AppListStore._MISSING_ICON = _missing_icon
            return _missing_icon

    def _is_app_visible(self, pkg_match):
        """
        Returns whether Application (through pkg_match) is still
        visible in the TreeView.
        This method shall be Thread safe.
        """
        s_data = {
            'sem': Semaphore(0),
            'res': None,
        }

        def _get_visible(data):
            valid_paths, start_path, end_path = self._view.get_visible_range()
            if not valid_paths:
                data['res'] = False
                data['sem'].release()
                return

            path = start_path
            while path <= end_path:
                path_iter = self.get_iter(path)
                if self.iter_is_valid(path_iter):
                    visible_pkg_match = self.get_value(path_iter, 0)
                    if visible_pkg_match == pkg_match:
                        data['res'] = True
                        data['sem'].release()
                        return
                path.next()

            data['res'] = False
            data['sem'].release()
            return

        GLib.idle_add(_get_visible, s_data)
        s_data['sem'].acquire()

        return s_data['res']

    def get_icon(self, pkg_match):
        cached = AppListStore._ICON_CACHE.get(pkg_match)
        if cached is not None:
            return cached

        def _ui_redraw_callback(*args):
            if const_debug_enabled():
                const_debug_write(__name__,
                                  "_ui_redraw_callback(), %s" % (args,))
            GLib.idle_add(self.emit, "redraw-request", pkg_match)
        app = Application(self._entropy, self._entropy_ws, pkg_match,
                          redraw_callback=_ui_redraw_callback)

        def _still_visible():
            return self._is_app_visible(pkg_match)

        icon, cache_hit = app.get_icon(_still_visible_cb=_still_visible)
        if const_debug_enabled():
            const_debug_write(__name__,
                              "get_icon({%s, %s}) = %s, hit: %s" % (
                    (pkg_match, app.name, icon, cache_hit,)))

        if icon is None:
            if cache_hit:
                # this means that there is no icon for package
                # and so we should not keep bugging underlying
                # layers with requests
                AppListStore._ICON_CACHE[pkg_match] = self._missing_icon
            return self._missing_icon

        icon_path = icon.local_document()
        if not os.path.isfile(icon_path):
            return self._missing_icon

        try:
            img = Gtk.Image.new_from_file(icon_path)
        except GObject.GError:
            return self._missing_icon

        img_buf = img.get_pixbuf()
        if img_buf is None:
            # wth, invalid crap
            return self._missing_icon
        w, h = img_buf.get_width(), img_buf.get_height()
        del img_buf
        del img
        if w < 1:
            # not legit
            return self._missing_icon
        width = AppListStore.ICON_SIZE
        height = width * h / w

        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                icon_path, width, height)
        except GObject.GError:
            try:
                os.remove(icon_path)
            except OSError:
                pass
            return self._missing_icon

        AppListStore._ICON_CACHE[pkg_match] = pixbuf
        return pixbuf

    def is_installed(self, pkg_match):
        def _ui_redraw_callback(*args):
            if const_debug_enabled():
                const_debug_write(__name__,
                                  "_ui_redraw_callback()")
            GLib.idle_add(self.emit, "redraw-request", pkg_match)

        app = Application(self._entropy, self._entropy_ws, pkg_match,
                          redraw_callback=_ui_redraw_callback)
        return app.is_installed()

    def is_available(self, pkg_match):
        def _ui_redraw_callback(*args):
            if const_debug_enabled():
                const_debug_write(__name__,
                                  "_ui_redraw_callback()")
            GLib.idle_add(self.emit, "redraw-request", pkg_match)

        app = Application(self._entropy, self._entropy_ws, pkg_match,
                          redraw_callback=_ui_redraw_callback)
        return app.is_available()

    def get_markup(self, pkg_match):
        def _ui_redraw_callback(*args):
            if const_debug_enabled():
                const_debug_write(__name__,
                                  "_ui_redraw_callback()")
            GLib.idle_add(self.emit, "redraw-request", pkg_match)

        app = Application(self._entropy, self._entropy_ws, pkg_match,
                          redraw_callback=_ui_redraw_callback)
        return app.get_markup()

    def get_review_stats(self, pkg_match):
        def _ui_redraw_callback(*args):
            if const_debug_enabled():
                const_debug_write(__name__,
                                  "_ui_redraw_callback()")
            GLib.idle_add(self.emit, "redraw-request", pkg_match)

        app = Application(self._entropy, self._entropy_ws, pkg_match,
                          redraw_callback=_ui_redraw_callback)

        def _still_visible():
            return self._is_app_visible(pkg_match)

        return app.get_review_stats(_still_visible_cb=_still_visible)

    def get_application(self, pkg_match):
        def _ui_redraw_callback(*args):
            if const_debug_enabled():
                const_debug_write(__name__,
                                  "_ui_redraw_callback()")
            GLib.idle_add(self.emit, "redraw-request", pkg_match)

        app = Application(self._entropy, self._entropy_ws, pkg_match,
                          redraw_callback=_ui_redraw_callback)
        return app

    def get_transaction_progress(self, pkg_match):
        # FIXME, lxnay complete this
        # int from 0 - 100, or -1 for no transaction
        return -1
