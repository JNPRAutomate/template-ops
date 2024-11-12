# template-ops
template-ops is a Python script folding minimalistic framework built atop of PyEZ for human interaction with Junos devices in terms of configuration and execution of RPCs (actions, data retrieval). Running both Linux off-box and Junos/Junos-EVO on-box. Initially designed for operations in custom [MX/PTX/SRX scale-out architectures](https://community.juniper.net/blogs/karel-hendrych/2024/02/22/mx-srx-scale-out-system-bulk-junos-config-changes "MX/PTX/SRX scale-out architectures"), but totally generic meanwhile. Licensed under Apache 2.0 license. 

Details are contained in the [PDF manual](https://github.com/JNPRAutomate/template-ops/blob/main/template-ops_man_v1.pdf).

Features:
* Conduct Junos config changes from Linux off-box and on-box from Junos devices like MX/PTX by using PyEZ libraries and SSH Netconf sessions with key authentication
* Uses Jinja2 templates for rendering both configuration and Python code with RPCs
*	For configurations designed to operate in Junos groups using set commands with explicit delete as a first operation
*	Have a configuration profile(s) driven bulk configuration push 
*	Optional workflow using prototype device for validation and verification prior bulk change. The idea of prototype prior rollout comes from real-life when changes can cause unforeseen consequences. Say one or more devices in the scale-out system can be designated for testing changes including longevity test prior roll out to whole system. 
*	Preview Junos set commands for prototype device
*	Do diff of running/candidate config on prototype device 
*	Load configuration to prototype device
*	Finally conduct bulk change across multiple devices 
*	Able to operate on multiple devices using input modifier, either in configuration profile or part of CLI. For example, the devices having sequentially lined up interface IPs, next /30 prefix, BGP ASNs, etc. Tasks can be quite complex like configure using one push of a button multiple SRX MN-HA pairs
*	Multi-profile operations when pre-defined configuration/execution profiles are sequentially executed with optional passing variables in-between code execution templates. Includes optional profile pre/post delays.
*	Profiles able to mix different device types with different templates and input variable processing
*	Control what device types are eligible for configuration push and/or only for viewing rendered set commands from template (safety and operator review prior Junos load set)
*	Easy to expand by new template variables inside of the code for given device type, simple expansion for template data from external data sources (e.g., YAML)
*	Thorough logging, including template rendering and execution debug 
*	Ability to archive committed/executed templates and result of rendering for audit and roll-back purposes
*	Option to include/exclude profiles from archival operations depending on global on/off
*	Ability to operate locally Junos on-box without SSH
*	Supports Junos Ephemeral Database with set/text/XML/JSON formats for loading configurations 
*	Convenience CLIs for listing and displaying templates / profiles.
*	For code execution templates retrieving data, either use default tabular view or allow custom header and/or column formatted contents
