import arrow
import logging
import validators
import urllib
import tweepy
from flask_security import current_user
from functools import wraps
from flask import request,abort,render_template,url_for,redirect,flash,\
            current_app,session

from unifispot.utils.translation import _l,_n,_
from unifispot.core.const import *
from unifispot.core.app import UnifispotModule
from unifispot.core.models import Wifisite,Guest,Landingpage
from unifispot.core.guestutils import validate_track,init_track,redirect_guest,\
                                guestlog_warn,guestlog_info,guestlog_error,\
                                guestlog_debug,guestlog_exception,assign_guest_entry,\
                                get_loginauth_validator,loginauth_check_relogin
from unifispot.core.baseviews import SiteModuleAPI
from .models import Twconfig,Twauth
from .forms import TwConfigForm, generate_twform, TwOverrideForm


module = UnifispotModule('twitter','login', __name__, template_folder='templates')

class TwConfigAPI(SiteModuleAPI):

    def get_form_obj(self):
        return TwConfigForm()

    def get_name(self):
        return self.__class__.__name__

    def get_modal_obj(self):
        return Twconfig

    def get_config_template(self):
        return 'module_config_twitter.html'

TwConfigAPI.register(module, route_base='/s/<siteid>/twitter/config')

#----------------------guest related

def get_login_config(wifisite,guesttrack):
    '''This method needs to be added to all login plugins
        Called by redirec_guest when rendering multi landing page
        return loginconfig object for the current login method

    '''
    twconfig = Twconfig.query.filter_by(siteid=wifisite.id).first()
    if not twconfig:
        guestlog_warn('trying to access twitter_login without configuring ',
                        wifisite,guesttrack)
        abort(404)
    return twconfig


def check_device_relogin(wifisite,guesttrack,loginconfig):
    '''This method needs to be added to all login plugins
        Called by redirec_guest when rendering multi landing page
        return True if the given device can be logged in successfully

    '''
    return loginauth_check_relogin(wifisite,guesttrack,Twauth,loginconfig)

def get_multilanding_html(wifisite,guesttrack):
    '''This method needs to be added to all login plugins
        Called by redirec_guest when rendering multi landing page
        return HTML for buttons or otherwise that needs to be rendered
        on the multilanding.html page

    '''
    loginurl = url_for('unifispot.modules.twitter.guest_login',
                            trackid=guesttrack.trackid)
    return '''<p>
                <a class="btn btn-twitter block full-width m-b" href="%s?from_multilanding=1" id="twitter-login">
                <strong>Login with Twitter </strong>
            </a>   </p> '''%loginurl


def validate_twconfig(f):
    '''Decorator for validating twitter config details.
        It injects  emailconfigobjects in kwargs

    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        wifisite    =  kwargs.get('wifisite')
        guesttrack  =  kwargs.get('guesttrack')
        #get the function name used
        fname = f.func_name
        #check if site is configured for emaillogin
        if not wifisite.check_login_en('auth_twitter'):
            guestlog_warn('trying to access twitter_login for  non configured site',wifisite,guesttrack)
            abort(404)
        #get and validated fbconfig
        twconfig = Twconfig.query.filter_by(siteid=wifisite.id).first()
        if not twconfig:
            guestlog_warn('trying to access twitter_login without configuring ',
                        wifisite,guesttrack)
            abort(404)
        kwargs['twconfig'] = twconfig
        return f(*args, **kwargs)
    return decorated_function


@module.route('/tw/login/<trackid>',methods = ['GET', 'POST'])
@validate_track
@validate_twconfig
@get_loginauth_validator(Twauth,'twconfig','twitter','auth_twitter')
def guest_login(trackid,guesttrack,wifisite,guestdevice,twconfig,loginauth):
    '''Function to called if the site is configured with Twitter login

        also handles collecting guest consent

    '''
    return_url = url_for('unifispot.modules.twitter.tw_login_check',trackid=trackid,_external=True)
    consumer_key        = twconfig.consumer_key
    consumer_secret     = twconfig.consumer_secret
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret,return_url)
    try:
        url = auth.get_authorization_url()
    except tweepy.TweepError:
        guestlog_exception('Error! Failed to get request token.')
        return redirect_guest(wifisite,guesttrack)

    session['request_token'] = auth.request_token
    #if the guest is coming from multi landing and
    #consent is not enabled,directly send to twitter redirect
    from_multilanding = request.args.get('from_multilanding')
    if from_multilanding and not twconfig.optinout_enabled():
        return redirect(url)


    twform = generate_twform(twconfig)

    if twform.validate_on_submit():
        #form submitted
        if twconfig.optinout_enabled():
            guesttrack.updateextrainfo('consent',twform.consent.data)
        return redirect(url)

    else:
        landingpage = Landingpage.query.filter_by(siteid=wifisite.id).first()
        return render_template('guest/%s/twitter_landing.html'%wifisite.template,
                    wifisite=wifisite,landingpage=landingpage,
                    trackid=trackid,twform=twform, twurl=url)


@module.route('/tw/login/check/<trackid>',methods = ['GET', 'POST'])
@validate_track
@validate_twconfig
@get_loginauth_validator(Twauth,'twconfig','twitter','auth_twitter')
def tw_login_check(trackid,guesttrack,wifisite,guestdevice,twconfig,loginauth):
    '''End point for validating guest's Twitter login

    '''
    verifier           = request.args.get('oauth_verifier')
    consumer_key       = twconfig.consumer_key
    consumer_secret    = twconfig.consumer_secret
    auth  = tweepy.OAuthHandler(consumer_key, consumer_secret)
    token = session.get('request_token')
    auth.request_token = token

    # auth.request_token = { 'oauth_token' : token,
                        #  'oauth_token_secret' : verifier }

    if verifier:
        try:
            auth.get_access_token(verifier)
            api = tweepy.API(auth)
            response = api.verify_credentials(include_email=True)
            profile = response._json
            if not profile:
                #User is not logged into DB app, redirect to social login page
                guestlog_warn('guestdevice MAC:%s twitter_login  empty profile, \
                    should be redirected to login '%guestdevice.devicemac,wifisite
                    ,guesttrack)
                return redirect_guest(wifisite,guesttrack)
        except tweepy.TweepError:
            guestlog_exception('Error! Failed to get access token.',wifisite,
                    guesttrack)
            return redirect_guest(wifisite,guesttrack)
    else:
        guestlog_exception('Did not recieve verification code from twitter',wifisite,
                    guesttrack)
        return redirect_guest(wifisite,guesttrack)

    #create Twitter AUTH
    loginauth.twprofileid   = profile.get('id')
    loginauth.twtoken       = auth.access_token
    loginauth.twtokensecret = auth.access_token_secret
    loginauth.save()


    #add/update guest
    newguest = assign_guest_entry(wifisite,guesttrack,twprofile=profile)

    #update guesttrack

    #update guestdevice
    guestdevice.guestid     = newguest.id
    guestdevice.save()
    #update guest
    newguest.demo           = guesttrack.demo
    newguest.devices.append(guestdevice)
    newguest.save()


    loginauth.populate_auth_details(twconfig)
    loginauth.reset()
    loginauth.reset_lastlogin()
    loginauth.state = LOGINAUTH_FIRST
    loginauth.save()
    #neither configured, authorize guest
    guesttrack.state        = GUESTTRACK_POSTLOGIN
    guesttrack.loginauthid  = loginauth.id
    guesttrack.updatestat('auth_twitter',1)
    return redirect_guest(wifisite,guesttrack)


@module.route('/tw/override/<trackid>',methods = ['GET', 'POST'])
@validate_track
@validate_twconfig
def guest_override(trackid,guesttrack,wifisite,guestdevice,twconfig):
    ''' Function to called if the guest have exceeded daily/monthly limit

    '''

    return handle_override(guesttrack,wifisite,guestdevice,twconfig,
            Twauth,TwOverrideForm,'limit_override.html',
            'auth_twitter')
