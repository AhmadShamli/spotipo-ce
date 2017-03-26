#! flask/bin/python
from os.path import abspath
import arrow
import getpass

from flask import current_app
from flask_script import Manager
from flask_assets import ManageAssets
from flask_migrate import Migrate, MigrateCommand

from unifispot import create_app
from unifispot.core.db import db

from unifispot.utils.translation import (add_translations, compile_translations,
                                        update_translations,
                                        add_plugin_translations,
                                        compile_plugin_translations,
                                        update_plugin_translations)

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())

logger = logging.getLogger()

app = create_app(mode='development')
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def init_data():
    with app.app_context():
        from  sqlalchemy.exc import OperationalError    
        from flask_security.utils import encrypt_password
        from unifispot.core.models import User,Account,Admin  
        import uuid 
        try:
            account = Account.query.filter_by(id=1).first()
            users = Admin.query.count()
        except :
            app.logger.debug( "No Account table Entry found,could be running migration ")
        else:
            enc_pass        = encrypt_password('password')
            if not account:
                #create default admin user                
                account         = Account()
                account.token = str(uuid.uuid4())
                db.session.add(account)
                db.session.commit()
            if not users:
                admin_user = Admin(email='admin@admin.com',password=enc_pass,displayname= "Admin User",active=1)
                admin_user.account_id = account.id
                db.session.add(admin_user)
                db.session.commit()

@manager.command
def init_demo():
    with app.app_context():        
        from  sqlalchemy.exc import OperationalError    
        from flask_security.utils import encrypt_password
        from unifispot.core.models import User,Account,Admin,Client,Wifisite,Landingpage
        from unifispot.core.guestutils import init_track,assign_guest_entry
        from unifispot.modules.analytics.methods import update_daily_stat
        from tests.helpers import randomMAC,randomGuestEmailForm
        from random import randint 

        account         = Account.query.filter_by(id=1).first()
        enc_pass        = encrypt_password('password')

        client1 = Client.query.filter_by(email='client1@gmail.com').first()
        if not client1:
            #add a client
            client1         = Client(email='client1@gmail.com',password=enc_pass,
                                    displayname= "Client User",active=1)
            client1.account_id = account.id
            client1.save()

        site1 = Wifisite.query.get(1)
        if not site1:
            site1 = Wifisite(name='Site1',sitekey='site1')
            site1.client_id = client1.id
            site1.account_id = account.id
            site1.save()
            landing1 = Landingpage()
            landing1.siteid = site1.id 
            landing1.save()

        now = arrow.now()
        month_start = now.replace(days=-30)
        days        = (now - month_start).days
        for d in range(days):
            day_start = month_start.replace(days=d).floor('day')
            logger.warn('-------Generating data for :%s'%day_start )
            for i in range(randint(5,10)):        
                track = init_track(site1,guestmac=randomMAC(),apmac=randomMAC())
                track.timestamp = day_start.replace(minutes=+i*1).naive
                track.loginstat =  {'num_visits':1,'auth_email':1}
                track.save()
                if i%2:
                    f = randomGuestEmailForm()
                    g = assign_guest_entry(site1,track,f)   
                    g.createdat = day_start.replace(minutes=+i*1).naive
                    g.save()
                track.save()
                logger.warn('track added for email ID;%s for :%s'%(track.id,day_start))

            #create random
            #half of them new user
            for i in range(randint(5,10)):        
                track = init_track(site1,guestmac=randomMAC(),apmac=randomMAC())
                track.timestamp = day_start.replace(minutes=+i*1).naive
                track.loginstat =  {'num_visits':1,'auth_facebook':1,'fbcheckedin':1}
                track.save()
                if i%2:
                    g= assign_guest_entry(site1,track,f) 
                    g.createdat = day_start.replace(minutes=+i*1).naive
                    g.save()                      
                    track.updatestat('fbliked',1)
                    track.save()              
                track.save()
                logger.warn('track added for FB ID;%s for :%s'%(track.id,day_start))
            update_daily_stat(site1,day_start)

@manager.command
def reset_admin():
    with app.app_context():
        from unifispot.core.models import User
        from flask_security.utils import encrypt_password
        admin = User.query.filter_by(id=1).first()
        enc_pass        = encrypt_password('password')
        admin.password = enc_pass
        db.session.commit()

@manager.command
def reset_pass():
    with app.app_context():
        from unifispot.core.models import User
        from flask_security.utils import encrypt_password

        def get_admin(iteration=1):
            if (iteration > 1):
                print "Invalid id entered. Try again"
            admin_id =  raw_input("Select the id of admin you want to reset password: ")
            selected_admin = User.query.get(admin_id)
            if not selected_admin:
                return get_admin(iteration=iteration+1)
            else:
                return selected_admin

        def get_password(iteration=1):
            if (iteration > 1):
                print "Passwords did not match. Try again"
            password1 =  getpass.getpass("Give a new password: ")
            password2 =  getpass.getpass("Confirm new password: ")
            if(password1 != password2):
                return get_password(iteration=iteration+1)
            else:
                return password1

        admins = User.query.all()
        print "id\temail"
        for admin in admins:
            print admin.id, "\t", admin.email
        selected_admin = get_admin()
        password = get_password()
        enc_pass = encrypt_password(password)
        selected_admin.password = enc_pass
        db.session.commit()

@manager.command
def rebuild_monthly_stats():
    from unifispot.core.models import User,Account,Admin,Client,Wifisite,Landingpage
    from unifispot.modules.analytics.methods import update_daily_stat
    site1 = Wifisite.query.get(1)
    now = arrow.now()
    month_start = now.floor('month')
    days        = (now.ceil('month') - month_start).days
    for d in range(days):
        day_start = month_start.replace(days=d).floor('day')
        logger.warn('-------Generating analytics data for :%s'%day_start )
        update_daily_stat(site1,day_start)


@manager.command
def get_notifications():
    with app.app_context():
        from unifispot.core.tasks import celery_get_notification
        from unifispot.core.models import Wifisite
        celery_get_notification()            

@manager.command
def send_weekly_reports():
    from unifispot.modules.analytics.tasks import celery_weekly_report  
    celery_weekly_report()

@manager.command
def send_monthly_reports():
    from unifispot.modules.analytics.tasks import celery_monthly_report  
    celery_monthly_report()

@manager.option('-l', '--lang', help='Language',dest='lang')
@manager.option('-p', '--plugin', help='Adds a new language to a plugin.',
                    dest='plugin')
def new_translation(lang,plugin=None):
    """Adds a new language to the translations. "lang" is the language code
    of the language, like, "de_AT"."""
    from unifispot.ext.plugins import plugin_manager
    if plugin:    
        print 'Adding :%s translation for plugin :%s'%(lang,plugin)
        add_plugin_translations(plugin, lang)
    else:
        add_translations(lang)    
        for p_name in plugin_manager.plugins:
            print 'Adding :%s translation for plugin :%s'%(lang,p_name)
            add_plugin_translations(p_name, lang)             


@manager.command
@manager.option('is_all', '--all')
@manager.option('-l', '--lang', help='Language')
def update_translation(is_all=True, plugin=None):
    """Updates all translations."""
    if is_all:
        is_all = True    
    if plugin is not None:
        print"[+] Updating language files for plugin {}..."\
                    .format(plugin)
        update_plugin_translations(plugin)
    else:
        print"[+] Updating language files..."
        update_translations(include_plugins=is_all)

@manager.command
@manager.option('is_all', '--all')
@manager.option('-p', '--plugin', help='Adds a new language to a plugin.')
def compile_translation(is_all=False, plugin=None):
    """Compiles the translations."""
    if is_all:
        is_all = True
    if plugin is not None:
        print"[+] Compiling language files for plugin {}..."\
                    .format(plugin)
        compile_plugin_translations(plugin)
    else:
        print "[+] Compiling language files..."
        compile_translations(include_plugins=is_all)

manager.run()