# coding: utf-8
from flask_security import Security 
from flask_security import Security,SQLAlchemyUserDatastore
from unifispot.core.tasks import send_security_email


security = Security()



def configure(app,user_datastore):
    security_ctx = security.init_app(app,user_datastore)

    ##workaround from http://stackoverflow.com/questions/27345291/sending-async-email-with-flask-security
    ## to avoid circular import 
    @security_ctx.send_mail_task
    def delay_security_email(msg):
        send_security_email.delay(msg)    
