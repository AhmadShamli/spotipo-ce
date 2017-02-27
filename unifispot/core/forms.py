import os
from timezones import zones
from flask import current_app,request,flash
from flask_wtf import FlaskForm as Form
from wtforms import TextField, HiddenField,SelectField,FileField,\
            BooleanField,PasswordField,TextAreaField,RadioField,\
            SelectMultipleField,widgets,validators
from wtforms.validators import Required,Email
from flask_security import current_user
import importlib
from spotipo_plugins import get_plugin


from unifispot.utils.translation import _l,_n,_
from unifispot.core.const import font_list
from unifispot.core.models import Wifisite
from unifispot.ext.plugins import plugin_manager



class UserForm(Form):
    email       = TextField(_('Email'),validators = [Required()])
    displayname = TextField(_('Name'),validators = [Required()])
    password    = PasswordField(_('Password')) 
    repassword  = PasswordField(_('Confirm Password'))
    
    def populate(self):
        pass

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False
        if self.password and (self.password.data != self.repassword.data):
            self.password.errors.append(_("Entered passwords didn't match"))
            return False
        return True

class AccountForm(Form):
    unifi_server    = TextField(_('Controller IP'),validators = [Required()])
    unifi_user      = TextField(_('Controller Username'),
                                validators = [Required()])
    unifi_pass      = PasswordField(_('Controller Password'),
                                validators = [Required()])
    unifi_port      = TextField(_('Controller Port'),
                                validators = [Required()])
    unifi_version   = SelectField(_('Controller API version'),
                                choices=[('v4','V4/V5')])

    def populate(self):
        pass

class MailsettingsForm(Form):
    mail_server     = TextField(_('Mail Server'))
    #mail_username   = TextField(_('Mail Username'))
    #mail_password   = PasswordField(_('Mail Password'))
    mail_port       = TextField(_('Mail Port'))
    #mail_use_tls    = SelectField(_('Mail Enable TLS'),coerce=int,
    #                            choices=[(0,'No'),(1,'Yes')])
    #mail_use_ssl    = SelectField(_('Mail Enable SSL'),coerce=int,
    #                            choices=[(0,'No'),(1,'Yes')])
    mail_default_sender= TextField(_('Mail Default Sender'))    

    def populate(self):
        pass

class TestEmailForm(Form):
    sendto     = TextField(_('Recipient Email'),
                        validators = [Required(),Email()])    



def get_wifisite_form(baseform=False):
    class F(Form):
        name                = TextField(_('Name'),validators = [Required()])   
        timezone            = SelectField(_('Site Timezone'),choices=[])
        client_id           = SelectField(_('Select Client'),coerce=int,
                                    choices=[],default=0)
        backend_type        = SelectField(_('Select Site Type'),
                                    choices=[('unifi',"UniFi")],default='unifi')  


        def populate(self,wifisite=None):
            from unifispot.core.models import Client
            clients = Client.query.filter_by(account_id=current_user.account_id).all()
            self.client_id.choices = []
            for client in clients:
                self.client_id.choices.append((client.id,client.displayname))

            self.timezone.choices = [ (tz_name,tz_formated)for tz_offset, tz_name, tz_formated in zones.get_timezones() ]


            if not baseform:
                self.sitekey.choices = []
                #populate sitekey with available options if specific id is specified
                if wifisite and wifisite.backend_type:
                    #try to get available sitekeys
                    try:
                        module_path = current_app.config.get('MODULE_PATH', 'modules')
                        backend_module = ".".join([current_app.name, module_path,
                                                    wifisite.backend_type,'main'])
                        backend = importlib.import_module(backend_module)
                        sitekeys = getattr(backend,'get_sitekeys')(wifisite)
                    except:
                        flash(_('Error while getting sitelist. \
                                        Please check Controller settings'), 'danger')
                        current_app.logger.exception("Exception while trying to get sitekeys for :%s"\
                                        %wifisite.id)
                    else:
                        self.sitekey.choices = sitekeys


    if not baseform:
        setattr(F,'redirect_url',TextField(_('Redirect Guest to URL'),
                        default='http://www.unifispot.com'))
        setattr(F,'reports_list',TextField(_('Additional Report Recipients')))
        setattr(F,'reports_type',SelectField(_('Select Reports Frequency'),
                                    choices=[('none','No Reporting'),
                                              ('weekly','Weekly Reports'),
                                              ('monthly','Monthly Reports')]))



        setattr(F,'sitekey',SelectField(_('Site ID'),choices=[]))
        setattr(F,'unifi_id',TextField(_('UniFi Site')))

        for p_name in plugin_manager.plugins:
            plugin = get_plugin(p_name)
            if plugin.type in ['login']:
                fieldname = 'auth_%s'%p_name
                fieldlabel = _('%s Login'%p_name.title())
                setattr(F,fieldname,TextField(fieldlabel))        

            elif plugin.type in ['prelogin']:
                fieldname = 'preauth_%s'%p_name
                fieldlabel = _('%s '%p_name.title())
                setattr(F,fieldname,TextField(fieldlabel)) 

            elif plugin.type in ['postlogin']:
                fieldname = 'postauth_%s'%p_name
                fieldlabel = _('Postlogin %s '%p_name.title())
                setattr(F,fieldname,TextField(fieldlabel)) 
            elif plugin.type in ['export']:
                fieldname = 'export_%s'%p_name
                fieldlabel = _('Export to %s '%p_name.title())
                setattr(F,fieldname,TextField(fieldlabel)) 

            if p_name == 'branding':
                choices = []
                for templ in os.listdir(current_app.config['GUEST_TEMPLATES']):
                    choices.append((templ,templ))                
                setattr(F,'template',SelectField(_('Select Template'),
                                    choices=choices))        


    return F() 


class LandingFilesForm(Form):
    logofile        = FileField(_('Logo File'))
    bgfile          = FileField(_('Background Image'))
    tosfile         = FileField(_('Select T&C pdf'))
    def populate(self):
        pass    

class SimpleLandingPageForm(Form):
    pagebgcolor1     = TextField(_('Page Background Color'))
    gridbgcolor     = TextField(_('Grid Background Color'))
    textcolor       = TextField(_('Text Color'))
    textfont        = SelectField('Select Font',coerce=int,default=2)
    def populate(self):
        #Font options
        fonts = [(idx,font) for idx,font in enumerate(font_list)]
        self.textfont.choices = fonts

class LandingPageForm(Form):
    site_id         = HiddenField('Site ID')
    logofile        = HiddenField('Header File')  
    bgfile          = HiddenField('Background Image')
    pagebgcolor     = TextField(_('Page Background Color'))    
    bgcolor         = TextField(_('Header Background Color'))
    headerlink      = TextField(_('Header Link'))
    basefont        = SelectField(_('Header Base Font'),coerce=int,default=2)
    topbgcolor      = TextField(_('Top Background Color'))
    toptextcolor    = TextField(_('Top Text Color'))
    topfont         = SelectField(_('Top Font'),coerce=int,default=2)
    toptextcont     = TextAreaField(_('Top Content'))
    middlebgcolor   = TextField(_('Middle Background Color'))
    middletextcolor = TextField(_('Middle Text Color'))
    middlefont      = SelectField(_('Bottom Base Font'),coerce=int,default=2)
    bottombgcolor   = TextField(_('Bottom Background Color'))
    bottomtextcolor = TextField(_('Bottom Text Color'))
    bottomfont      = SelectField(_('Base Font'),coerce=int,default=2)
    footerbgcolor   = TextField(_('Footer Background Color'))
    footertextcolor = TextField(_('Text Color'))
    footerfont      = SelectField(_('Base Font'),coerce=int,default=2)
    footertextcont  = TextAreaField(_('Footer Content'))
    btnbgcolor      = TextField(_('Button Color'))
    btntxtcolor     = TextField(_('Button Text Color'))
    btnlinecolor    = TextField(_('Button Border Color'))
    tosfile         = HiddenField(_('Select T&C pdf'))
    copytextcont    = TextAreaField(_('Copyright Text'))
    

    def populate(self):
        #Font options
        fonts = [(idx,font) for idx,font in enumerate(font_list)]
        self.basefont.choices = fonts
        self.topfont.choices = fonts
        self.middlefont.choices = fonts
        self.bottomfont.choices = fonts
        self.footerfont.choices = fonts

