# -*- coding: utf-8 -*-
from spotipo_plugins import connect_event

from unifispot.modules import SpotipoPlugin,create_method_field

from .main import module

__version__ = "0.1"
__plugin__ = "TwitterLoginPlugin"


def create_tw_settings_button():
    return create_method_field('Twitter Login','auth_twitter','twitter')


class TwitterLoginPlugin(SpotipoPlugin):

    name = "Twitter Login Plugin"

    description = ("This Plugin provides Twitter Login for Spotipo.")

    author = "sudheesh"

    license = "AGPL"

    version = __version__


    def setup(self):
        self.register_blueprint(module, url_prefix="")
        connect_event("print-login-method-settings", create_tw_settings_button)
