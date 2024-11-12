# TEMPLATE_VARSx_LIST are referred by template_vars_get function below, update accordingly
TEMPLATE_VARS1_LIST = ["vsrx"]
TEMPLATE_VARS2_LIST = ["ptx", "mx"]
TEMPLATE_VARS3_LIST = ["exec1"]
# sample for 4th set of devices receving more complex data in input param
TEMPLATE_VARS4_LIST = ["srx_yaml1"]

# template vars listed here can be subjected to diff/push operation, else only print set commands
DIFF_PUSH_ELIGIBLE_LIST = ["mx", "vsrx", "exec1"]
# template types for print_help (does not contain the VARS3 sample above), update Junos config for context help too
TEMPLATE_VARS_STR = "[vsrx|srx4600|mx|ptx|exec1]"


def template_vars_get(template_vars_arg, _input):
    if template_vars_arg in TEMPLATE_VARS1_LIST:
        return template_vars1(_input)
    elif template_vars_arg in TEMPLATE_VARS2_LIST:
        return template_vars2(_input)
    elif template_vars_arg in TEMPLATE_VARS3_LIST:
        return template_vars3(_input)
    elif template_vars_arg in TEMPLATE_VARS4_LIST:
        return template_vars4(_input)
    else:
        raise ValueError("UNKNOWN device-type")


def template_vars1(_input):
    # vsrx template variable generator
    seq = int(_input)
    aut_sys = 65000 + seq
    template_vars = {
        "seq": str(seq),
        "aut_sys": str(aut_sys),
    }
    return template_vars


def template_vars2(_input):
    # ptx/mx template variable generator
    trust_int_list = [2, 4, 6, 8, 10, 12, 14, 16]
    seq = int(_input)
    trust_int = trust_int_list[seq - 1]
    untrust_int = trust_int + 1
    aut_sys = 65000 + seq

    template_vars = {
        "seq": str(seq),
        "seq_0x": str(seq).zfill(2),
        "aut_sys": str(aut_sys),
        "trust_int": str(trust_int),
        "untrust_int": str(untrust_int),
    }
    return template_vars


def template_vars3(_input):
    # sessions template input generator
    template_vars = {
        "ip": str(_input),
    }
    return template_vars


def template_vars4(_input):
    import yaml
    with open(_input, 'r') as file:
      data = yaml.safe_load(file)

    template_vars = {
        "list1": data['list1']
    }
    return template_vars


def template_vars5(_input):
    # sample method to split input "x, y" into list
    input_list = _input.split(",")
    return template_vars
