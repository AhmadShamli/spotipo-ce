# -*- coding: utf-8 -*-
from spotipo_plugins import connect_event

from unifispot.modules import SpotipoPlugin,create_method_field

from .main import module

__version__ = "0.1"
__plugin__ = "GoogleLoginPlugin"


def create_gp_settings_button():
    return create_method_field('Google Plus Login','auth_google','google')


class GoogleLoginPlugin(SpotipoPlugin):

    name = "Google Login Plugin"

    description = ("This Plugin provides Google Login for Spotipo.")

    author = "sudheesh"

    license = "AGPL"

    version = __version__


    def setup(self):
        self.register_blueprint(module, url_prefix="")
        connect_event("print-login-method-settings", create_gp_settings_button)
