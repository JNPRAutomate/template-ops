try:
   from junos import Junos_Context
   PATH = '/var/db/scripts/op/'
except:   
   from os import getcwd 
   PATH = getcwd() + '/'

SSH_KEY = PATH + 'id_rsa'
REMOVE_DEL_CMDS_DURING_PUSH_DIFF_ERR_ENABLE = 1
TEMPLATE_EXEC_ENABLE = 1
TEMPLATE_SEARCH_PATH = PATH + 'xtemplate'
# maximum devices for multi-threaded profile operation
MAX_PROFILE_DEV = 16
COMMIT_TIMEOUT = 30

SAVE_COMMIT_J2_ENABLE = 1
SAVE_COMMIT_CFG_ENABLE = 1
SAVE_EXEC_J2_ENABLE = 1
SAVE_EXEC_PY_ENABLE = 1
SAVE_PATH_COMMIT_J2 =  PATH + 'xarchive'
SAVE_PATH_COMMIT_CFG = PATH + 'xarchive'
SAVE_PATH_EXEC_J2 = PATH + 'xarchive'
SAVE_PATH_EXEC_PY = PATH + 'xarchive'

# groups
vsrx = { 'vsrx-01':{}, 'vsrx-02':{}, 'vsrx-03':{}, 'vsrx-04':{}, }

push_profiles = { 
  'add_srx_1':     { 'comment':['add MX/SRX config 1'] },
  'add_srx_2':     { 'comment':['add MX/SRX config 2'] },
  'add_srx_3':     { 'comment':['add MX/SRX config 3'] },
  'add_srx_4':     { 'comment':['add MX/SRX config 4'] },
  'del_srx_1':     { 'comment':['del MX/SRX config 1'] },
  'del_srx_2':     { 'comment':['del MX/SRX config 2'] },
  'del_srx_3':     { 'comment':['del MX/SRX config 3'] },
  'del_srx_4':     { 'comment':['del MX/SRX config 4'] },
  'update_srx_all':{ 'comment':['update srx config all'] },
  'sessions':      { 'comment':['retrieve sessions for specific source IP'] }, 
  'pl_1_add_json': { 'comment':['loads prefix list pl-1 into eph instance pl, json fmt'] },
  'pl_1_add_set':  { 'comment':['loads prefix list pl-1 into eph instance pl, set fmt'] },
  'pl_1_del':      { 'comment':['empty prefix list pl-1 in ephemeral instance pl'] },
  'filter':        { 'comment':['displays counters from FF counters'] },
  'version':       { 'comment':['show Junos versions'] },
  'mx_local':      { 'comment':['show Junos versions, mx local'] },
  'alarm':         { 'comment':['show system alarms'] },
  'shutdown':      { 'comment':['shutdown all'] },
  'bgp':           { 'comment':['show bgp peers'] },
  'load':          { 'comment':['collect load data'] },
  'mp_load_sum':   { 'comment':['aggregate load data'] },
}

multi_profiles = {
    "sessions": {
        "comment": ["retrieve session info"],
        "push_profiles": [
            {"sessions": {}},
            {"mp_sessions_sum": {"post-delay": 2, "pre-delay": 0}},
        ],
    },
    "status": {
        "comment": ["alarm and version info"],
        "push_profiles": [{"version": {"pre-delay": 1}}, {"alarm": {}}],
    },
    "add_srx_all": {
        "comment": ["add all srx and mx"],
        "push_profiles": [
            {"add_srx_1": {"post-delay": 2}},
            {"add_srx_2": {"post-delay": 2}},
            {"add_srx_3": {"post-delay": 2}},
            {"add_srx_4": {"post-delay": 2}},
            {"bgp": {"pre-delay":10}},
            {"sessions": {}},
            {"mp_sessions_sum": {}},
        ],
    },
    "del_srx_all": {
        "comment": ["del all srx and mx"],
        "push_profiles": [
            {"del_srx_1": {}},
            {"del_srx_2": {}},
            {"del_srx_3": {}},
            {"del_srx_4": {}},
            {"bgp": {}},
        ],
    },
    "load": {
        "comment": ["show SRX load summary"],
        "push_profiles": [
            {"load": {}},
            {"mp_load_sum": {}},
        ],
    },
}
                                 
auth_profiles = {
  'default':{ 'user':['template-ops'], 'port':[830], 'ssh_key':[SSH_KEY] },
   'vmx-01':{ 'host':['10.0.0.10'],},
  'vsrx-01':{ 'host':['10.0.0.11'] },
  'vsrx-02':{ 'host':['10.0.0.12'] },
  'vsrx-03':{ 'host':['10.0.0.13'] },
  'vsrx-04':{ 'host':['10.0.0.14'] },
} 

sessions = {
  'default':{ 'template_vars':['exec1'], 'template':['sessions'], 'input':['0/0'], 'exec':[True] },
  'vsrx-01':{ },
  'vsrx-02':{ },
  'vsrx-03':{ },
  'vsrx-04':{ },
}

mp_sessions = {
  'default':{ 'template_vars':['exec1'], 'template':['mp_sessions'], 'input':['0/0'], 'exec':[True] },
  'vsrx-01':{ },
  'vsrx-02':{ },
  'vsrx-03':{ },
  'vsrx-04':{ },
}

mp_sessions_sum = {
  'default':{ 'template_vars':['exec1'], 'template':['mp_sessions_sum'], 'input':['0/0'], 'exec':[True] },
  'vsrx-01':{ },
}

update_srx_all = {
  'default':{ 'template_vars':['vsrx'], 'template':['cgn_srx_add'] },
  'vsrx-01':{ 'input':['1'] },
  'vsrx-02':{ 'input':['2'] },
  'vsrx-03':{ 'input':['3'] },
  'vsrx-04':{ 'input':['4'] },
}

add_srx_1 = {
   'vmx-01':{ 'template_vars':['mx']  , 'template':  ['cgn_mx_add'], 'input':['1'] },
  'vsrx-01':{ 'template_vars':['vsrx'], 'template': ['cgn_srx_add'], 'input':['1'] },
}

add_srx_2 = {
   'vmx-01':{ 'template_vars':['mx']  , 'template':  ['cgn_mx_add'], 'input':['2'] },
  'vsrx-02':{ 'template_vars':['vsrx'], 'template': ['cgn_srx_add'], 'input':['2'] },
}

add_srx_3 = {
   'vmx-01':{ 'template_vars':['mx']  , 'template':  ['cgn_mx_add'], 'input':['3'] },
  'vsrx-03':{ 'template_vars':['vsrx'], 'template': ['cgn_srx_add'], 'input':['3'] },
}

add_srx_4 = {
   'vmx-01':{ 'template_vars':['mx']  , 'template':  ['cgn_mx_add'], 'input':['4'] },
  'vsrx-04':{ 'template_vars':['vsrx'], 'template': ['cgn_srx_add'], 'input':['4'] },
}


del_srx_1 = {
   'vmx-01':{ 'template_vars':['mx']  , 'template':  ['cgn_mx_del'], 'input':['1'] },
  'vsrx-01':{ 'template_vars':['vsrx'], 'template': ['cgn_srx_del'], 'input':['1'] },
}

del_srx_2 = {
   'vmx-01':{ 'template_vars':['mx']  , 'template':  ['cgn_mx_del'], 'input':['2'] },
  'vsrx-02':{ 'template_vars':['vsrx'], 'template': ['cgn_srx_del'], 'input':['2'] },
}

del_srx_3 = {
   'vmx-01':{ 'template_vars':['mx']  , 'template':  ['cgn_mx_del'], 'input':['3'] },
  'vsrx-03':{ 'template_vars':['vsrx'], 'template': ['cgn_srx_del'], 'input':['3'] },
}

del_srx_4 = {
   'vmx-01':{ 'template_vars':['mx']  , 'template':  ['cgn_mx_del'], 'input':['4'] },
  'vsrx-04':{ 'template_vars':['vsrx'], 'template': ['cgn_srx_del'], 'input':['4'] },
}


pl_1_add_json = {
  'vsrx-01':{ 'template_vars':['vsrx'], 'template':['pl_1_add_json'], 'input':['1'], 'eph_inst':['pl','json'], 'save_rendered_j2':[False, False] },
  'vsrx-02':{ 'template_vars':['vsrx'], 'template':['pl_1_add_json'], 'input':['2'], 'eph_inst':['pl','json'], 'save_rendered_j2':[False, False] },
  'vsrx-03':{ 'template_vars':['vsrx'], 'template':['pl_1_add_json'], 'input':['3'], 'eph_inst':['pl','json'], 'save_rendered_j2':[False, False] },
  'vsrx-04':{ 'template_vars':['vsrx'], 'template':['pl_1_add_json'], 'input':['4'], 'eph_inst':['pl','json'], 'save_rendered_j2':[False, False] },
}

pl_1_add_set = {
  'default':{ 'template_vars':['vsrx'], 'template':['pl_1_add_set'], 'input':['1'], 'eph_inst':['pl','set'] },
  'vsrx-01':{},
  'vsrx-02':{},
  'vsrx-03':{},
  'vsrx-04':{},
}

filter = {
  'default':{ 'template_vars':['exec1'], 'template':['filter'], 'input':['accept'], 'exec':[True], 'save_rendered_j2':[True, False] },
  'vsrx-01':{ },
  'vsrx-02':{ },
  'vsrx-03':{ },
  'vsrx-04':{ },
}

pl_1_del = {
  'vsrx-01':{ 'template_vars':['vsrx'], 'template':['pl_1_del'], 'input':['1'], 'eph_inst':['pl','text'] },
  'vsrx-02':{ 'template_vars':['vsrx'], 'template':['pl_1_del'], 'input':['2'], 'eph_inst':['pl','text'] },
  'vsrx-03':{ 'template_vars':['vsrx'], 'template':['pl_1_del'], 'input':['3'], 'eph_inst':['pl','text'] },
  'vsrx-04':{ 'template_vars':['vsrx'], 'template':['pl_1_del'], 'input':['4'], 'eph_inst':['pl','text'] },
}

version = {
  'default':{ 'template_vars':['exec1'], 'template':['version'], 'input':[''], 'exec':[True] },
  'vsrx-01':{ },
  'vsrx-02':{ },
  'vsrx-03':{ },
  'vsrx-04':{ },
}

alarm = {
  'default':{ 'template_vars':['exec1'], 'template':['alarm'], 'input':[''], 'exec':[True] },
  'vsrx-01':{ },
  'vsrx-02':{ },
  'vsrx-03':{ },
  'vsrx-04':{ },
}

shutdown = {
  'default':{ 'template_vars':['exec1'], 'template':['shutdown'], 'input':[''], 'exec':[True] },
   'vmx-01':{ },
  'vsrx-01':{ },
  'vsrx-02':{ },
  'vsrx-03':{ },
  'vsrx-04':{ },
}

bgp = {
  'default':{ 'template_vars':['exec1'], 'template':['bgp'], 'input':[''], 'exec':[True] },
  'vsrx-01':{ },
  'vsrx-02':{ },
  'vsrx-03':{ },
  'vsrx-04':{ },
}

mx_local = {
  'default':{ 'template_vars':['exec1'], 'template':['version'], 'input':[''], 'exec':[True] },
  'local':{ },
}

load = {
  'default':{ 'template_vars':['exec1'], 'template':['load'], 'input':[''], 'exec':[True] },
}
load = {**load, **vsrx }

mp_load_sum = {
  'default':{ 'template_vars':['exec1'], 'template':['mp_load_sum'], 'input':[''], 'exec':[True] },
  'vsrx-01':{},
}
