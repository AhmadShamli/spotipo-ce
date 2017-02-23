from flask import request,session
from flask.json import JSONEncoder as BaseEncoder
from speaklater import _LazyString
from flask_babelplus import Domain, get_locale,Babel
from spotipo_plugins import get_enabled_plugins

import os

babel = Babel()


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


#Modify JSONEncoder to handle babel texts
#http://stackoverflow.com/questions/26124581/flask-json-serializable-error-because-of-flask-babel
class JSONEncoder(BaseEncoder):
    def default(self, o):
        if isinstance(o, _LazyString):
            return str(o)

        return BaseEncoder.default(self, o)

def configure(app):
    babel.init_app(app,default_domain=SpotipoDomain(app))

    app.json_encoder = JSONEncoder

    if babel.locale_selector_func is None:
        @babel.localeselector
        def get_locale():
            override = request.args.get('lang')
            if override:
                session['lang'] = override
            else:
                # use default language if set
                if app.config.get('BABEL_DEFAULT_LOCALE'):
                    session['lang'] = app.config.get('BABEL_DEFAULT_LOCALE')
                else:
                    # get best matching language
                    if app.config.get('BABEL_LANGUAGES'):
                        session['lang'] = request.accept_languages.best_match(
                            app.config.get('BABEL_LANGUAGES')
                        )

            return session.get('lang', 'en')    

