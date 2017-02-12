# -*- coding: utf-8 -*-
from spotipo_plugins import connect_event

from unifispot.modules import SpotipoPlugin

from .main import module

__version__ = "0.1"
__plugin__ = "PortalPlugin"



class PortalPlugin(SpotipoPlugin):

    name = "Analytics Plugin"

    description = ("This Plugin provides basic analytics for Spotipo.")

    author = "rakeshmukundan"

    license = "AGPL"

    version = __version__


    def setup(self):
        self.register_blueprint(module, url_prefix="")



