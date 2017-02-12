# -*- coding: utf-8 -*-
from spotipo_plugins import connect_event

from unifispot.modules import SpotipoPlugin,create_method_field

from .main import module

__version__ = "0.1"
__plugin__ = "EmailLoginPlugin"


def create_email_settings_button():
    return create_method_field('Email Login','auth_email','email')


class EmailLoginPlugin(SpotipoPlugin):

    name = "Email Login Plugin"

    description = ("This Plugin provides Email Login for Spotipo.")

    author = "rakeshmukundan"

    license = "AGPL"

    version = __version__


    def setup(self):
        self.register_blueprint(module, url_prefix="")
        connect_event("print-login-method-settings", create_email_settings_button)



