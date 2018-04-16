__author__ = 'Hanspeter Höschle <hanspeter.hoeschle@energyville.be>'
__date__ = "16/04/2018"
import subprocess
import sys

import gams
import pandas as pd

from .gams_add_on_exception import GamsAddOnException


def gdx_to_df(gdx_file, symbol, **kwargs):
    ws = gams.GamsWorkspace()
    db = ws.add_database_from_gdx(gdx_file)
    s = db.get_symbol(symbol)
    gams_type = "L"
    fillna = 0.0
    if kwargs is not None:
        if "fillna" in kwargs.keys():
            fillna = kwargs["fillna"]
        if "gams_type" in kwargs.keys():
            gams_type = kwargs["gams_type"]

    if type(s) in [gams.GamsVariable, gams.GamsEquation]:
        return __gdx_to_df_var_equ(s, gams_type, fillna)
    elif type(s) == gams.GamsParameter:
        return __gdx_to_df_par(s, fillna)
    elif type(s) == gams.GamsSet:
        return __gdx_to_df_set(s)
    else:
        exit("ERROR: NOT YET IMPLEMENTED for %s" % type(s))


def __gdx_to_df_var_equ(var, gams_type="L", fillna=0.0):
    index_cols = []
    index_names = []
    if var.domains == []:
        return __gdx_to_df_scalar(var, gams_type)
    for domain in var.domains:
        if type(domain) == gams.GamsSet:
            index_cols.append([ss.keys[0] for ss in domain])
            index_names.append(domain.name)
        else:
            index_cols.append(["PLACEHOLDER"])
            index_names.append("*")
    index = pd.MultiIndex.from_product(index_cols)
    df = pd.DataFrame(None, index=index, columns=[var.name])
    df.index.names = index_names
    if len(df.index.names) > 1 and (
            any([n == "*" for n in df.index.names]) or any([n == None for n in df.index.names])):
        df.index.names = ["Dim%d" % d for d in range(1, len(df.index.names) + 1)]

    if gams_type.upper() == "L":
        for value in var:
            df.loc[tuple(value.keys), var.name] = value.level
    elif gams_type.upper() == "M":
        for value in var:
            df.loc[tuple(value.keys), var.name] = value.marginal
    elif gams_type.upper() == "UP":
        for value in var:
            df.loc[tuple(value.keys), var.name] = value.upper
    elif gams_type.upper() == "LO":
        for value in var:
            df.loc[tuple(value.keys), var.name] = value.lower
    elif gams_type.upper() == "SCALE":
        for value in var:
            df.loc[tuple(value.keys), var.name] = value.scale
    else:
        raise GamsAddOnException("gams_type %s not defined" % gams_type)

    df.drop(tuple(["PLACEHOLDER"] * len(df.index.names)), axis=0, inplace=True, errors="ignore")
    df.fillna(fillna, inplace=True)
    return df


def __gdx_to_df_par(par, fillna=0.0):
    index_cols = []
    index_names = []
    if par.domains == []:
        return __gdx_to_df_scalar(par)
    for domain in par.domains:
        if type(domain) == gams.GamsSet:
            index_cols.append([ss.keys[0] for ss in domain])
            index_names.append(domain.name)
        else:
            index_cols.append(["PLACEHOLDER"])
            index_names.append("*")
    index = pd.MultiIndex.from_product(index_cols)
    df = pd.DataFrame(0., index=index, columns=[par.name])
    df.index.names = index_names
    if any([n == "*" for n in df.index.names]):
        df.index.names = ["Dim%d" % d for d in range(1, len(df.index.names) + 1)]

    for value in par:
        df.loc[tuple(value.keys), par.name] = value.value

    df.drop(tuple(["PLACEHOLDER"] * len(df.index.names)), axis=0, inplace=True, errors="ignore")
    df.fillna(fillna, inplace=True)
    return df


def __gdx_to_df_scalar(var, gams_type="L"):
    if type(var) == gams.GamsParameter:
        return [v.value for v in var][0]
    elif gams_type.upper() == "L":
        return [v.level for v in var][0]
    elif gams_type.upper() == "M":
        return [v.marginal for v in var][0]
    elif gams_type.upper() == "LO":
        return [v.lower for v in var][0]
    elif gams_type.upper() == "UP":
        return [v.upper for v in var][0]
    elif gams_type.upper() == "SCALE":
        return [v.scale for v in var][0]
    else:
        raise GamsAddOnException("gams_type %s not defined" % gams_type)


def __gdx_to_df_set(s):
    index_cols = []
    index_names = []
    for domain in s.domains:
        if type(domain) == gams.GamsSet:
            index_cols.append([ss.keys[0] for ss in domain])
            index_names.append(domain.name)
        else:
            index_cols.append(["PLACEHOLDER"])
            index_names.append("*")
    index = pd.MultiIndex.from_product(index_cols)

    df = pd.DataFrame(False, index=index, columns=[s.name])
    df.index.names = index_names
    if len(df.index.names) == 1 and "*" == df.index.names[0]:
        df.index.names = [s.name]
    elif len(df.index.names) > 1 and (
            any([n == "*" for n in df.index.names]) or any([n == None for n in df.index.names])):
        df.index.names = ["Dim%d" % d for d in range(1, len(df.index.names) + 1)]

    for value in s:
        df.loc[tuple(value.keys), s.name] = (str(value).split(" ")[-1] == "yes")
    df.drop(tuple(["PLACEHOLDER"] * len(df.index.names)), axis=0, inplace=True, errors="ignore")
    return df


def __call_gdxdump(gdx_file, symbol, gams_type="L"):
    if gams_type == "L":
        if sys.platform in ['linux2', 'darwin']:
            proc = subprocess.Popen(
                ['gdxdump %s Symb=%s Format=csv Delim=comma FilterDef=N EpsOut=0.0' % (gdx_file, symbol), ""],
                stdout=subprocess.PIPE, shell=True,
                stderr=subprocess.STDOUT)
        elif sys.platform in ['win32']:
            proc = subprocess.Popen(
                ['gdxdump', '%s' % gdx_file, 'Symb=%s' % symbol, 'FilterDef=N', 'Format=csv', 'Delim=comma',
                 'EpsOut=0.0'],
                stdout=subprocess.PIPE, shell=True,
                stderr=subprocess.STDOUT)
        else:
            raise GamsAddOnException('ERROR {platform} not handled'.format(platform=sys.platform))
    else:
        if sys.platform in ['linux2', 'darwin']:
            proc = subprocess.Popen(
                ['gdxdump %s Symb=%s Format=csv Delim=comma FilterDef=N EpsOut=0.0' % (gdx_file, symbol), ""],
                stdout=subprocess.PIPE, shell=True,
                stderr=subprocess.STDOUT)
        elif sys.platform in ['win32']:
            cmd = ['gdxdump', '%s' % gdx_file, 'Symb=%s' % symbol, 'FilterDef=N', 'Format=csv', 'Delim=comma',
                   'CSVAllFields', 'EpsOut=0.0']
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE, shell=True,
                                    stderr=subprocess.STDOUT)
        else:
            raise GamsAddOnException('ERROR {platform} not handled'.format(platform=sys.platform))
    (out, err) = proc.communicate()
    out = out.decode("latin-1")
    return out, err
