#!/bin/sh
# postinst script for spotipo

set -e

# summary of how this script can be called:
#        * <postinst> `configure' <most-recently-configured-version>
#        * <old-postinst> `abort-upgrade' <new version>
#        * <conflictor's-postinst> `abort-remove' `in-favour' <package>
#          <new-version>
#        * <postinst> `abort-remove'
#        * <deconfigured's-postinst> `abort-deconfigure' `in-favour'
#          <failed-install-package> <version> `removing'
#          <conflicting-package> <version>
# for details, see http://www.debian.org/doc/debian-policy/ or
# the debian-policy package

# source debconf library
. /usr/share/debconf/confmodule

CONFFILE=/usr/share/nginx/spotipo/instance/config.py
INSTALLDIR=/usr/share/nginx/spotipo

$INSTALLDIR/.env/bin/python $INSTALLDIR/manage.py db migrate
$INSTALLDIR/.env/bin/python $INSTALLDIR/manage.py db upgrade

service nginx restart
service supervisor restart
