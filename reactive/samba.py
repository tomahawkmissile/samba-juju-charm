import os
import sys
import shutil
import charms.apt as apt

from shutil import copyfile

from charmhelpers.core import host

from charms.reactive import when, when_not, set_flag
from charmhelpers.core import hookenv
from charmhelpers.core.templating import render

hooks = hookenv.Hooks()

@when_not('layer-samba.installed')
def install_layer_samba():
    sys.path.append(os.path.realpath('..'))
    # Do your setup here.
    #
    # If your charm has other dependencies before it can install,
    # add those as @when() clauses above., or as additional @when()
    # decorated handlers below
    #
    # See the following for information about reactive charms:
    #
    #  * https://jujucharms.com/docs/devel/developer-getting-started
    #  * https://github.com/juju-solutions/layer-basic#overview
    #
    config = hookenv.config()

    password = config['password']
    server_name = config['server_name']
    online = config['online']

    hookenv.status_set('maintenance', 'Updating apt')
    apt.update()

    hookenv.status_set('maintenance', 'Installing packages')
    apt.queue_install(['samba'])
    apt.install_queued()

    #os.system('git clone https://github.com/bdrung/ionit.git')
    #os.system('python3 ionit/setup.py install')

    hookenv.status_set('maintenance', 'Configuring')

    host.add_group('juju-samba-ubuntu')
    host.adduser('ubuntu',password)
    host.add_user_to_group('ubuntu','juju-samba-ubuntu')

    cmd = ("sudo echo -e \""+password+"\n"+password+"\" | smbpasswd -s -a ubuntu")
    os.system(cmd)

    if not os.path.exists('/opt/samba/share'):
        os.makedirs('/opt/samba/share')
    host.chownr('/opt/samba/share','ubuntu','juju-samba-ubuntu',True,True)
    if not os.path.exists('/etc/samba/smb.conf'):
        os.makedirs('/etc/samba')
        shutil.copy('opt/smb.conf','/etc/samba/smb.conf')
    render(source='smb',target='/etc/samba/smb.conf',
    context={"cfg":config,},
    owner='root',perms=0o740)

    restartSamba()

    set_flag('layer-samba.installed')

    if(not online):
        stopSamba()
        hookenv.status_set('active', 'Stopped')
    hookenv.status_set('active', 'Started')
@when('config.changed.online')
def config_changed_online():
    config = hookenv.config()
    online = config['online']
    if(not online):
        stopSamba()
        hookenv.status_set('active', 'Stopped')
    else:
        startSamba()
        hookenv.status_set('active', 'Started')
@when('config.changed.server_name')
def config_changed_name():
    config = hookenv.config()
    render(source='smb',target='/etc/samba/smb.conf',
    context={"cfg":config,},
    owner='root',perms=0o740)
@when('config.changed.password')
def config_changed_password():
    config = hookenv.config()
    password = config['password']
    cmd = ("sudo echo -e \""+password+"\n"+password+"\" | smbpasswd -s -a ubuntu")
    os.system(cmd)
    host.service_restart('smbd')
@hooks.hook('start')
def start():
    startSamba()
    hookenv.status_set('active', 'Started')
@hooks.hook('stop')
def stop():
    stopSamba()
    hookenv.status_set('active', 'Stopped')

def stopSamba():
    os.system('sudo systemctl stop smbd')
    os.system('sudo systemctl stop nmbd')
    #host.service_stop(service_name='smbd')
    #host.service_stop(service_name='nmbd')
def startSamba():
    os.system('sudo systemctl start smbd')
    os.system('sudo systemctl start nmbd')
    #host.service_start(service_name='smbd')
    #host.service_start(service_name='nmbd')
def restartSamba():
    stopSamba()
    startSamba()
