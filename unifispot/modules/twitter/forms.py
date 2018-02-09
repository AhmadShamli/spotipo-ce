from flask_wtf import FlaskForm as Form
from wtforms import TextField, HiddenField,BooleanField,TextAreaField,\
                        IntegerField,PasswordField,SelectField
from wtforms.validators import Required,DataRequired,Email
from wtforms.fields.html5 import EmailField

from unifispot.core.const import *
from unifispot.utils.translation import _l,_n,_

class TwConfigForm(Form):
    data_limit          = IntegerField(_('Data Limit(Mb)',default=0))
    time_limit          = IntegerField(_('Time Limit(Min)',default=0))
    speed_ul            = IntegerField(_('Ul Speed Limit(Kbps)',default=0))
    speed_dl            = IntegerField(_('DL Speed Limit(Kbps)',default=0))
    consumer_key        = TextField(_('Consumer Key'))
    consumer_secret     = TextField(_('Consumer Secret'))
    session_limit_control= SelectField(_('Restrict Sessions'),coerce=int,choices=[])
    session_overridepass= TextField(_('Override Password'))
    relogin_policy      = SelectField(_('Guest has to login'),choices=[])
    
    def populate(self):
        self.session_limit_control.choices = [(0,'Never'),(1,'Daily'),(2,'Monthly')]
        self.relogin_policy.choices=[('always','Always'),('onetime','One Time'),
                                        ('monthly','Monthly')]


class TwOverrideForm(Form):
    password            = PasswordField(_('Password'),validators = [Required()])


def generate_twform(twconfig):
    optinout_fields = twconfig.optinout_fields or {}

    class F(Form):
        pass

    return F()