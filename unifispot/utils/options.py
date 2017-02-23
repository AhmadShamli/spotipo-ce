from unifispot.core.models import Options


def get_option_value(option_name,default_value=None):
    '''method to return an option value if exists else return default_value

    '''
    try:
        option = Options.query.filter_by(option_name=option_name).first()
        if option != None :
            return option.option_value
        else:
            return default_value
    except:
        return default_value

def set_option_default(option_name,option_value):
    '''method to set the default value for option_name if it doesn't exists

    '''
    try:
        option = Options.query.filter_by(option_name=option_name).first()
        if not option:
            option = Options(option_name=option_name,
                        option_value=option_value)
            option.save()
    except:
        return None
def set_option_value(option_name,option_value):
    '''method to set the value for option_name

    '''
    try:
        option = Options.query.filter_by(option_name=option_name).first()
        if not option:
            option = Options(option_name=option_name,
                        option_value=option_value)
            option.save()
        option.option_value=option_value
        option.save()
    except:
        return None       

def save_options_from_form(form):
    '''Iterate over form fields and save value to options.

        option_name will be ALL CAPS version for form element name
    
        eg: mail_server will be saved as MAIL_SERVER
    '''
    for fieldname, value in form.data.items():
        set_option_value(fieldname.upper(),value)
