# svntrac
#
# Copyright (C) 2003 Xyche Software
# Copyright (C) 2003 Jonas Borgstr�m <jonas@xyche.com>
#
# svntrac is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# svntrac is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Author: Jonas Borgstr�m <jonas@xyche.com>

import os
import sys
import cgi
import warnings
from util import set_cgi_name, set_authcgi_name
from svn import util, repos, core
import Href

warnings.filterwarnings('ignore', 'DB-API extension cursor.next() used')

import db
from auth import verify_authentication
from perm import cache_permissions, PermissionError

modules = {
#  name module class need_db need_svn    
    'log'         : ('Log', 'Log', 1),
    'file'        : ('File', 'File', 1),
    'wiki'        : ('Wiki', 'Wiki', 0),
    'report'      : ('Report', 'Report', 0),
    'ticket'      : ('Ticket', 'Ticket', 0),
    'browser'     : ('Browser', 'Browser', 1),
    'timeline'    : ('Timeline', 'Timeline', 1),
    'changeset'   : ('Changeset', 'Changeset', 1),
    'newticket'   : ('Ticket', 'Newticket', 0),
    }

def main():
    mode = 'wiki' #default module
    db.init()
    config = db.load_config()
    set_cgi_name(config['general']['cgi_name'])
    set_authcgi_name(config['general']['authcgi_name'])
    Href.initialize(config)

    core.apr_initialize()
    pool = core.svn_pool_create(None)
    
    _args = cgi.FieldStorage()
    args = {}
    for x in _args.keys():
	args[x] = _args[x].value

    if args.has_key('mode'):
        mode = args['mode']

    module_name, constructor_name, need_svn = modules[mode]
    module = __import__(module_name, globals(),  locals(), [])
    constructor = getattr(module, constructor_name)
    module = constructor(config, args, pool)

    verify_authentication (args)
    cache_permissions()

    if need_svn:
        repos_dir = config['general']['svn_repository']
        rep = repos.svn_repos_open(repos_dir, pool)
        fs_ptr = repos.svn_repos_fs(rep)
        module.repos = rep
        module.fs_ptr = fs_ptr
        db.sync (rep, fs_ptr, pool)

    try:
        module.render()
        module.apply_template()
    except Exception, e:
        print 'Content-Type: text/plain\r\n\r\n',
        import traceback
        traceback.print_exc(file=sys.stdout)
        
    core.svn_pool_destroy(pool)
    core.apr_terminate()


