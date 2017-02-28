from flask_wtf import Form
from wtforms import TextField, HiddenField,BooleanField,TextAreaField,\
                        PasswordField,SelectField,FileField
from wtforms.validators import Required,DataRequired,Email,NumberRange
from wtforms.fields.html5 import EmailField,IntegerField

from unifispot.utils.translation import _l,_n,_
from unifispot.core.const import *

class VoucherConfigForm(Form):
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


    def populate(self):
        pass


def generate_voucherform(voucherconfig):
    enable_fields   = voucherconfig.enable_fields
    mandate_fields  = voucherconfig.mandate_fields
    labelfor_fields = voucherconfig.labelfor_fields

    class F(Form):
        pass

    setattr(F, 'voucher', TextField('Voucher*',validators = [DataRequired()])) 

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

class VoucherDesignForm(Form):
    site_id         = HiddenField(_('Site ID'))
    logofile        = HiddenField(_('Header File'))   
    bgcolor         = TextField(_('Background Color'))
    txtcolor        = TextField(_('Text Color'))
    bordercolor     = TextField(_('Border Color'))
    showlogo        = BooleanField(_('Show Logo'),default=1)     
    shownotes       = BooleanField(_('Show Notes'),default=1)
    showqr          = BooleanField(_('Show QRcode'),default=1)
    showduration    = BooleanField(_('Show Duration'),default=1)
    showdata        = BooleanField(_('Show Data Limit'),default=1)
    showspeed       = BooleanField(_('Show Speed Limit'),default=1)
    def populate(self):
        pass    

class VoucherFilesForm(Form):
    logofile        = FileField(_('Logo File'))
    def populate(self):
        pass        

class VoucherForm(Form):  
    duration_val    = IntegerField(_("Duration"),validators = [DataRequired()])
    batchid         = IntegerField(_("Batch ID"),[DataRequired(),NumberRange(min=1000,
                            max=9999,message=_('Batch ID should be a 4 digit number'))])
    notes           = TextField(_("Note"))
    number          = IntegerField(_("Create"),validators = [DataRequired()])
    bytes_t         = IntegerField(_("Total Data in Mb"))
    duration_type   = SelectField(_("Select"),coerce=int,
                            choices=[(1,'Minutes'),(2,'Hours'),(3,'Days')] )  
    num_devices     = IntegerField(_("Devices Allowed"),validators = [DataRequired()])  
    speed_dl        = IntegerField(_("Download Speed"))
    speed_ul        = IntegerField(_("Upload Speed"))
    def populate(self):
        pass        