#!/bin/bash
mx="10.0.0.10:/var/db/scripts/op"
scp template-ops.py $mx 
scp template_ops_conf.py $mx 
scp template_ops_vars.py $mx 
scp xtemplate/* $mx/xtemplate
