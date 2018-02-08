import arrow
import logging
import validators
import json
import urllib
import urlparse
import httplib2
from oauth2client import client
from flask_security import current_user
from functools import wraps
from user_agents import parse
from flask import request,abort,render_template,url_for,redirect,flash,\
            current_app

from unifispot.utils.translation import _l,_n,_
from unifispot.core.const import *
from unifispot.core.app import UnifispotModule
from unifispot.core.models import Wifisite,Guest,Landingpage
from unifispot.core.guestutils import validate_track,init_track,redirect_guest,\
                                guestlog_warn,guestlog_info,guestlog_error,\
                                guestlog_debug,guestlog_exception,assign_guest_entry,\
                                get_loginauth_validator,loginauth_check_relogin
from unifispot.core.baseviews import SiteModuleAPI
from .models import Gpconfig,Gpauth
from .forms import GpConfigForm, generate_gpform, GpOverrideForm


module = UnifispotModule('google','login', __name__, template_folder='templates')

class GpConfigAPI(SiteModuleAPI):

    def get_form_obj(self):
        return GpConfigForm()

    def get_name(self):
        return self.__class__.__name__

    def get_modal_obj(self):
        return Gpconfig

    def get_config_template(self):
        return 'module_config_google.html'

GpConfigAPI.register(module, route_base='/s/<siteid>/google/config')

#----------------------guest related

def get_login_config(wifisite,guesttrack):
    '''This method needs to be added to all login plugins
        Called by redirec_guest when rendering multi landing page
        return loginconfig object for the current login method

    '''
    gpconfig = Gpconfig.query.filter_by(siteid=wifisite.id).first()
    if not gpconfig:
        guestlog_warn('trying to access google_login without configuring ',
                        wifisite,guesttrack)
        abort(404)
    return gpconfig


def check_device_relogin(wifisite,guesttrack,loginconfig):
    '''This method needs to be added to all login plugins
        Called by redirec_guest when rendering multi landing page
        return True if the given device can be logged in successfully

    '''
    return loginauth_check_relogin(wifisite,guesttrack,Gpauth,loginconfig)

def get_multilanding_html(wifisite,guesttrack):
    '''This method needs to be added to all login plugins
        Called by redirec_guest when rendering multi landing page
        return HTML for buttons or otherwise that needs to be rendered
        on the multilanding.html page

    '''
    loginurl = url_for('unifispot.modules.google.guest_login',
                            trackid=guesttrack.trackid)
    return '''<p>
                <a class="btn btn-google block full-width m-b" href="%s?from_multilanding=1" id="google-login">
                <strong>Login with Google Plus </strong>
            </a>   </p> '''%loginurl


def validate_gpconfig(f):
    '''Decorator for validating google config details.
        It injects  emailconfigobjects in kwargs

    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        wifisite    =  kwargs.get('wifisite')
        guesttrack  =  kwargs.get('guesttrack')
        #get the function name used
        fname = f.func_name
        #check if site is configured for emaillogin
        if not wifisite.check_login_en('auth_google'):
            guestlog_warn('trying to access google_login for  non configured site',wifisite,guesttrack)
            abort(404)
        #get and validated fbconfig
        gpconfig = Gpconfig.query.filter_by(siteid=wifisite.id).first()
        if not gpconfig:
            guestlog_warn('trying to access google_login without configuring ',
                        wifisite,guesttrack)
            abort(404)
        kwargs['gpconfig'] = gpconfig
        return f(*args, **kwargs)
    return decorated_function


def get_trackid_from_parameters(f):
    '''Decorator for getting trackid from parameters instead of URL part
        needed for google plus
        It injects  trackid  in kwargs
    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        state = request.args.get('state')
        decoded = urlparse.parse_qsl(state)
        param_dict = dict(decoded)
        trackid = param_dict.get('trackid')
        if not trackid:
            abort(404)
        kwargs['trackid'] = trackid
        return f(*args, **kwargs)
    return decorated_function


@module.route('/gp/login/<trackid>',methods = ['GET', 'POST'])
@validate_track
@validate_gpconfig
@get_loginauth_validator(Gpauth,'gpconfig','google','auth_google')
def guest_login(trackid,guesttrack,wifisite,guestdevice,gpconfig,loginauth):
    '''Function to called if the site is configured with Google login

        also handles collecting guest consent

    '''
    client_id       = gpconfig.client_id
    client_secret    = gpconfig.client_secret
    redirect_uri = url_for('unifispot.modules.google.gp_login_check',_external=True)
    state = urllib.urlencode({ "trackid" : trackid})
    flow = client.OAuth2WebServerFlow(
        client_id = client_id,
        client_secret = client_secret,
        scope = "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email",
        redirect_uri=redirect_uri
        )
    url = flow.step1_get_authorize_url(state=state)

    #if the guest is coming from multi landing and
    #consent is not enabled,directly send to google redirect
    from_multilanding = request.args.get('from_multilanding')
    if from_multilanding and not gpconfig.optinout_enabled():
        return redirect(url)

    gpform = generate_gpform(gpconfig)
    if gpform.validate_on_submit():
        #form submitted
        if gpconfig.optinout_enabled():
            guesttrack.updateextrainfo('consent',gpform.consent.data)
        return redirect(url)

    else:
        landingpage = Landingpage.query.filter_by(siteid=wifisite.id).first()
        return render_template('guest/%s/google_landing.html'%wifisite.template,
                    wifisite=wifisite,landingpage=landingpage,
                    trackid=trackid,gpform=gpform, gpurl=url)


@module.route('/gp/login/check/',methods = ['GET', 'POST'])
@get_trackid_from_parameters
@validate_track
@validate_gpconfig
@get_loginauth_validator(Gpauth,'gpconfig','google','auth_google')
def gp_login_check(trackid,guesttrack,wifisite,guestdevice,gpconfig,loginauth):
    '''End point for validating guest's Google login

    '''
    client_id       = gpconfig.client_id
    client_secret    = gpconfig.client_secret
    redirect_uri = url_for('unifispot.modules.google.gp_login_check',_external=True)
    code = request.args.get('code')
    if 'error' in request.args or not code:
        guestlog_warn('Code not recieved'%wifisite
        ,guesttrack)
        return redirect_guest(wifisite,guesttrack)

    flow = client.OAuth2WebServerFlow(
        client_id = client_id,
        client_secret = client_secret,
        scope = "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email",
        redirect_uri = redirect_uri
        )

    try:
        credentials = flow.step2_exchange(code=code)
    except:
        guestlog_exception('Error! Failed to get access token.',wifisite,
                guesttrack)
        return redirect_guest(wifisite,guesttrack)
    access_token = credentials.access_token
    parser = httplib2.Http()
    resp, content = parser.request("https://www.googleapis.com/oauth2/v1/userinfo?access_token={accessToken}".format(accessToken=access_token))
    # #this gets the google profile!!
    profile = json.loads(content)
    if not profile:
        #User is not logged into DB app, redirect to social login page
        guestlog_warn('guestdevice MAC:%s google_login  empty profile, \
            should be redirected to login '%guestdevice.devicemac,wifisite
            ,guesttrack)
        return redirect_guest(wifisite,guesttrack)

    #create google AUTH
    loginauth.gpprofileid   = profile.get('id')
    loginauth.gptoken       = access_token
    loginauth.save()


    #add/update guest
    newguest = assign_guest_entry(wifisite,guesttrack,loginauth,gpprofile=profile)

    #update guesttrack

    #update guestdevice
    guestdevice.guestid     = newguest.id
    guestdevice.save()
    #update guest
    newguest.demo           = guesttrack.demo
    newguest.devices.append(guestdevice)
    newguest.save()


    loginauth.populate_auth_details(gpconfig)
    loginauth.reset()
    loginauth.reset_lastlogin()
    loginauth.state = LOGINAUTH_FIRST
    loginauth.save()
    #neither configured, authorize guest
    guesttrack.state        = GUESTTRACK_POSTLOGIN
    guesttrack.loginauthid  = loginauth.id
    guesttrack.updatestat('auth_google',1)
    return redirect_guest(wifisite,guesttrack)


@module.route('/gp/override/<trackid>',methods = ['GET', 'POST'])
@validate_track
@validate_gpconfig
def guest_override(trackid,guesttrack,wifisite,guestdevice,gpconfig):
    ''' Function to called if the guest have exceeded daily/monthly limit

    '''

    return handle_override(guesttrack,wifisite,guestdevice,gpconfig,
            Gpauth,GpOverrideForm,'limit_override.html',
            'auth_google')
