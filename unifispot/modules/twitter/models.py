import arrow
from wtforms import BooleanField,TextField,IntegerField

from unifispot.core.db import db,FORMAT_DATETIME,JSONEncodedDict
from unifispot.core.const import *
from unifispot.core.models import Loginauth,Wifisite
from unifispot.utils.modelhelpers import SerializerMixin,CRUDMixin,LoginconfigMixin
from unifispot.utils.translation import format_datetime



class Twconfig(LoginconfigMixin,CRUDMixin,SerializerMixin,db.Model):
    id                  = db.Column(db.Integer, primary_key=True)
    account_id          = db.Column(db.Integer, db.ForeignKey('account.id'))
    siteid              = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    consumer_key        = db.Column(db.String(200))
    consumer_secret     = db.Column(db.String(200))
    data_limit          = db.Column(db.BigInteger,default=0)
    time_limit          = db.Column(db.Integer,default=60)
    speed_ul            = db.Column(db.Integer,default=0)
    speed_dl            = db.Column(db.Integer,default=0)
    session_limit_control= db.Column(db.Integer)
    session_overridepass = db.Column(db.String(50))
    relogin_policy      = db.Column(db.String(25),default='onetime')
    optinout_fields     = db.Column(JSONEncodedDict(255))
    site                = db.relationship(Wifisite, backref=db.backref("twitterconfigs", \
                                cascade="all,delete"))
    def __init__(self):
        '''Initial values for fields

        '''
        self.optinout_fields = {'optinout_enable':0,
                                'optinout_label':"I have read and agree to T&C",
                                'optinout_default':1,'optinout_mandatory':0}


    #serializer arguement
    __json_hidden__ = []

    __json_modifiers__ = {'optinout_fields':'modeljson_to_dict'}


    __form_fields_avoid__ = ['id','siteid','account_id']

    __form_fields_modifiers__ =  { 'optinout_fields':'form_to_modeljson'}

    def optinout_enabled(self):
        if self.optinout_fields.get('optinout_enable'):
            return 1
        else:
            return 0


class Twauth(Loginauth):
    twprofileid     = db.Column(db.String(200),index=True)
    twtoken         = db.Column(db.Text)
    twtokensecret   = db.Column(db.Text)
    __mapper_args__ = {'polymorphic_identity': 'twauth'}

    def reset_lastlogin(self):
        self.last_login_at = arrow.utcnow().naive
        self.save()

    def login_completed(self,loginconfig):
        if self.state == LOGINAUTH_INIT:
            return False
        else:
            return True
