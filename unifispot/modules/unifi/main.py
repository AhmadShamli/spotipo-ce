from flask import request,abort,jsonify,current_app
import arrow
import logging
from functools import wraps
from flask_security import current_user
import validators

from .controller import Controller
from unifispot.core.app import UnifispotModule
from unifispot.core.const import *
from unifispot.core.models import Wifisite,Loginauth,Account,Guestsession
from unifispot.core.guestutils import validate_track,init_track,redirect_guest,\
                                    guestlog_warn,guestlog_info,guestlog_exception,\
                                    guestlog_exception,show_message


module = UnifispotModule('unifi','general', __name__, template_folder='templates')


##--------------------backend methods------------------------------------
def get_sitekeys(wifisite):
    #returns a list of sitekeys and site names available  
    if current_app.config['NO_UNIFI']:
        return [('test1','TEST1'),('test2','TEST2'),('test3','TEST3')]

    sitekeys = []
    if not wifisite:
        return sitekeys
    account = Account.query.get(wifisite.account_id)
    if not account:
        current_app.logger.warn('Site:%s is not associated with an account'%wifisite.id)      

    c = Controller(account=account,sitekey='default')
    for site in c.get_sites():
        sitekeys.append((site.get('name'),site.get('desc')))
    return sitekeys

def disconnect_client(wifisite,mac):
    #disconnect the given MAC
    if current_app.config['NO_UNIFI']:
        return 1    
    if not wifisite:
        return None
    account = Account.query.get(wifisite.account_id)
    if not account:
        current_app.logger.warn('Site:%s is not associated with an account'%wifisite.id)  
        return None   

    c = Controller(account=account,sitekey=wifisite.sitekey)
    return c.unauthorize_guest(mac)

def update_device_session(wifisite,mac):
    #update session details for a given MAC
    pass
    if current_app.config['NO_UNIFI']:
        return 1   

##


def validate_unificonfig(f):
    '''Decorator for validating emailconfig detials. 
        It injects  emailconfigobjects in kwargs

    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        wifisite    =  kwargs.get('wifisite')
        guesttrack  =  kwargs.get('guesttrack')
        #get the function name used 
        fname = f.func_name
        #check if site is configured for unifi backend
        if not wifisite.backend_type == 'unifi':
            guestlog_warn('guest_auth for a site which is not Unifi site',
                            wifisite,guesttrack)        
            abort(404)
        account = Account.query.get(wifisite.account_id)
        if not account:
            guestlog_warn('guest_auth for a site which is not Unifi site',
                            wifisite,guesttrack)        
            abort(404)    

        kwargs['account'] = account
        return f(*args, **kwargs)
    return decorated_function


@module.route('/guest/s/<sitekey>/',methods = ['GET', 'POST'])
def guest_portal(sitekey):

    #--get all URL parameters, expected URL format--

    devicemac   = request.args.get('id')
    apmac       = request.args.get('ap')   
    visitedurl  = request.args.get('url')   
    demo        = request.args.get('demo')
    utcnow      = arrow.utcnow().naive
  
    
    ua = request.headers.get('User-Agent')
    if ua and 'CaptiveNetworkSupport' in ua:
        current_app.logger.debug('Detected apple CNA, sending our ERROR response')
        return '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN"><HTML><HEAD>
                    <TITLE>ERROR</TITLE></HEAD><BODY>ERROR</BODY></HTML>'''

    if not devicemac or not apmac:
        current_app.logger.error("Guest portal called with empty ap_mac/user_mac URL:%s"\
                %request.url)
        abort(404)

    if not validators.mac_address(devicemac) or not validators.mac_address(apmac):
        current_app.logger.error("Guest portal called with invalid ap_mac/user_mac URL:%s"%\
                request.url)
        abort(404)

    wifisite    = Wifisite.query.filter_by(sitekey=sitekey).first()
    if not wifisite:
        current_app.logger.error("Guest portal called with unknown UnifiID URL:%s"%request.url)
        abort(404)  
    if demo and current_user.is_authenticated:
        demo = 1
    else:
        demo = 0
    guesttrack = init_track(wifisite,devicemac,apmac,visitedurl,demo)   

    return redirect_guest(wifisite,guesttrack)

@module.route('/unifi/auth/<trackid>/',methods = ['GET', 'POST'])
@validate_track
@validate_unificonfig
def guest_auth(trackid,guesttrack,wifisite,guestdevice,account):  
    #redirect to authorize a particular guest

    if not guesttrack.state == GUESTTRACK_AUTH:
        guestlog_warn('guest_auth called with unathorized track',
                        wifisite,guesttrack)
        abort(404)        

    #get login auth
    loginauth = Loginauth.query.filter_by(siteid=wifisite.id,
                        id=guesttrack.loginauthid).first()
    if not loginauth:
        guestlog_warn('guest_auth called without a proper loginauth attached to track',
                        wifisite,guesttrack)
        abort(404)

    time_limit = loginauth.time_available()
    duration = time_limit if time_limit else 480
    
    if not current_app.config['NO_UNIFI']:
        try:                
            c = Controller(account=account,sitekey=wifisite.sitekey)  
            if current_app.config['UNIFI_NO_AP_MAC']:
                #made sending AP MAC to be configurable
                c.authorize_guest(guesttrack.devicemac,duration,
                                  up_bandwidth=loginauth.speed_ul,
                                  down_bandwidth=loginauth.speed_dl)
            else:
                c.authorize_guest(guesttrack.devicemac,duration,
                                  ap_mac=guesttrack.apmac,
                                  up_bandwidth=loginauth.speed_ul,
                                  down_bandwidth=loginauth.speed_dl)    
        except:
            guestlog_exception('exception while trying to authorize guest',wifisite,guesttrack)
            abort(500)   



    #create session if not already created for the track
    guestsession = Guestsession(siteid=wifisite.id,deviceid=guestdevice.id,
                                loginauthid=loginauth.id)
    guestsession.mac =  guestdevice.devicemac
    guestsession.trackid= guesttrack.id
    guestsession.save()

    return show_message(wifisite,guesttrack) 

@module.route('/unifi/tempauth/<trackid>/',methods = ['GET', 'POST'])
@validate_track
def guest_temp_auth(trackid,guesttrack,wifisite,guestdevice):  
    #redirect to authorize a particular guest

    return jsonify({'status':1,'msg':''})      