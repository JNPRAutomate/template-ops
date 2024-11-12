#!/usr/bin/python
ver = "2024-09-29.138"

"""
template-ops tool 

Copyright (c) 2024, Juniper Networks, Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

# on-box operation check
try:
    from junos import Junos_Context
    import jcs
except:
    import sys

    sys.dont_write_bytecode = True
    import syslog

    onbox = False
else:
    onbox = True

import argparse
import os

if onbox:
    import sys
import traceback
import jinja2
import re
import warnings
import pathlib
import hashlib
import shutil
from threading import Thread
from datetime import datetime
from jnpr.junos import Device
from jnpr.junos.exception import ConfigLoadError, CommitError
from jnpr.junos.utils.config import Config
from time import sleep
import template_ops_conf as template_ops_conf

# default commit timeout
COMMIT_TIMEOUT = 30
from template_ops_conf import *
from template_ops_vars import *

# reduce traceback verbosity
# sys.tracebacklimit=0

if onbox:
    try:
        USER = Junos_Context["user-context"]["login-name"]
    except:
        # may happen during event-options execution (no interactive execution)
        USER = Junos_Context["user-context"]["user"]

else:
    USER = os.getlogin()

# for purposes of template-ops detection from within template
global TEMPLATE_OPS
TEMPLATE_OPS = True

PID = str(os.getpid())
script = "[{user}]{path}[{pid}]".format(
    path=os.path.abspath(sys.argv[0]), user=USER, pid=PID
)

threads = []
warnings.filterwarnings(action="ignore", module=".*paramiko.*")
template_thread_data = []

# variable for returning header from exec template
header = "default"
# variables from exec templates
result = "use global result and optionally header variable in exec() template"
# for purposes of passing non-string between templates in mprofile
result_adv = None

TEMPLATE_DATA_HEADER_DEFAULT = [["device", "template operation output"]]
# TEMPLATE_DATA_HEADER can be modified by templates
TEMPLATE_DATA_HEADER = [["device", "template operation output"]]
LIST_PROFILE_HEADER = [["#", "push profile", "comment"]]
LIST_MPROFILE_HEADER = [["#", "multi push profile", "comment"]]
LIST_TEMPLATE_HEADER = [["#", TEMPLATE_SEARCH_PATH + "/*.j2", "md5"]]
SHOW_PROFILE_HEADER = [
    [
        "profile",
        "device",
        "template-vars",
        "template",
        "input",
        "exec",
        "eph-instance:fmt",
        "archival override",
    ]
]

SHOW_MPROFILE_HEADER = [
    [
        "multi profile",
        "profile",
        "pre-delay[s]",
        "post-delay[s]",
    ]
]


def emit_info(msg, use_stdout=True, use_syslog=True, use_snmp=False):
    if use_stdout:
        print(msg)
    if onbox:
        if use_syslog:
            jcs.syslog("14", "{script} {msg}".format(script=script, msg=msg))
            # in case of jcs.syslog reliablity issues use logger instead
            # os.system("logger -p user.info {script} {msg}".format(script=script, msg=msg))
        if use_snmp:
            dev.rpc.request_snmp_spoof_trap(
                trap="jnxEventTrap",
                variable_bindings="jnxEventTrapDescr = {script}, jnxEventAvAttribute = {msg}".format(
                    script=script, msg=msg.replace(" ", "_")
                ),
            )
    elif use_syslog:
        syslog.openlog(facility=syslog.LOG_INFO)
        syslog.syslog(syslog.LOG_INFO, "{script} {msg}".format(script=script, msg=msg))


def print_help():
    """Print help"""

    if onbox:
        help_msg = """
    
  template-ops is a simple yet powerful tool for rendering and uploading Jinja2 templates,
  designed for operations with MX/PTX-SRX scale-out, but with general use-case in mind.
   
  arguments:  
  
    template-vars          pointer to variable gen function in template_ops_vars.py, {TEMPLATE_VARS_STR}  
    template               name of j2 template receiving variables from template-vars 
    input                  template seeding data, e.g., sequence number 1-n (or data enclosed in " ")
    diff-target            device name to retrieve diff between candidate and running config
    push-target            device name for config template push
    exec-target            device name for processing template as Python code 
    profile                push to multiple SRX devices using profile [profile-name|# from list]
    mprofile               multi-profile execution defined by profile [mprofile-name|# from list]
    list-profile           list push target profiles from template_ops_conf.py (any argument)
    list-mprofile          list multi-profiles from template_ops_conf.py (any argument)
    show-profile           show details of push target profile [all|profile-name|# from list]
    show-mprofile          show multi-profile details [all|mprofile-name|# from list]
    list-template          list available Jinja2 template files (any argument)
    show-template          show contents of specific template [template-name|# from list ]
    debug                  [on] enable backtraces to stdout (SYSLOG by default) 
  
  template-vars, input and template must be used together, push/diff-target is optional
  profile and optionally input (to override config profile) are used as the only arguments for bulk operation
  
  The idea is to preview the template first in a form of set commands:
  
  > op template-ops template-vars srx4600 template srx4600-local-01 input 10
  
  Then optionally diff the configuration against running config:
  
  > op template-ops template-vars srx4600 template srx4600-local-01 input 10 diff-target srx-10
    
  Finaly push to single device and validate:
  
  > op template-ops template-vars srx4600 template srx4600-local-01 input 10 push-target srx-10
  
  where srx-10 is defined along with profile(s) below in template_ops_conf.py
  
  Finally, to upload proven template to multiple devices:
  
  > op template-ops profile p1 
    
  Templates are located in {TEMPLATE_SEARCH_PATH} folder. 
  
  Both profiles and templates can be listed and viewed using corresponding list and show commands.
  
  version {ver}

        """.format(
            TEMPLATE_VARS_STR=TEMPLATE_VARS_STR,
            TEMPLATE_SEARCH_PATH=TEMPLATE_SEARCH_PATH,
            ver=ver,
        )
    else:
        help_msg = """
    
  template-ops is a simple yet powerful tool for rendering and uploading Jinja2 templates,
  designed for operations with MX/PTX-SRX scale-out, but with general use-case in mind.
   
  arguments:  
  
    --template-vars          pointer to variable gen function in template_ops_vars.py, {TEMPLATE_VARS_STR}  
    --template               name of j2 template receiving variables from --template-vars 
    --input                  template seeding data, e.g., sequence number 1-n (or data enclosed in " ")
    --diff-target            device name to retrieve diff between candidate and running config
    --push-target            device name for config template push
    --exec-target            device name for processing template as Python code
    --profile                push to multiple SRX devices using profile [profile-name|# from list]
    --mprofile               multi-profile execution defined by profile [mprofile-name|# from list]
    --list-profile           list push target profiles from template_ops_conf.py
    --list-mprofile          list multi-profiles from template_ops_conf.py 
    --show-profile           show details of push target profile [all|profile-name|# from list]
    --show-mprofile          show multi-profile details [all|mprofile-name|# from list]
    --list-template          list available Jinja2 template files
    --show-template          show contents of specific template [template-name|# from list ]
    --debug                  [on] enable backtraces to stdout (SYSLOG by default) 
  
  template-vars, input and template must be used together, push/diff-target is optional
  profile and optionally input (to override config profile) are used as the only arguments for bulk operation
  
  The idea is to preview the template first in a form of set commands:
    
    template-ops --template-vars srx4600 --template srx4600-local-01 --input 10
  
  Then optionally diff the configuration against running config:
  
    template-ops --template-vars srx4600 --template srx4600-local-01 --input 10 --diff-target srx-10
    
  Finaly push to single device and validate:
  
    template-ops --template-vars srx4600 --template srx4600-local-01 --input 10 --push-target srx-10
  
  where srx-10 is defined along with profile(s) below in template_ops_conf.py
  
  Finally, to upload proven template to multiple devices:
  
    template-ops --profile p1 
    
  Templates are located in {TEMPLATE_SEARCH_PATH} folder. 
  
  Both profiles and templates can be listed and viewed using corresponding list and show commands.

  version {ver}

        """.format(
            TEMPLATE_VARS_STR=TEMPLATE_VARS_STR,
            TEMPLATE_SEARCH_PATH=TEMPLATE_SEARCH_PATH,
            ver=ver,
        )

    print(help_msg)


def file_md5(path):
    try:
        with open(path, "rb") as f:
            file_hash = hashlib.md5()
            chunk = f.read(8192)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(8192)

        return file_hash.hexdigest()
    except Exception:
        traceback_msg = str(traceback.format_exc())
        emit_info(
            "error calculating md5, traceback: {traceback_msg}".format(
                traceback_msg=traceback_msg
            ),
            debug,
        )
        return "error calculating md5"


def parse_args():
    """Parse arguments"""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--template")
    parser.add_argument("--template-vars", dest="template_vars")
    parser.add_argument("--input")
    parser.add_argument("--push-target", dest="push_target")
    parser.add_argument("--exec-target", dest="exec_target")
    parser.add_argument("--diff-target", dest="diff_target")
    parser.add_argument("--profile", dest="profile")
    parser.add_argument("--mprofile", dest="mprofile")
    parser.add_argument("--debug", default=False)
    parser.add_argument("--list-profile", nargs="?", const="all", dest="list_profile")
    parser.add_argument("--list-mprofile", nargs="?", const="all", dest="list_mprofile")
    parser.add_argument("--list-template", nargs="?", const="all", dest="list_template")
    parser.add_argument("--show-profile", dest="show_profile")
    parser.add_argument("--show-mprofile", dest="show_mprofile")
    parser.add_argument("--show-template", dest="show_template")
    parser.add_argument("--eph-instance", dest="eph_instance")
    parsed_args = parser.parse_args()
    return parsed_args


def list_profile(arg):
    try:
        table_width = 95
        print("-" * table_width)
        for row in LIST_PROFILE_HEADER:
            print("| {:>3} | {:^21} |  {:^60} |".format(*row))
            print("-" * table_width)

        for row_nr, (profile, profile_detail) in enumerate(
            template_ops_conf.push_profiles.items(), start=1
        ):
            print(
                "| {:>3} | {:>21} |  {:>60} |".format(
                    row_nr, profile, profile_detail["comment"][0]
                )
            )
            print("-" * table_width)
    except Exception:
        traceback_msg = str(traceback.format_exc())
        emit_info(
            "error listing profiles, traceback: {traceback_msg}".format(
                traceback_msg=traceback_msg
            ),
            debug,
        )
        emit_info("error listing profiles, use debug on/see log", not debug, not debug)


def show_profile(arg):
    by_index = True
    try:
        if int(arg) > 0:
            index = int(arg)
        for row_nr, (profile, profile_detail) in enumerate(
            template_ops_conf.push_profiles.items(), start=1
        ):
            if index == row_nr:
                arg_profile = profile
                break
    except:
        by_index = False
        arg_profile = arg
    finally:
        try:
            if arg_profile in template_ops_conf.push_profiles or arg_profile == "all":
                profile_data = []
                for profile in template_ops_conf.push_profiles:
                    if profile == arg_profile or arg_profile == "all":
                        profile_dict = getattr(template_ops_conf, profile)
                        for profile_dev in profile_dict.keys():
                            # merge with default profile, pre-python 3.9 style
                            if "default" in profile_dict.keys():
                                profile_dev_detail = {
                                    **profile_dict["default"],
                                    **profile_dict[profile_dev],
                                }
                            else:
                                profile_dev_detail = profile_dict[profile_dev]
                            # build a list with profile settings for printing
                            if not "default" in profile_dev:
                                profile_data.append(
                                    [
                                        profile,
                                        profile_dev,
                                        profile_dev_detail["template_vars"][0],
                                        profile_dev_detail["template"][0],
                                        profile_dev_detail["input"][0],
                                        # Y if explicit True, N for explicit False and no setting
                                        "Y"
                                        if bool(
                                            profile_dev_detail.get("exec", [False])[0]
                                        )
                                        else "N",
                                        # eph_instance:format if set, N when eph_instance is not set
                                        f"{profile_dev_detail.get('eph_inst')[0]}:{profile_dev_detail.get('eph_inst')[1]}"
                                        if bool(
                                            profile_dev_detail.get("eph_inst", [False])[
                                                0
                                            ]
                                        )
                                        else "N",
                                        # save rendered, j2
                                        f"rendered:{'Y' if profile_dev_detail.get('save_rendered_j2')[0] else 'N'}, J2:{'Y' if profile_dev_detail.get('save_rendered_j2')[1] else 'N'}"
                                        if profile_dev_detail.get("save_rendered_j2")
                                        else "N",
                                    ]
                                )

                table_width = 168

                for row in SHOW_PROFILE_HEADER:
                    if row[0] != "":
                        print("-" * table_width)
                    print(
                        "| {:^21} | {:^13} | {:^15} | {:^26} | {:^25} | {:>4} | {:^20} | {:^19} |".format(
                            *row
                        )
                    )
                prev_profile = ""
                for row in profile_data:
                    if row[0] == prev_profile:
                        row[0] = ""
                    if row[0] != "":
                        prev_profile = row[0]
                        print("-" * table_width)
                    print(
                        "| {:>21} | {:>13} | {:>15} | {:>26} | {:>25} | {:>4} | {:>20} | {:>19} |".format(
                            *row
                        )
                    )
                print("-" * table_width)

            else:
                emit_info("Profile doesn't exist")
        except Exception:
            traceback_msg = str(traceback.format_exc())
            emit_info(
                "show-profile error, traceback: {traceback_msg}".format(
                    traceback_msg=traceback_msg
                ),
                debug,
            )
            emit_info("show-profile error, use debug on/see log", not debug, not debug)


def show_mprofile(arg):
    by_index = True
    try:
        if int(arg) > 0:
            index = int(arg)
        for row_nr, (mprofile, mprofile_detail) in enumerate(
            template_ops_conf.multi_profiles.items(), start=1
        ):
            if index == row_nr:
                arg_mprofile = mprofile
                break
    except:
        by_index = False
        arg_mprofile = arg
    finally:
        try:
            if (
                arg_mprofile in template_ops_conf.multi_profiles
                or arg_mprofile == "all"
            ):
                mprofile_data = []
                for mprofile in template_ops_conf.multi_profiles:
                    if mprofile == arg_mprofile or arg_mprofile == "all":
                        for push_profiles in template_ops_conf.multi_profiles[mprofile][
                            "push_profiles"
                        ]:
                            for (
                                push_profile,
                                push_profile_settings,
                            ) in push_profiles.items():
                                # build a list with mprofile settings for printing
                                mprofile_data.append(
                                    [
                                        mprofile,
                                        push_profile,
                                        # " " if 0 or empty, value for non-0 setting
                                        ""
                                        if not bool(
                                            push_profile_settings.get("pre-delay", 0)
                                        )
                                        else push_profile_settings.get("pre-delay"),
                                        # " " if 0 or empty, value for non-0 setting
                                        ""
                                        if not bool(
                                            push_profile_settings.get("post-delay", 0)
                                        )
                                        else push_profile_settings.get("post-delay"),
                                    ]
                                )

                table_width = 83

                for row in SHOW_MPROFILE_HEADER:
                    if row[0] != "":
                        print("-" * table_width)
                    print("| {:^21} | {:^21} | {:^14} | {:^14} | ".format(*row))
                prev_mprofile = ""
                for row in mprofile_data:
                    if row[0] == prev_mprofile:
                        row[0] = ""
                    if row[0] != "":
                        prev_mprofile = row[0]
                        print("-" * table_width)
                    print("| {:>21} | {:>21} | {:>14} | {:>14} |".format(*row))
                print("-" * table_width)

            else:
                emit_info("Multi-profile doesn't exist")

        except Exception:
            traceback_msg = str(traceback.format_exc())
            emit_info(
                "show-profile error, traceback: {traceback_msg}".format(
                    traceback_msg=traceback_msg
                ),
                debug,
            )
            emit_info("show-mprofile error, use debug on/see log", not debug, not debug)


def list_mprofile(arg):
    try:
        table_width = 95
        print("-" * table_width)
        for row in LIST_MPROFILE_HEADER:
            print("| {:>3} | {:^21} |  {:^60} |".format(*row))
            print("-" * table_width)

        for row_nr, (mprofile, mprofile_detail) in enumerate(
            template_ops_conf.multi_profiles.items(), start=1
        ):
            print(
                "| {:>3} | {:>21} |  {:>60} |".format(
                    row_nr, mprofile, mprofile_detail["comment"][0]
                )
            )
            print("-" * table_width)
    except Exception:
        traceback_msg = str(traceback.format_exc())
        emit_info(
            "error listing multi profiles, traceback: {traceback_msg}".format(
                traceback_msg=traceback_msg
            ),
            debug,
        )
        emit_info(
            "error listing multi profiles, use debug on/see log", not debug, not debug
        )


def list_template(return_only):
    try:
        template_files = [f for f in pathlib.Path(TEMPLATE_SEARCH_PATH).glob("*.j2")]
        template_files.sort()
        if not return_only:
            table_width = 87
            print("-" * table_width)
            for row in LIST_TEMPLATE_HEADER:
                print("| {:>3} | {:^40} | {:^34} |".format(*row))
                print("-" * table_width)

            for row_nr, row in enumerate(template_files, start=1):
                print(
                    "| {:>3} | {:>40} | {:>34} |".format(
                        row_nr, str(row.stem), file_md5(row)
                    )
                )
                print("-" * table_width)
        # show-template use
        else:
            return template_files
    except Exception:
        traceback_msg = str(traceback.format_exc())
        emit_info(
            "error listing templates, traceback: {traceback_msg}".format(
                traceback_msg=traceback_msg
            ),
            debug,
        )
        emit_info("Error listing templates, use debug on/see log", not debug, not debug)


def show_template(arg):
    by_index = True
    templates_path_file = list_template(True)
    templates_file = [template.stem for template in templates_path_file]
    try:
        if int(arg) > 0:
            index = int(arg) - 1
        arg_template = templates_file[index]
    except:
        by_index = False
        arg_template = arg
    finally:
        if not by_index and arg_template in templates_file:
            index = templates_file.index(arg_template)
        try:
            with open(templates_path_file[index], "r") as f:
                print(
                    "#\n####################################### BEGIN {} #######################################\n#".format(
                        templates_file[index]
                    )
                )
                print(f.read())
                print(
                    "#\n####################################### END  {} ########################################\n#".format(
                        templates_file[index]
                    )
                )
        except Exception:
            traceback_msg = str(traceback.format_exc())
            emit_info(
                "error opening template, traceback: {traceback_msg}".format(
                    traceback_msg=traceback_msg
                ),
                debug,
            )
            emit_info(
                "Error opening template, use debug on/see log", not debug, not debug
            )


def template_thread(parsed_args, profile_operation, profile, device="", timestamp=""):
    def eph_settings(eph_param):
        # function to set data type for load to eph, set is default, json/xml/text are loaded with overwrite = True to overcome slow delete in eph
        if eph_param == None:
            return None, "set", False

        eph_instance = eph_param[0]
        eph_conf_type = eph_param[1]
        if eph_conf_type in ["json", "xml", "text"]:
            return eph_instance, eph_conf_type, True

        return eph_instance, "set", False

    # sets eph paramaters for CLI param, it is called during profile operation too
    eph_instance, eph_conf_type, eph_load_overwrite = eph_settings(
        parsed_args.eph_instance
    )

    if parsed_args.exec_target:
        exec_template = True
    else:
        exec_template = False

    templateLoader = jinja2.FileSystemLoader(searchpath=TEMPLATE_SEARCH_PATH)
    templateEnv = jinja2.Environment(loader=templateLoader)

    diff_only = False
    init_error = False
    template_file = ""
    status = ""

    # read archival constants, setting may be overriden in profile operations
    save_exec_py_enable = SAVE_EXEC_PY_ENABLE
    save_exec_j2_enable = SAVE_EXEC_J2_ENABLE
    save_commit_cfg_enable = SAVE_COMMIT_CFG_ENABLE
    save_commit_j2_enable = SAVE_COMMIT_J2_ENABLE

    # either diff or push to single device (or set render)
    if not profile_operation:
        template_file = parsed_args.template + ".j2"
        _input = parsed_args.input
        template_vars = parsed_args.template_vars

        # diff
        if parsed_args.diff_target:
            diff_only = True
            push_target = parsed_args.diff_target
        # push or no diff/push
        else:
            if parsed_args.push_target:
                push_target = parsed_args.push_target
            elif parsed_args.exec_target:
                push_target = parsed_args.exec_target
            # neither diff/push - set rendering
            else:
                push_target = "N/A"
    # profile operation
    else:
        try:
            push_target = device
            profile_dict = getattr(template_ops_conf, profile)

            # merge with default profile, pre-python 3.9 style
            if "default" in profile_dict.keys():
                profile_dev = {**profile_dict["default"], **profile_dict[device]}
            else:
                profile_dev = profile_dict[device]

            template_file = profile_dev["template"][0] + ".j2"
            template_vars = profile_dev["template_vars"][0]
            # profile input override
            if parsed_args.input:
                _input = parsed_args.input
            else:
                _input = profile_dev["input"][0]

            exec_template = True if bool(profile_dev.get("exec", [False])[0]) else False
            eph_instance, eph_conf_type, eph_load_overwrite = eph_settings(
                profile_dev.get("eph_inst", None)
            )

            # override template render and j2 save default archival settings
            if "save_rendered_j2" in profile_dev.keys():
                save_exec_py_enable = profile_dev.get("save_rendered_j2")[0]
                save_exec_j2_enable = profile_dev.get("save_rendered_j2")[1]
                save_commit_cfg_enable = save_exec_py_enable
                save_commit_j2_enable = save_exec_j2_enable

        except Exception:
            init_error = True
            traceback_msg = str(traceback.format_exc())
            emit_info(
                "error reading device profile, traceback: {traceback_msg}".format(
                    traceback_msg=traceback_msg
                ),
                debug,
            )
            status = "Error reading device profile, use debug on/see log"
            template_thread_data.append([push_target, status])

    template_abs = TEMPLATE_SEARCH_PATH + "/" + template_file
    # missing/inaccesible file for both single/profile operation
    if not os.path.isfile(template_abs) and not init_error:
        status = (
            "Error opening template file {template_file}, file doesn't exist".format(
                template_file=template_file.replace(".j2", "")
            )
        )
        template_thread_data.append([push_target, status])
        emit_info(status, False)

    # proceed if there is no init error recorded above
    elif not init_error:
        try:
            template = templateEnv.get_template(template_file)
            template_md5 = file_md5(template_abs)
            template_vars_for_render = template_vars_get(template_vars, _input)
            template_output = template.render(template_vars_for_render)
        except Exception:
            traceback_msg = str(traceback.format_exc())
            emit_info(
                "{push_target} error rendering template {template_file}, traceback: {traceback_msg}".format(
                    push_target=push_target,
                    template_file=template_file,
                    traceback_msg=traceback_msg,
                ),
                debug,
            )
            status = (
                "Error rendering template {template_file}, use debug on/see log".format(
                    template_file=template_file.replace(".j2", "")
                )
            )
            template_thread_data.append([push_target, status])
        # no exception during template rendering
        else:
            # determine if local on-box mode without SSH
            if push_target in ["local", "localhost"]:
                local_onbox_ops = True
            else:
                local_onbox_ops = False

            # diff/push(includes exec) operation (not set rendering) to eligible template vars
            if push_target != "N/A" and template_vars in DIFF_PUSH_ELIGIBLE_LIST:
                try:
                    if not local_onbox_ops:
                        # merge with default profile, pre-python 3.9 style
                        if "default" in template_ops_conf.auth_profiles:
                            netconf_param = {
                                **template_ops_conf.auth_profiles["default"],
                                **template_ops_conf.auth_profiles[push_target],
                            }
                        else:
                            netconf_param = template_ops_conf.auth_profiles[push_target]

                except Exception:
                    traceback_msg = str(traceback.format_exc())
                    emit_info(
                        "{push_target} netconf config lookup error {template_file}, traceback: {traceback_msg}".format(
                            push_target=push_target,
                            template_file=template_abs,
                            traceback_msg=traceback_msg,
                        ),
                        debug,
                    )
                    template_thread_data.append(
                        [push_target, "netconf config lookup error"]
                    )
                # no netconf lookup error
                else:
                    # localhost operation, no SSH
                    if local_onbox_ops:
                        dev = Device(gather_facts=False)
                    # SSH operation
                    else:
                        dev = Device(
                            user=netconf_param["user"][0],
                            host=netconf_param["host"][0],
                            port=netconf_param["port"][0],
                            ssh_private_key_file=netconf_param["ssh_key"][0],
                            gather_facts=False,
                        )
                    try:
                        # probe doesn't work with local operation, only SSH
                        if local_onbox_ops:
                            dev.open()
                        else:
                            dev.open(auto_probe=2)
                    except Exception:
                        traceback_msg = str(traceback.format_exc())
                        emit_info(
                            "{push_target} error connecting to the device, {traceback_msg}".format(
                                push_target=push_target,
                                traceback_msg=traceback_msg,
                            ),
                            debug,
                        )

                        template_thread_data.append(
                            [push_target, "error connecting to the device"]
                        )
                    # device connection OK
                    else:
                        # config operation, no exec()
                        if not exec_template:
                            if not diff_only:
                                emit_info(
                                    "{push_target} template push start {template_file} (md5: {md5})".format(
                                        push_target=push_target,
                                        template_file=template_abs,
                                        md5=template_md5,
                                    ),
                                    False,
                                )
                            else:
                                emit_info(
                                    "{push_target} template diff start {template_file} (md5: {md5})".format(
                                        push_target=push_target,
                                        template_file=template_abs,
                                        md5=template_md5,
                                    ),
                                    False,
                                )

                            set_cmd = template_output
                            no_exception = False
                            removed_del_cmds = False
                            try:

                                def load_or_diff(eph=False):
                                    if eph:
                                        # overwrite with json/xml/text
                                        cu.load(
                                            set_cmd,
                                            format=eph_conf_type,
                                            overwrite=eph_load_overwrite,
                                        )
                                    else:
                                        cu.load(set_cmd, format="set")
                                    # can't happen with ephemeral, parameter check prevents that
                                    if diff_only:
                                        diff = cu.diff()
                                        cu.rollback()
                                        return diff
                                    else:
                                        cu.commit(timeout=COMMIT_TIMEOUT)

                                if eph_instance is not None:
                                    with Config(
                                        dev,
                                        mode="ephemeral",
                                        ephemeral_instance=eph_instance,
                                    ) as cu:
                                        diff = load_or_diff(eph=True)
                                else:
                                    with Config(dev) as cu:
                                        diff = load_or_diff()

                            # handle diff/push differently by removing delete which may not be present, if configured
                            except (ConfigLoadError, CommitError):
                                if eph_instance is not None:
                                    cu.rollback()
                                # check if removing delete commands is configured for diff/push re-try
                                if REMOVE_DEL_CMDS_DURING_PUSH_DIFF_ERR_ENABLE:
                                    try:
                                        # items for delete might not be present, remove and commit without
                                        # ^delete pattern is not used as that doesn't apply for multiple lines!!
                                        set_cmd = re.sub(r"delete\ .*\n", "", set_cmd)
                                        # unless repeated re-open of ephemeral, commit is to regular config
                                        # TBD re-factor repeated code, handle exception in load_or_diff function
                                        if eph_instance is not None:
                                            with Config(
                                                dev,
                                                mode="ephemeral",
                                                ephemeral_instance=eph_instance,
                                            ) as cu:
                                                diff = load_or_diff(eph=True)
                                        else:
                                            with Config(dev) as cu:
                                                diff = load_or_diff()
                                        # for purposes of console and log message
                                        removed_del_cmds = True
                                    # neither regular/without delete push/diff passed
                                    except Exception:
                                        cu.rollback()
                                        traceback_msg = str(traceback.format_exc())
                                        if diff_only:
                                            template_thread_data.append(
                                                [
                                                    push_target,
                                                    "error during template diff (-del cmds), rollback..., use debug on/see log",
                                                ]
                                            )
                                            emit_info(
                                                "{push_target} error during template diff (-del cmds), rollback..., {template_file} (md5: {md5}), traceback: {traceback_msg}".format(
                                                    push_target=push_target,
                                                    template_file=template_abs,
                                                    md5=template_md5,
                                                    traceback_msg=traceback_msg,
                                                ),
                                                debug,
                                            )
                                        else:
                                            template_thread_data.append(
                                                [
                                                    push_target,
                                                    "error during template commit (-del cmds), rollback..., use debug on/see log",
                                                ]
                                            )
                                            emit_info(
                                                "{push_target} error during template commit (-del cmds), rollback..., {template_file} (md5: {md5}), traceback: {traceback_msg}".format(
                                                    push_target=push_target,
                                                    template_file=template_abs,
                                                    md5=template_md5,
                                                    traceback_msg=traceback_msg,
                                                ),
                                                debug,
                                            )
                                    # no exception during push/diff without del cmds
                                    else:
                                        no_exception = True
                                # exception and REMOVE_DEL_CMDS_DURING_PUSH_DIFF_ERR_ENABLE = 0
                                else:
                                    traceback_msg = str(traceback.format_exc())
                                    if diff_only:
                                        template_thread_data.append(
                                            [
                                                push_target,
                                                "error during template diff, rollback..., use debug on/see log",
                                            ]
                                        )
                                        emit_info(
                                            "{push_target} error during template diff, rollback..., {template_file} (md5: {md5}), traceback: {traceback_msg}".format(
                                                push_target=push_target,
                                                template_file=template_abs,
                                                md5=template_md5,
                                                traceback_msg=traceback_msg,
                                            ),
                                            debug,
                                        )
                                    else:
                                        template_thread_data.append(
                                            [
                                                push_target,
                                                "error during template commit, rollback..., use debug on/see log",
                                            ]
                                        )

                                        emit_info(
                                            "{push_target} error during template commit, rollback..., {template_file} (md5: {md5}), traceback: {traceback_msg}".format(
                                                push_target=push_target,
                                                template_file=template_abs,
                                                md5=template_md5,
                                                traceback_msg=traceback_msg,
                                            ),
                                            debug,
                                        )

                            # no exception during regular push/diff
                            else:
                                no_exception = True

                            if no_exception:
                                # log if there was diff
                                if diff_only and not (diff is None):
                                    template_thread_data.append(["diff", diff])
                                    emit_info(
                                        "{push_target} diff exist between candidate and current config {template_file} (md5: {md5})".format(
                                            push_target=push_target,
                                            template_file=template_abs,
                                            md5=template_md5,
                                        ),
                                        False,
                                    )
                                # log if there was no diff
                                elif diff_only:
                                    if removed_del_cmds:
                                        template_thread_data.append(
                                            [
                                                push_target,
                                                "No diff between candidate and current config (after removing delete cmds)",
                                            ]
                                        )
                                        emit_info(
                                            "{push_target} no diff between candidate and current config (after removing delete cmds) {template_file} (md5: {md5})".format(
                                                push_target=push_target,
                                                template_file=template_abs,
                                                md5=template_md5,
                                            ),
                                            False,
                                        )
                                    # if no del_cmds got removed
                                    else:
                                        template_thread_data.append(
                                            [
                                                push_target,
                                                "No diff between candidate and current config",
                                            ]
                                        )
                                        emit_info(
                                            "{push_target} no diff between candidate and current config {template_file} (md5: {md5})".format(
                                                push_target=push_target,
                                                template_file=template_abs,
                                                md5=template_md5,
                                            ),
                                            False,
                                        )
                                # archive operation for .j2 and/or set cmds during push
                                else:
                                    try:
                                        archive_msg = ""
                                        template_file = template_file.replace(".j2", "")
                                        if save_commit_j2_enable:
                                            shutil.copy(
                                                template_abs,
                                                SAVE_PATH_COMMIT_J2
                                                + "/"
                                                + timestamp
                                                + "__"
                                                + template_file
                                                + "__"
                                                + push_target
                                                + ".j2",
                                            )
                                            archive_msg = ", j2 template archived"
                                        if save_commit_cfg_enable:
                                            save_commit_set_file = (
                                                SAVE_PATH_COMMIT_CFG
                                                + "/"
                                                + timestamp
                                                + "__"
                                                + template_file
                                                + "__"
                                                + push_target
                                                + ".set"
                                            )
                                            with open(save_commit_set_file, "w") as f:
                                                f.writelines(set_cmd)
                                            archive_msg = ", set-cmd archived"

                                        if (
                                            save_commit_j2_enable == 1
                                            and save_commit_cfg_enable == 1
                                        ):
                                            archive_msg = ", j2+set-cmd archived"

                                    except Exception:
                                        traceback_msg = str(traceback.format_exc())
                                        emit_info(
                                            "error archiving j2 template or set commands during commit: {traceback_msg}".format(
                                                traceback_msg=traceback_msg
                                            ),
                                            debug,
                                        )
                                        archive_msg = ", archive error, see log"

                                    # delete commands removed due to exception, commit completed
                                    if removed_del_cmds:
                                        status = "{template_file} template commit completed (-del cmds){archive_msg}".format(
                                            template_file=template_file,
                                            archive_msg=archive_msg,
                                        )
                                        template_thread_data.append(
                                            [push_target, status]
                                        )
                                        emit_info(
                                            "{push_target} commit completed (-del cmds) {template_file} (md5: {md5})".format(
                                                push_target=push_target,
                                                template_file=template_abs,
                                                md5=template_md5,
                                            ),
                                            False,
                                        )
                                    # no delete commands were removed due to exception, commit completed
                                    else:
                                        status = "{template_file} template commit completed{archive_msg}".format(
                                            template_file=template_file,
                                            archive_msg=archive_msg,
                                        )
                                        template_thread_data.append(
                                            [push_target, status]
                                        )
                                        emit_info(
                                            "{push_target} commit completed {template_file} (md5: {md5})".format(
                                                push_target=push_target,
                                                template_file=template_abs,
                                                md5=template_md5,
                                            ),
                                            False,
                                        )

                        # template exec() operation
                        else:
                            if TEMPLATE_EXEC_ENABLE:
                                emit_info(
                                    "{push_target} code execution start {template_file} (md5: {md5})".format(
                                        push_target=push_target,
                                        template_file=template_abs,
                                        md5=template_md5,
                                    ),
                                    False,
                                )

                                try:
                                    exec(template_output)
                                    # template return data for passing between mprofiles
                                    if result:
                                        if result_adv:
                                            template_thread_data.append(
                                                [push_target, result, result_adv]
                                            )
                                        else:
                                            template_thread_data.append(
                                                [push_target, result]
                                            )

                                except Exception:
                                    traceback_msg = str(traceback.format_exc())
                                    emit_info(
                                        "{push_target} error executing code {template_file}, traceback: {traceback_msg}".format(
                                            push_target=push_target,
                                            template_file=template_file,
                                            traceback_msg=traceback_msg,
                                        ),
                                        debug,
                                    )
                                    status = "Error executing code {template_file}, use debug on/see log".format(
                                        template_file=template_file.replace(".j2", "")
                                    )
                                    template_thread_data.append([push_target, status])

                                # archive code j2 and/or resulting py
                                else:
                                    try:
                                        archive_msg = ""
                                        template_file = template_file.replace(".j2", "")
                                        if save_exec_j2_enable:
                                            shutil.copy(
                                                template_abs,
                                                SAVE_PATH_EXEC_J2
                                                + "/"
                                                + timestamp
                                                + "__"
                                                + template_file
                                                + "__"
                                                + push_target
                                                + ".py.j2",
                                            )
                                            archive_msg = ", j2 exec template archived"
                                        if save_exec_py_enable:
                                            save_commit_set_file = (
                                                SAVE_PATH_EXEC_PY
                                                + "/"
                                                + timestamp
                                                + "__"
                                                + template_file
                                                + "__"
                                                + push_target
                                                + ".py"
                                            )
                                            with open(save_commit_set_file, "w") as f:
                                                f.writelines(template_output)
                                            archive_msg = ", exec code archived"

                                        if (
                                            save_exec_j2_enable == 1
                                            and save_exec_py_enable == 1
                                        ):
                                            archive_msg = ", exec j2+code archived"

                                        emit_info(
                                            "{push_target} template {template_file}{archive_msg} ".format(
                                                push_target=push_target,
                                                template_file=template_file,
                                                archive_msg=archive_msg,
                                            ),
                                            False,
                                        )

                                    except Exception:
                                        traceback_msg = str(traceback.format_exc())
                                        emit_info(
                                            "error archiving j2 exec template and/or exec code during commit: {traceback_msg}".format(
                                                traceback_msg=traceback_msg
                                            ),
                                            debug,
                                        )
                            # template exec not allowed
                            else:
                                emit_info(
                                    "{push_target} template execution not enabled".format(
                                        push_target=push_target,
                                    ),
                                    False,
                                )
                                status = "template execution not enabled"
                                template_thread_data.append([push_target, status])
                        # close dev
                        try:
                            dev.close()
                        except Exception:
                            traceback_msg = str(traceback.format_exc())
                            emit_info(
                                "{push_target} error closing device, {traceback_msg}".format(
                                    push_target=push_target,
                                    traceback_msg=traceback_msg,
                                ),
                                debug,
                            )
            # only print rendered set cmds
            else:
                print(template_output)


def print_results():
    if len(template_thread_data) > 0:
        # diff
        if template_thread_data[0][0] == "diff":
            print(template_thread_data[0][1])
        # process non-diff
        else:
            # print only if the result is not dict/list and non-empty.
            print_data = [
                data
                for data in template_thread_data
                if (type(data[1]) not in [dict, list]) and data[1]
            ]

            # look at the last recorded data if multiline
            if (
                len(template_thread_data[len(template_thread_data) - 1][1].splitlines())
                > 1
            ):
                multi_line = True
            else:
                multi_line = False

            print_data.sort()
            # if template returns custom header, or None to avoid printing, else default
            print_header = True
            table_width = 119
            if header not in [None, "default"]:
                TEMPLATE_DATA_HEADER[0][1] = header
                table_width = 19 + len(header)
            elif header in ["default"]:
                TEMPLATE_DATA_HEADER[0][1] = TEMPLATE_DATA_HEADER_DEFAULT[0][1]
            elif header is None:
                print_header = False

            # multi-line exec operation formatting
            if multi_line:
                if print_header:
                    print("|" + "-" * table_width)
                    for row in TEMPLATE_DATA_HEADER:
                        print("| {:^12} | {:^100} | ".format(*row))
                        print("|" + "-" * table_width)

                for row in print_data:
                    print("|# {:<12} {:>100}  ".format(*row))
                    print("|" + "-" * table_width)
            # no exec multi-line or regular template output
            else:
                # when custom header is set adjust table width based on result
                if header not in ["default"]:
                    if print_header:
                        print("-" * table_width)
                        for row in TEMPLATE_DATA_HEADER:
                            print("| {:^12} | {} | ".format(row[0], row[1]))
                            print("-" * table_width)
                    for row in print_data:
                        if len(row[1]) > 0:
                            # in case of error like device unreachable
                            if len(row[1]) < len(header):
                                row[1] = row[1].ljust(len(header))
                            print("| {:^12} | {} | ".format(row[0], row[1]))
                            print("-" * table_width)

                # fixed width when custom header is not used
                else:
                    if print_header:
                        print("-" * table_width)
                        for row in TEMPLATE_DATA_HEADER:
                            print("| {:^12} | {:^100} | ".format(*row))
                            print("-" * table_width)
                    for row in print_data:
                        print("| {:^12} | {:>100} | ".format(*row))
                        print("-" * table_width)


def main():
    try:
        parsed_args = parse_args()

        global debug
        debug = parsed_args.debug
        if debug in ["yes", "1", "enable", "on"]:
            debug = True
        # bad option for single device or multi
        if not (
            parsed_args.template and parsed_args.template_vars and parsed_args.input
        ) and not (
            parsed_args.profile
            or parsed_args.mprofile
            or parsed_args.show_profile
            or parsed_args.show_mprofile
            or parsed_args.show_template
            or parsed_args.list_profile
            or parsed_args.list_mprofile
            or parsed_args.list_template
        ):
            print_help()
        # exclusive options
        elif (
            [parsed_args.push_target, parsed_args.diff_target, parsed_args.exec_target]
        ).count(None) < 2:
            print_help()

        elif parsed_args.eph_instance and (
            parsed_args.diff_target or parsed_args.exec_target
        ):
            print_help()

        elif parsed_args.list_profile:
            list_profile(parsed_args.list_profile)

        elif parsed_args.list_mprofile:
            list_mprofile(parsed_args.list_mprofile)

        elif parsed_args.list_template:
            list_template(False)

        elif parsed_args.show_profile:
            show_profile(parsed_args.show_profile)

        elif parsed_args.show_mprofile:
            show_mprofile(parsed_args.show_mprofile)

        elif parsed_args.show_template:
            show_template(parsed_args.show_template)
        # single device operation
        elif parsed_args.template and parsed_args.template_vars and parsed_args.input:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            template_thread(parsed_args, False, parsed_args.profile, None, timestamp)
            print_results()
        # multi device operations
        elif (parsed_args.profile or parsed_args.mprofile) and not (
            parsed_args.template or parsed_args.template_vars
        ):
            by_index = True
            try:

                def retrieve_profile(data_set, profile):
                    if int(profile) > 0:
                        index = int(profile)
                    for row_nr, (profile, profile_detail) in enumerate(
                        data_set.items(), start=1
                    ):
                        if index == row_nr:
                            return profile

                if parsed_args.profile:
                    parsed_args.profile = retrieve_profile(
                        template_ops_conf.push_profiles, parsed_args.profile
                    )
                else:
                    parsed_args.mprofile = retrieve_profile(
                        template_ops_conf.multi_profiles, parsed_args.mprofile
                    )

            except:
                by_index = False
            finally:
                run_profiles = []
                # multi profile
                if parsed_args.mprofile:
                    if parsed_args.mprofile in template_ops_conf.multi_profiles:
                        for push_profile in multi_profiles[parsed_args.mprofile][
                            "push_profiles"
                        ]:
                            # line up profiles in a list, as if they were dict keys by profile name, no option to repeat
                            run_profiles.append(push_profile)
                    else:
                        emit_info(
                            "No matching multi profile {multi_profile} ".format(
                                multi_profile=parsed_args.mprofile,
                            ),
                            True,
                        )

                # single profile
                else:
                    if parsed_args.profile in template_ops_conf.push_profiles:
                        # honor the same data structure as with multi-profile
                        run_profiles.append({parsed_args.profile: {}})
                    else:
                        emit_info(
                            "No matching profile {multi_profile} ".format(
                                multi_profile=parsed_args.profile,
                            ),
                            True,
                        )

                # common execucution for profile/mprofile
                for profile_dict in run_profiles:
                    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                    for key, value in profile_dict.items():
                        profile = key
                    profile_dev = getattr(template_ops_conf, profile)
                    if "default" in profile_dev.keys():
                        nr_profile_devices = len(profile_dev) - 1
                    else:
                        nr_profile_devices = len(profile_dev)

                    # MAX_PROFILE_DEV check
                    if nr_profile_devices > template_ops_conf.MAX_PROFILE_DEV:
                        emit_info(
                            "{profile} profile number of targets ({profile_dev}) > MAX_PROFILE_DEV ({MAX_PROFILE_DEV}) setting".format(
                                profile_dev=profile_dev,
                                MAX_PROFILE_DEV=template_ops_conf.MAX_PROFILE_DEV,
                                profile=profile,
                            ),
                            True,
                        )

                    # proceed profile size less than MAX_PROFILE_DEV
                    else:
                        # pre-pause for defined time, meant for mprofile
                        sleep(profile_dict[profile].get("pre-delay", 0))

                        for device in getattr(template_ops_conf, profile):
                            # exclude default profile
                            if not device in ["default"]:
                                thread = Thread(
                                    target=template_thread,
                                    args=(
                                        parsed_args,
                                        True,
                                        profile,
                                        device,
                                        timestamp,
                                    ),
                                )
                                threads.append(thread)
                                thread.start()

                        for thread in threads:
                            thread.join()

                        # post-pause for defined time, meant for mprofile
                        sleep(profile_dict[profile].get("post-delay", 0))

                        print_results()

                        # remove simple string output to avoid repeated print with mprofile in print_results
                        for data in template_thread_data:
                            if type(data[1]) not in [dict, list]:
                                data[1] = ""

    except Exception:
        traceback_msg = str(traceback.format_exc())
        emit_info(traceback_msg, debug)
        emit_info("Error during execution, use debug on/see log", not debug, not debug)


if __name__ == "__main__":
    main()
