from blinker import Namespace
from .tasks import celery_run_exports

unifispot_signals = Namespace()

# Signals
device_loggedin     = unifispot_signals.signal('device_loggedin')

newguest_signup     = unifispot_signals.signal('newguest_signup')

guest_loggedin      = unifispot_signals.signal('guest_loggedin')

guest_fbliked       = unifispot_signals.signal('guest_fbliked')

guest_fbcheckedin   = unifispot_signals.signal('guest_fbcheckedin')



#run export modules when new guest signs up
def run_exports(guest_details):
    celery_run_exports.delay(guest_details['guestid'],guest_details['siteid'])



newguest_signup.connect(run_exports)