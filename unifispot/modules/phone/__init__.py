# -*- coding: utf-8 -*-
from spotipo_plugins import connect_event

from unifispot.modules import SpotipoPlugin,create_method_field

from .main import module

__version__ = "0.1"
__plugin__ = "PhoneLoginPlugin"


def create_phone_settings_button():
    return create_method_field('Phone Login','auth_phone','phone')


class PhoneLoginPlugin(SpotipoPlugin):

    name = "Phone Login Plugin"

    description = ("This Plugin provides Phone Login for Spotipo.")

    author = "rakeshmukundan"

    license = "AGPL"

    version = __version__


    def setup(self):
        self.register_blueprint(module, url_prefix="")
        connect_event("print-login-method-settings", 
                       create_phone_settings_button)



