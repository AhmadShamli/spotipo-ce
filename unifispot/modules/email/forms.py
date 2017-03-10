from flask_wtf import FlaskForm as Form
from wtforms import TextField, HiddenField,BooleanField,TextAreaField,\
                        IntegerField,PasswordField,SelectField
from wtforms.validators import Required,DataRequired,Email
from wtforms.fields.html5 import EmailField

from unifispot.core.const import *
from unifispot.utils.translation import _l,_n,_



def generate_emailform(emailconfig):
    enable_fields   = emailconfig.enable_fields
    mandate_fields  = emailconfig.mandate_fields
    labelfor_fields = emailconfig.labelfor_fields

    class F(Form):
        pass

    def get_field(fieldname,fieldtype,extravalidators=[]):
        if enable_fields.get('enable_%s'%fieldname):
            label = labelfor_fields.get('labelfor_%s'%fieldname)
            if mandate_fields.get('mandate_%s'%fieldname):
                validators = [Required()]
                validators.extend(extravalidators)
                setattr(F, fieldname, fieldtype('%s*'%label,validators = validators)) 
            else:
                setattr(F, fieldname, fieldtype('%s'%label))    

    get_field('email',EmailField,extravalidators=[Email()])
    get_field('firstname',TextField,extravalidators=[])
    get_field('lastname',TextField,extravalidators=[])
    get_field('dob',TextField,extravalidators=[])
    get_field('extra1',TextField,extravalidators=[])
    get_field('extra2',TextField,extravalidators=[])


    return F()

class EmailConfigForm(Form):
    enable_email        = BooleanField(_('Email'),default=1)
    enable_firstname    = BooleanField(_('First Name'),default=1)
    enable_lastname     = BooleanField(_('Last Name'),default=1)
    enable_dob          = BooleanField(_('DOB'),default=1)
    enable_extra1       = BooleanField(_('Extra1'),default=1)    
    enable_extra2       = BooleanField(_('Extra2'),default=1)    
    mandate_email       = BooleanField(_('Email'),default=1)
    mandate_firstname   = BooleanField(_('First Name'),default=1)
    mandate_lastname    = BooleanField(_('Last Name'),default=1)
    mandate_dob         = BooleanField(_('DOB'),default=1)
    mandate_extra1      = BooleanField(_('Extra1'),default=1)    
    mandate_extra2      = BooleanField(_('Extra2'),default=1) 
    labelfor_email      = TextField(_('Email Field'))
    labelfor_firstname  = TextField(_('Firstname Field'))
    labelfor_lastname   = TextField(_('Lastname Field'))
    labelfor_dob        = TextField(_('DOB Field'))
    labelfor_extra1     = TextField(_('Extra Field1'))
    labelfor_extra2     = TextField(_('Extra Field2'))
    data_limit          = IntegerField(_('Data Limit(Mb)'),default=0)
    time_limit          = IntegerField(_('Time Limit(Min)'),default=0)
    speed_ul            = IntegerField(_('Ul Speed Limit(Kbps)'),default=0)
    speed_dl            = IntegerField(_('DL Speed Limit(Kbps)'),default=0)
    session_limit_control= SelectField(_('Restrict Sessions'),coerce=int,choices=[])
    session_overridepass= TextField(_('Override Password'))
    relogin_policy      = SelectField(_('Guest has to login'),choices=[])

    def populate(self):
        self.session_limit_control.choices = [(0,_('No Limit')),
                            (1,_('Daily')),(2,_('Monthly'))]
        self.relogin_policy.choices=[('always','Always'),('onetime','One Time'),
                                        ('monthly','Monthly')]

class EmailOverrideForm(Form):
    password            = PasswordField(_('Password'),validators = [Required()])

   