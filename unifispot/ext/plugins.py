from spotipo_plugins import PluginManager

plugin_manager = PluginManager()



def configure(app):
    plugin_manager.init_app(app,plugin_folder="modules")