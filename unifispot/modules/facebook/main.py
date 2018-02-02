import json
import arrow
import logging
import validators
import urllib
from flask_security import current_user
from functools import wraps
from facebook import get_user_from_cookie, GraphAPI,GraphAPIError
from flask import request,abort,render_template,url_for,redirect,flash,current_app

from unifispot.utils.translation import _l,_n,_
from unifispot.core.const import *
from unifispot.core.app import UnifispotModule
from unifispot.core.utils import render_guest_template
from unifispot.core.models import Wifisite,Guest,Landingpage
from unifispot.core.guestutils import validate_track,init_track,redirect_guest,\
                                guestlog_warn,guestlog_info,guestlog_error,\
                                guestlog_debug,guestlog_exception,assign_guest_entry,\
                                get_loginauth_validator,loginauth_check_relogin
from unifispot.core.baseviews import SiteModuleAPI
from .models import Fbconfig,Fbauth
from .forms import FbConfigForm,CheckinForm,FbOverrideForm,generate_fbform


module = UnifispotModule('facebook','login', __name__, template_folder='templates')

class FbConfigAPI(SiteModuleAPI):

    def get_form_obj(self):
        return FbConfigForm()

    def get_name(self):
        return self.__class__.__name__

    def get_modal_obj(self): 
        return Fbconfig

    def get_config_template(self):
        return 'module_config_facebook.html'

FbConfigAPI.register(module, route_base='/s/<siteid>/facebook/config')

#----------------------guest related

def get_login_config(wifisite,guesttrack):
    '''This method needs to be added to all login plugins
        Called by redirec_guest when rendering multi landing page
        return loginconfig object for the current login method

    '''
    fbconfig = Fbconfig.query.filter_by(siteid=wifisite.id).first()
    if not fbconfig:
        guestlog_warn('trying to access fb_login without configuring ',
                        wifisite,guesttrack)
        abort(404)
    return fbconfig   


def check_device_relogin(wifisite,guesttrack,loginconfig):
    '''This method needs to be added to all login plugins
        Called by redirec_guest when rendering multi landing page
        return True if the given device can be logged in successfully

    '''    
    return loginauth_check_relogin(wifisite,guesttrack,Fbauth,loginconfig)


def get_multilanding_html(wifisite,guesttrack):
    '''This method needs to be added to all login plugins
        Called by redirec_guest when rendering multi landing page
        return HTML for buttons or otherwise that needs to be rendered
        on the multilanding.html page

    '''
    loginurl = url_for('unifispot.modules.facebook.guest_login',
                            trackid=guesttrack.trackid)
    return '''<p> 
                <a class="btn btn-block btn-social btn-facebook" href="%s?from_multilanding=1" id="facebook-login">
                <span class="fa fa-facebook"></span><strong>'''%loginurl+_('Login with Facebook')+ ''' </strong>
            </a>   </p> '''


def get_trackid_from_parameters(f):
    '''Decorator for getting trackid from parameters instead of URL part
        needed for facebook
        It injects  trackid  in kwargs
    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        state  = request.args.get('state')
        if not state:
            flash('State not found','danger')
            abort(404)
        try:
            trackid = json.loads(state).get('trackid')
            if not trackid:
                flash('Track id not found','danger')
                abort(404)
        except Exception as e:
            flash('Invalid state value','danger')
            abort(404)
        kwargs['trackid'] = trackid
        return f(*args, **kwargs)
    return decorated_function


def validate_fbconfig(f):
    '''Decorator for validating fbconfig detials. 
        It injects  emailconfigobjects in kwargs

    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        wifisite    =  kwargs.get('wifisite')
        guesttrack  =  kwargs.get('guesttrack')
        #get the function name used 
        fname = f.func_name
        #check if site is configured for emaillogin
        if not wifisite.check_login_en('auth_facebook'):
            guestlog_warn('trying to access fb_login for  non configured site',wifisite,guesttrack)
            abort(404)
        #get and validated fbconfig
        fbconfig = Fbconfig.query.filter_by(siteid=wifisite.id).first()
        if not fbconfig:
            guestlog_warn('trying to access fb_login without configuring ',
                        wifisite,guesttrack)
            abort(404)
        kwargs['fbconfig'] = fbconfig
        return f(*args, **kwargs)
    return decorated_function

@module.route('/fb/guest/<trackid>',methods = ['GET', 'POST'])
@validate_track
@validate_fbconfig
@get_loginauth_validator(Fbauth,'fbconfig','facebook','auth_facebook')
def guest_login(trackid,guesttrack,wifisite,guestdevice,fbconfig,loginauth):
    ''' Function to called if the site is configured with FB login    
    
    '''    
    fb_appid = fbconfig.fb_appid
    auth_fb_post = fbconfig.auth_fb_post
    return_url = url_for('unifispot.modules.facebook.fb_login_check',
                         _external=True)
    data = {"trackid": trackid}
    state = json.dumps(data)

    extra_profile_fields = fbconfig.get_extra_profile_fields()

    url = "https://www.facebook.com/dialog/oauth?client_id=%s&scope=email,%s&redirect_uri=%s&state=%s"%(fb_appid,extra_profile_fields,return_url,state)

    #if the guest is coming from multi landing and 
    #consent is not enabled,directly send to FB redirect
    from_multilanding = request.args.get('from_multilanding') 
    if from_multilanding and not fbconfig.optinout_enabled():
        return redirect(url)


    fbform = generate_fbform(fbconfig)

    if fbform.validate_on_submit():
        #form submitted 
        if fbconfig.optinout_enabled():
            guesttrack.updateextrainfo('consent',fbform.consent.data)
        return redirect(url)

    else:
        landingpage = Landingpage.query.filter_by(siteid=wifisite.id).first()
        return render_guest_template('social_landing.html',wifisite.template,
                    wifisite=wifisite,landingpage=landingpage,
                    fb_appid=fb_appid,auth_fb_post=auth_fb_post,
                    fbform=fbform,url=url)

@module.route('/fb/login/check/',methods = ['GET', 'POST'])
@get_trackid_from_parameters
@validate_track
@validate_fbconfig
@get_loginauth_validator(Fbauth,'fbconfig','facebook','auth_facebook')
def fb_login_check(trackid,guesttrack,wifisite,guestdevice,fbconfig,loginauth):
    '''End point for validating guest's FB login

    '''
    code  = request.args.get('code')
    state  = request.args.get('state')
    access_token = None
    fb_appid = fbconfig.fb_appid   
    fb_app_secret = fbconfig.fb_app_secret    
    if code:    
        #URL called after OAuth
        redirect_uri = url_for('unifispot.modules.facebook.fb_login_check',
                                _external=True)
        try:
            at  = GraphAPI().get_access_token_from_code(code, redirect_uri, 
                        fb_appid, fb_app_secret)
            access_token = at['access_token']
            graph = GraphAPI(access_token)
            profile = graph.get_object("me",fields='name,email,first_name,last_name,gender,birthday,age_range')
            if not profile:
                #
                #User is not logged into DB app, redirect to social login page
                guestlog_warn('guestdevice MAC:%s facebook_login  empty profile, \
                    should be redirected to login '%guestdevice.devicemac,wifisite
                    ,guesttrack)            
                return redirect_guest(wifisite,guesttrack)
        except:
            guestlog_exception('guestdevice MAC:%s facebook_login  exception , \
                    should be redirected to login '%guestdevice.devicemac,wifisite,
                    guesttrack)
            return redirect_guest(wifisite,guesttrack)        
    else:
        #URL could be called by JS, check for cookies
        #
        try:
            check_user_auth = get_user_from_cookie(cookies=request.cookies, 
                                    app_id=fb_appid,app_secret=fb_app_secret)
            access_token = check_user_auth['access_token']
            graph = GraphAPI(access_token) 
            profile = graph.get_object("me",fields='name,email,first_name,last_name,gender,birthday,age_range')
            if not check_user_auth or not check_user_auth['uid'] or not profile:
                #
                #User is not logged into DB app, redirect to social login page
                guestlog_warn('guestdevice MAC:%s facebook_login  empty profile, \
                    should be redirected to login '%guestdevice.devicemac,
                            wifisite,guesttrack)            
                return redirect_guest(wifisite,guesttrack)
        except:
            guestlog_exception('guestdevice MAC:%s facebook_login  exception , \
                    should be redirected to login '%guestdevice.devicemac,wifisite,
                    guesttrack)
            return redirect_guest(wifisite,guesttrack)   
    #create FB AUTH             
    loginauth.fbprofileid  = profile['id']
    loginauth.fbtoken      = access_token
    loginauth.save()


    #add/update guest
    newguest = assign_guest_entry(wifisite,guesttrack,fbprofile=profile)

    #update guesttrack   

    #update guestdevice
    guestdevice.guestid     = newguest.id
    guestdevice.save()
    #update guest
    newguest.demo           = guesttrack.demo
    newguest.devices.append(guestdevice)
    newguest.save()

    #check if either checkin/like configured
    if fbconfig.auth_fb_post == 1:
        return redirect(url_for('unifispot.modules.facebook.fb_checkin')+'?state={}'.format(state))
    elif fbconfig.auth_fb_like == 1 and newguest.fbliked != 1:
        return redirect(url_for('unifispot.modules.facebook.fb_like',trackid=trackid))
    else:
        loginauth.populate_auth_details(fbconfig)
        loginauth.reset()     
        loginauth.reset_lastlogin()
        loginauth.state = LOGINAUTH_FIRST
        loginauth.save()            
        #neither configured, authorize guest
        guesttrack.state        = GUESTTRACK_POSTLOGIN
        guesttrack.loginauthid  = loginauth.id 
        guesttrack.updatestat('auth_facebook',1)
        return redirect_guest(wifisite,guesttrack)


@module.route('/fb/checkin/',methods = ['GET', 'POST'])
@get_trackid_from_parameters
@validate_track
@validate_fbconfig
@get_loginauth_validator(Fbauth,'fbconfig','facebook','auth_facebook')
def fb_checkin(trackid,guesttrack,wifisite,guestdevice,fbconfig,loginauth):
    '''End point for guest to checkin

    '''
    code  = request.args.get('code')
    state  = request.args.get('state')
    access_token = None
    fb_appid = fbconfig.fb_appid   
    fb_app_secret = fbconfig.fb_app_secret 
    fb_page = fbconfig.fb_page        
    redirect_uri = url_for('unifispot.modules.facebook.fb_checkin',
                _external=True)
    checkin_url = url_for('unifispot.modules.facebook.fb_checkin')+'?state={}'.format(state)  
    if code:
        #URL called after OAuth        
        try:
            at  = GraphAPI().get_access_token_from_code(code, redirect_uri,\
                             fb_appid, fb_app_secret)
            access_token = at['access_token']
            graph = GraphAPI(access_token)
            permissions = graph.get_connections("me","permissions")
        except:
            guestlog_exception('fb_checkin exception while getting access_token \
                                redirecting to fb_checkin ',wifisite,
                                            guesttrack)            
            #send back to page
            return redirect(redirect_uri,code=302)
    else:
        try:
            graph = GraphAPI(loginauth.fbtoken)
            permissions = graph.get_connections("me","permissions")

        except:
            guestlog_exception('fb_checkin exception while getting permissions \
                                redirecting to fb_checkin ',wifisite,guesttrack)
                                              
            return redirect_guest(wifisite,guesttrack)

    #check if the user has granted publish_permissions
    publish_permission = False
    for perm in permissions['data']:
        if perm.get('permission') == 'publish_actions' and\
                 perm.get('status') == 'granted':    
            publish_permission = True 

    if not publish_permission:
        guestlog_warn('fb_checkin  called without guest giving publish_permission redo Oauth\
                         fbauth',wifisite,guesttrack)        
        
        params={'client_id':fb_appid,'redirect_uri':redirect_uri,
                'scope':'publish_actions ','state':state}
        url = 'https://www.facebook.com/dialog/oauth?'+urllib.urlencode(params)
        return redirect(url,code=302)            

    checkinform = CheckinForm()
    if checkinform.validate_on_submit():
        #try to do checkin
        try:
             
            page_info = graph.get_object(fb_page,
                    fields='description,name,location,picture')
            graph.put_wall_post(message=checkinform.message.data,
                                    attachment={'place':page_info['id']})
        except Exception as e: 
            if 'Duplicate status message' in str(e):
                guestlog_warn('duplicate message exception while doing checkin, \
                                ask guest to enter some message',wifisite,guesttrack)
                flash(_('Please enter some message'),'danger')
            else:
                guestlog_exception('exception while doing checkin',wifisite,guesttrack)
        else:
            #mark fbauth with checkedin
            guesttrack.updatestat('fbcheckedin',1)
            guest = Guest.query.get(guestdevice.guestid)
            if not guest:
                guestlog_warn("no guest associated with guestdevice",wifisite,guesttrack)
                return redirect_guest(wifisite,guesttrack)

            loginauth.fbcheckedin = 1
            loginauth.save()

            guest.fbcheckedin = 1
            guest.save()
            #check if guest needs to be redirected to asklike 
            #page
            if fbconfig.auth_fb_like:
                if guest.fbliked != 1:
                    return redirect(url_for('unifispot.modules.facebook.fb_like',trackid=trackid))
                else:
                    #to ensure all the loginauth related to a guest
                    #is marked as fb liked
                    loginauth.fbliked = 1
                    loginauth.save()
            else:
                #redirect guest to auth page
                loginauth.populate_auth_details(fbconfig)
                loginauth.reset()     
                loginauth.reset_lastlogin()
                loginauth.state = LOGINAUTH_FIRST
                loginauth.save()            
                #neither configured, authorize guest
                guesttrack.state        = GUESTTRACK_POSTLOGIN
                guesttrack.loginauthid  = loginauth.id 
                guesttrack.updatestat('auth_facebook',1)
                return redirect_guest(wifisite,guesttrack)

    guestlog_debug('show ask for checkin page',wifisite,guesttrack)

    landingpage = Landingpage.query.filter_by(siteid=wifisite.id).first()

    page_info = graph.get_object(fb_page,fields='location,name')     
    loc = page_info['location']
    location = ' %s - %s %s %s'%(page_info.get('name',''),loc.get('street',''),
                        loc.get('city',''),loc.get('country',''))
    return render_template("guest/%s/fb_checkin.html"%wifisite.template,
                            landingpage = landingpage,
                            app_id=fb_appid,checkin_url=checkin_url,fb_page=fb_page,
                            location=location,checkinform=checkinform)


@module.route('/fb/like/<trackid>',methods = ['GET', 'POST'])
@validate_track
@validate_fbconfig
@get_loginauth_validator(Fbauth,'fbconfig','facebook','auth_facebook')
def fb_like(trackid,guesttrack,wifisite,guestdevice,fbconfig,loginauth):
    auth_like = None
    auth_post = None    
    if request.method == 'POST':
        auth_like = request.form['authlike']    

    if auth_like == '1' :
        #quick hack to test for liking and posting, guest has skipped the liking, allow
        #internet for now and ask next time
        pass

    elif auth_like == '2':
        #user has liked the page mark track and guest as liked          
        guest = Guest.query.get(guestdevice.guestid)
        if not guest:
            guestlog_warn("no guest associated with guestdevice",wifisite,guesttrack)
            return redirect_guest(wifisite,guesttrack)        
        guest.fbliked = 1
        guest.save()

        loginauth.fbliked = 1
        loginauth.save()

        guesttrack.updatestat('fbliked',1)

    else:
        #show page asking guest to like
        landingpage = Landingpage.query.filter_by(siteid=wifisite.id).first()
        fb_page = fbconfig.fb_page 
        fb_appid = fbconfig.fb_appid 
        guestlog_debug('show ask for like page',wifisite,guesttrack)
        return render_template("guest/%s/fb_like.html"%wifisite.template,
                    landingpage = landingpage,fb_appid=fb_appid,trackid=trackid,
                    fb_page=fb_page)


    #redirect guest to auth page
    loginauth.populate_auth_details(fbconfig)
    loginauth.reset()     
    loginauth.reset_lastlogin()
    loginauth.state = LOGINAUTH_FIRST
    loginauth.save()            
    #neither configured, authorize guest
    guesttrack.state        = GUESTTRACK_POSTLOGIN
    guesttrack.loginauthid  = loginauth.id 
    guesttrack.updatestat('auth_facebook',1)
    return redirect_guest(wifisite,guesttrack)



@module.route('/fb/override/<trackid>',methods = ['GET', 'POST'])
@validate_track
@validate_fbconfig
def guest_override(trackid,guesttrack,wifisite,guestdevice,fbconfig):
    ''' Function to called if the guest have exceeded daily/monthly limit   
    
    '''    

    return handle_override(guesttrack,wifisite,guestdevice,fbconfig,
            Fbauth,FbOverrideForm,'limit_override.html',
            'auth_facebook')