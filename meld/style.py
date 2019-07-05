# Copyright (C) 2002-2006 Stephen Kennedy <stevek@gnome.org>
# Copyright (C) 2009 Vincent Legoll <vincent.legoll@gmail.com>
# Copyright (C) 2012-2019 Kai Willadsen <kai.willadsen@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import enum
from typing import (
    Mapping,
    Optional,
    Tuple,
)

from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import GtkSource

from meld.conf import _


class MeldStyleScheme(enum.Enum):
    base = "meld-base"
    dark = "meld-dark"


base_style_scheme: Optional[GtkSource.StyleScheme] = None


def get_base_style_scheme() -> GtkSource.StyleScheme:

    global base_style_scheme

    if base_style_scheme:
        return base_style_scheme

    env_theme = GLib.getenv('GTK_THEME')
    if env_theme:
        use_dark = env_theme.endswith(':dark')
    else:
        gtk_settings = Gtk.Settings.get_default()
        use_dark = gtk_settings.props.gtk_application_prefer_dark_theme

    # As of 3.28, the global dark theme switch is going away.
    if not use_dark:
        from meld.sourceview import MeldSourceView
        stylecontext = MeldSourceView().get_style_context()
        background_set, rgba = (
            stylecontext.lookup_color('theme_bg_color'))

        # This heuristic is absolutely dire. I made it up. There's
        # literally no basis to this.
        if background_set and rgba.red + rgba.green + rgba.blue < 1.0:
            use_dark = True

    base_scheme_name = (
        MeldStyleScheme.dark if use_dark else MeldStyleScheme.base)

    manager = GtkSource.StyleSchemeManager.get_default()
    base_style_scheme = manager.get_scheme(base_scheme_name)

    return base_style_scheme


def colour_lookup_with_fallback(name: str, attribute: str) -> Gdk.RGBA:
    from meld.settings import meldsettings
    source_style = meldsettings.style_scheme

    style = source_style.get_style(name) if source_style else None
    style_attr = getattr(style.props, attribute) if style else None
    if not style or not style_attr:
        base_style = get_base_style_scheme()
        try:
            style = base_style.get_style(name)
            style_attr = getattr(style.props, attribute)
        except AttributeError:
            pass

    if not style_attr:
        import sys
        print(_(
            "Couldn’t find colour scheme details for %s-%s; "
            "this is a bad install") % (name, attribute), file=sys.stderr)
        sys.exit(1)

    colour = Gdk.RGBA()
    colour.parse(style_attr)
    return colour


ColourMap = Mapping[str, Gdk.RGBA]


def get_common_theme() -> Tuple[ColourMap, ColourMap]:
    lookup = colour_lookup_with_fallback
    fill_colours = {
        "insert": lookup("meld:insert", "background"),
        "delete": lookup("meld:insert", "background"),
        "conflict": lookup("meld:conflict", "background"),
        "replace": lookup("meld:replace", "background"),
        "error": lookup("meld:error", "background"),
        "focus-highlight": lookup("meld:current-line-highlight", "foreground"),
        "current-chunk-highlight": lookup(
            "meld:current-chunk-highlight", "background")
    }
    line_colours = {
        "insert": lookup("meld:insert", "line-background"),
        "delete": lookup("meld:insert", "line-background"),
        "conflict": lookup("meld:conflict", "line-background"),
        "replace": lookup("meld:replace", "line-background"),
        "error": lookup("meld:error", "line-background"),
    }
    return fill_colours, line_colours
