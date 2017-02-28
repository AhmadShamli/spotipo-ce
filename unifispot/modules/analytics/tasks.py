import os
import logging
import arrow
from flask import render_template,current_app
from premailer import transform,Premailer
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from dateutil import tz
from flask_mail import Message,Attachment
from sqlalchemy import and_,or_

from unifispot.core.models import Wifisite,Guestsession,Guest
from unifispot.ext.celeryext import celery
from unifispot.ext.mail import mail
from unifispot.core.utils import send_email
from unifispot.utils.options import get_option_value
from unifispot.utils.translation import _l,_n,_

from .methods import update_daily_stat

logger =logging.getLogger('analytics.tasks')

@periodic_task(run_every=(crontab(minute="*/5")))
def celery_update_stat(*args, **kwargs):
    logger.info('-----------Running celery_update_stat-----------------------')
    sites = Wifisite.query.all()
    for site in sites:
        tzinfo = tz.gettz(site.timezone)
        now    = arrow.now(tzinfo)
        #process today's status for this site
        update_daily_stat(site,now)
        if now.hour < 2:
            #process yesterday's stats as well
            yesterday = now.replace(days=-1)
            update_daily_stat(site,yesterday)

#task for email reports
@periodic_task(run_every=crontab(hour=0, minute=30, day_of_week=1))
def celery_weekly_report(*args, **kwargs):
    current_app.logger.info('-----------Running celery_weekly_report-----------------------')
    sites = Wifisite.query.all()
    for site in sites:
        if site.reports_type == 'weekly':
            current_app.logger.debug('celery_weekly_report for site:%s'%site.name)
            tzinfo = tz.gettz(site.timezone)
            day     = arrow.now(tzinfo).replace(days=-2) #calculate past week
            start_of_week = day.floor('week')
            end_of_week = day.ceil('week')
            try:
                generate_report(site.id,start_of_week,end_of_week)
            except:
                current_app.logger.exception('celery_weekly_report  exception for site:%s'%site.name)

@periodic_task(run_every=crontab(hour=0, minute=30, day_of_month=1))           
def celery_monthly_report(*args, **kwargs):
    current_app.logger.info('-----------Running celery_monthly_report-----------------------')
    sites = Wifisite.query.all()
    for site in sites:
        if site.reports_type == 'monthly':
            current_app.logger.debug('celery_monthly_report for site:%s'%site.name)
            tzinfo = tz.gettz(site.timezone)
            day     = arrow.now(tzinfo).replace(days=-2)
            start_of_month = day.floor('month')
            end_of_month = day.ceil('month')
            try:
                generate_report(site.id,start_of_month,end_of_month)
            except:
                current_app.logger.exception('celery_monthly_report  exception for site:%s'%site.name)

def generate_report(siteid,startday,endday):
    '''Create and send report for given site during the specified periodic_task


    '''
    site = Wifisite.query.filter_by(id=siteid).first()
    start_date = startday.format('DD-MM-YYYY')
    end_date   = endday.format('DD-MM-YYYY')
    current_app.logger.debug('Going to process report for :%s from :%s to :%s'%(site.name,start_date,end_date))    
    #get all entries within given period
    entries = Guest.query.filter(and_(Guest.siteid==siteid,Guest.demo ==0, 
                    Guest.created_at >= startday,
                    Guest.created_at <= endday)).all()

    csvList = '\n'.join(','.join(row.to_row()) for row in entries)  


    filename = "Report_%s_to_%s.csv"%(start_date,end_date)  
    attachment = Attachment(filename=filename,
                            content_type='txt/plain',
                            data=csvList)
    msg = Message(_("Wifi usage report for the period :%s to :%s"%(start_date,
                        end_date)),
                    recipients=[site.client.email,site.reports_list],
                    attachments =[attachment])

    msg.body  = _("Dear %s,\n\n"\
            "\tPlease find the wifi usage report for the period of starting from:%s to %s \n"\
            "\nRegards\n"\
            "Admin"%(site.name,start_date,end_date))
    mail.send(msg)