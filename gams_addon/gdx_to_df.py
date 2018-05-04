#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Hanspeter Höschle <hanspeter.hoeschle@energyville.be>'
__date__ = "04/05/2018"

import gams
import pandas as pd

from .gams_add_on_exception import GamsAddOnException


def gdx_to_df(gdx_file, symbol, **kwargs):
    ws = gams.GamsWorkspace()
    db = ws.add_database_from_gdx(gdx_file)
    s = db.get_symbol(symbol)
    if s.number_records == 0:
        return __gdx_to_df_var_empty(s)
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


def __gdx_to_df_var_empty(symbol):
    index = pd.MultiIndex.from_tuples([tuple([1] * symbol.dimension)])
    df = pd.DataFrame(None, index=index, columns=[symbol.name]).dropna()
    df.index.names = symbol.domains_as_strings
    return df


def __gdx_to_df_var_equ(var, gams_type="L", fillna=0.0):
    if var.domains == []:
        return __gdx_to_df_scalar(var, gams_type)

    index = pd.MultiIndex.from_tuples([g.keys for g in var])

    if gams_type.upper() == "L":
        values = [v.level for v in var]
    elif gams_type.upper() == "M":
        values = [v.marginal for v in var]
    elif gams_type.upper() == "UP":
        values = [v.upper for v in var]
    elif gams_type.upper() == "LO":
        values = [v.lower for v in var]
    elif gams_type.upper() == "SCALE":
        values = [v.scale for v in var]
    else:
        raise GamsAddOnException("gams_type %s not defined" % gams_type)

    df = pd.DataFrame(values, index=index, columns=[var.name])
    df.index.names = __replace_stars(var.domains_as_strings)
    return df


def __gdx_to_df_par(par, fillna=0.0):
    if par.domains == []:
        return __gdx_to_df_scalar(par)

    index = pd.MultiIndex.from_tuples([g.keys for g in par])
    values = [v.value for v in par]

    df = pd.DataFrame(values, index=index, columns=[par.name])
    df.index.names = __replace_stars(par.domains_as_strings)
    return df


def __replace_stars(domain_list):
    for i, s in enumerate(domain_list):
        if s == "*":
            domain_list[i] = "Dim%d" % (i + 1)
    return domain_list


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
    index = pd.MultiIndex.from_tuples([g.keys for g in s])
    values = [(str(v).split(" ")[-1] == "yes") for v in s]
    df = pd.DataFrame(values, index=index, columns=[s.name])
    if s.dimension == 1 and s.domains_as_strings == ["*"]:
        df.index.names = [s.name]
    else:
        df.index.names = __replace_stars(s.domains_as_strings)

    return df
