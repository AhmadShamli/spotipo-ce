# -*- coding: utf-8 -*-
"""
    spotipo.plugins
    ~~~~~~~~~~~~~~~

    This module contains the Plugin class used by all Plugins for Spotipo.

    Based on https://github.com/sh4nks/flaskbb/blob/master/flaskbb/plugins/__init__.py


"""
from flask import current_app
from spotipo_plugins import Plugin

def create_method_field(fieldtext,checkboxid,modulename):
    """Method to create method field consist of a check box and config
    button to be used in site-settings page

    """
    return '''<div class="form-group">
                <label class="col-md-3 col-sm-3 col-xs-12 control-label">
                    %s
                </label>
                <div class="checkbox col-xs-5">
                    <label>
                        <input type="checkbox" name="%s" id="%s" value="1">
                    </label>
                    <button type="button" name='%s' id="%s-btn" class="btn btn-info btn-xs method_btn ">Config</button>
                </div>
              </div>'''%(fieldtext,checkboxid,checkboxid,modulename,checkboxid)



class SpotipoPlugin(Plugin):
    #to do add installable property

    # Some helpers
    def register_blueprint(self, blueprint, **kwargs):
        """Registers a blueprint.

        :param blueprint: The blueprint which should be registered.
        """
        current_app.register_blueprint(blueprint, **kwargs)

    def create_table(self, model, db):
        """Creates the relation for the model

        :param model: The Model which should be created
        :param db: The database instance.
        """
        if not model.__table__.exists(bind=db.engine):
            model.__table__.create(bind=db.engine)

    def drop_table(self, model, db):
        """Drops the relation for the bounded model.

        :param model: The model on which the table is bound.
        :param db: The database instance.
        """
        model.__table__.drop(bind=db.engine)

    def create_all_tables(self, models, db):
        """A interface for creating all models specified in ``models``.

        :param models: A list with models
        :param db: The database instance
        """
        for model in models:
            self.create_table(model, db)

    def drop_all_tables(self, models, db):
        """A interface for dropping all models specified in the
        variable ``models``.

        :param models: A list with models
        :param db: The database instance.
        """
        for model in models:
            self.drop_table(model, db)


