from flask import request,session
from flask.json import JSONEncoder as BaseEncoder
from speaklater import _LazyString
from flask_babelplus import Domain, get_locale,Babel
from spotipo_plugins import get_enabled_plugins
import os

from unifispot.utils.translation import SpotipoDomain

babel = Babel()




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



