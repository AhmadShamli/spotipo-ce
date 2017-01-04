from blinker import Namespace
unifispot_signals = Namespace()

# Signals
device_loggedin     = unifispot_signals.signal('device_loggedin')

newguest_signup     = unifispot_signals.signal('newguest_signup')

guest_loggedin      = unifispot_signals.signal('guest_loggedin')

guest_fbliked       = unifispot_signals.signal('guest_fbliked')

guest_fbcheckedin   = unifispot_signals.signal('guest_fbcheckedin')