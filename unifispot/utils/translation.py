from flask import g,current_app
from babel.support import LazyProxy
from flask_babelplus import gettext, lazy_gettext, ngettext
from flask_babelplus import format_datetime as _format_datetime
from flask_babelplus import Domain, get_locale
from spotipo_plugins import get_enabled_plugins

import os
import subprocess
import babel
from unifispot.ext.plugins import plugin_manager

def ugettext(s):
    # we assume a before_request function
    # assigns the correct user-specific
    # translations
    return g.translations.ugettext(s)

ugettext_lazy = LazyProxy(ugettext)

_ = gettext
_l = lazy_gettext
_n = ngettext

def format_datetime(dtime):
    with current_app.app_context():
        return _format_datetime(dtime)


##based on https://github.com/sh4nks/flaskbb/blob/master/flaskbb/utils/translations.py
class SpotipoDomain(Domain):
    def __init__(self, app):
        self.app = app
        super(SpotipoDomain, self).__init__()

        self.plugins_folder = os.path.join(
            os.path.join(self.app.root_path, "modules")
        )

        # Spotipo's translations
        self.spotipo_translations = os.path.join(
            self.app.root_path, "translations"
        )

        # Plugin translations
        with self.app.app_context():
            self.plugin_translations = [
                os.path.join(plugin.path, "translations")
                for plugin in get_enabled_plugins()
            ]

    def get_translations(self):
        """Returns the correct gettext translations that should be used for
        this request.  This will never fail and return a dummy translation
        object if used outside of the request or if a translation cannot be
        found.
        """
        locale = get_locale()
        cache = self.get_translations_cache()

        translations = cache.get(str(locale))
        if translations is None:
            # load Spotipo translations
            translations = babel.support.Translations.load(
                dirname=self.spotipo_translations,
                locales=locale,
                domain="messages"
            )

            # If no compiled translations are found, return the
            # NullTranslations object.
            if not isinstance(translations, babel.support.Translations):
                return translations

            # now load and add the plugin translations
            for plugin in self.plugin_translations:
                plugin_translation = babel.support.Translations.load(
                    dirname=plugin,
                    locales=locale,
                    domain="messages"
                )
                translations.add(plugin_translation)

            cache[str(locale)] = translations

        return translations

def update_translations(include_plugins=False):
    """Updates all translations.
    :param include_plugins: If set to `True` it will also update the
                            translations for all plugins.
    """

    # update spotipo translations
    translations_folder = os.path.join(current_app.root_path, "translations")
    source_file = os.path.join(translations_folder, "messages.pot")

    subprocess.call(["pybabel", "extract", "-F", "babel.cfg",
                     "-k", "lazy_gettext", "-o", source_file, "."])
    subprocess.call(["pybabel", "update", "-i", source_file,
                     "-d", translations_folder])

    if include_plugins:
        # updates all plugin translations too
        for plugin in plugin_manager.all_plugins:
            update_plugin_translations(plugin)


def add_translations(translation):
    """Adds a new language to the translations."""

    translations_folder = os.path.join(current_app.root_path, "translations")
    source_file = os.path.join(translations_folder, "messages.pot")

    subprocess.call(["pybabel", "extract", "-F", "babel.cfg",
                     "-k", "lazy_gettext", "-o", source_file, "."])
    subprocess.call(["pybabel", "init", "-i", source_file,
                     "-d", translations_folder, "-l", translation])


def compile_translations(include_plugins=False):
    """Compiles all translations.
    :param include_plugins: If set to `True` it will also compile the
                            translations for all plugins.
    """

    # compile spotipo translations
    translations_folder = os.path.join(current_app.root_path, "translations")
    subprocess.call(["pybabel", "compile", "-d", translations_folder])

    if include_plugins:
        # compile all plugin translations
        for plugin in plugin_manager.all_plugins:
            compile_plugin_translations(plugin)


def add_plugin_translations(plugin, translation):
    """Adds a new language to the plugin translations. Expects the name
    of the plugin and the translations name like "en".
    """

    plugin_folder = os.path.join(current_app.root_path,'modules', plugin)
    translations_folder = os.path.join(plugin_folder, "translations")
    source_file = os.path.join(translations_folder, "messages.pot")

    subprocess.call(["pybabel", "extract", "-F", "babel.cfg",
                     "-k", "lazy_gettext", "-o", source_file,
                     plugin_folder])
    subprocess.call(["pybabel", "init", "-i", source_file,
                     "-d", translations_folder, "-l", translation])


def update_plugin_translations(plugin):
    """Updates the plugin translations. Expects the name of the plugin."""

    plugin_folder = os.path.join(current_app.root_path,'modules', plugin)
    translations_folder = os.path.join(plugin_folder, "translations")
    source_file = os.path.join(translations_folder, "messages.pot")

    subprocess.call(["pybabel", "extract", "-F", "babel.cfg",
                     "-k", "lazy_gettext", "-o", source_file,
                     plugin_folder])
    subprocess.call(["pybabel", "update", "-i", source_file,
                     "-d", translations_folder])


def compile_plugin_translations(plugin):
    """Compile the plugin translations. Expects the name of the plugin."""

    plugin_folder = os.path.join(self.app.root_path,'modules', plugin)
    translations_folder = os.path.join(plugin_folder, "translations")

    subprocess.call(["pybabel", "compile", "-d", translations_folder])
