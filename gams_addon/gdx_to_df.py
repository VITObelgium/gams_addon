__author__ = 'Hanspeter Hoeschle <hanspeter.hoeschle@gmail.com>'
__date__ = "26/06/2017"
import io
import subprocess
import sys

import pandas as pd

from .domain_info import DomainInfo
from .gams_add_on_exception import GamsAddOnException


def gdx_to_df(gdx_file, symbol, gams_type='L', domain_info=None, fillna=0.0):
    # Derive domain info
    if domain_info is None:
        domain_info = DomainInfo(gdx_file)
    if symbol not in domain_info.symbols:
        raise GamsAddOnException('"%s" not in Domain of "%s"' % (symbol, gdx_file))
    symbol_type = domain_info.symbols[symbol][0]

    # Sets
    if symbol_type == "Set":
        return __gdx_to_df_set(gdx_file, symbol, domain_info)

    # Parameter
    if symbol_type == "Par":
        return __gdx_to_df_par(gdx_file, symbol, domain_info, fillna)

    # Variable
    if symbol_type == "Var":
        return __gdx_to_df_var(gdx_file, symbol, domain_info, gams_type.upper(), fillna)

    # Equation
    if symbol_type == "Equ":
        return __gdx_to_df_equ(gdx_file, symbol, domain_info, gams_type.upper(), fillna)


def __gdx_to_df_equ(gdx_file, symbol, domain_info, gams_type, fillna):
    sets = domain_info.get_sets(symbol)
    if sets and any([s == "*" for s in sets]):
        print("-" * 80)
        print("WARNING: Sets have not been specified for: %s" % symbol)
        print("-" * 80)
        (out, err) = __call_gdxdump(gdx_file, symbol, gams_type)
        df_in = pd.read_csv(io.StringIO(out), sep=",")
        if gams_type == "L":
            idx = list(df_in.columns[:-1])
            df_in.set_index(idx, inplace=True)
            df_in.columns = [symbol]
            return df_in
        else:
            idx = list(df_in.columns[:-5])
            df_in.set_index(idx, inplace=True)
            if gams_type == "M":
                df_in[symbol] = df_in["Marginal"]
            elif gams_type == "LO":
                df_in[symbol] = df_in["Lower"]
            elif gams_type == "UP":
                df_in[symbol] = df_in["Upper"]
            elif gams_type == "SCALE":
                df_in[symbol] = df_in["Scale"]
            else:
                raise GamsAddOnException("gams_type %s not defined" % gams_type)
            return pd.DataFrame(df_in[symbol])
    else:
        set_names = []
        set_index = []

        if sets:
            for s in sets:
                ss = s
                i = 1
                while ss in set_names:
                    ss = "%s_%02d" % (s, i)
                    i += 1
                set_names.append(ss)
                if s != "*":
                    idx = __gdx_to_df_set(gdx_file, s, domain_info)
                    idx = idx[idx[s]].index
                else:
                    idx = [0]
                set_index.append(list(idx))
                df = pd.DataFrame(index=pd.MultiIndex.from_product(set_index))
                df.index.names = set_names
        else:
            return __gdx_to_df_scalar(gdx_file, symbol, gams_type)

        df[symbol] = fillna

        (out, err) = __call_gdxdump(gdx_file, symbol, gams_type)
        df_in = pd.read_csv(io.StringIO(out), sep=",")
        if gams_type == "L":
            df_in.columns = df.index.names + [symbol]
        else:
            exit()

        df[symbol] = df_in[symbol]
        return df.fillna(fillna)


def __gdx_to_df_var(gdx_file, symbol, domain_info, gams_type, fillna):
    sets = domain_info.get_sets(symbol)
    if sets is None:
        return __gdx_to_df_scalar(gdx_file, symbol, gams_type=gams_type, fillna=fillna)

    set_names = []
    set_index = []

    for s in sets:
        ss = s
        while ss in set_names:
            ss = ss + s[-1]
        set_names.append(ss)
        idx = __gdx_to_df_set(gdx_file, s, domain_info)
        idx = idx[idx[s]].index
        set_index.append(list(idx))
    df = pd.DataFrame(index=pd.MultiIndex.from_product(set_index))
    df.index.names = set_names
    df[symbol] = fillna

    (out, err) = __call_gdxdump(gdx_file, symbol, gams_type)
    df_in = pd.read_csv(io.StringIO(out), sep=",")
    if gams_type == "L":
        index = list(df_in.columns[:-1])
        df_in.set_index(index, inplace=True)
        for idx in df_in.index:
            df.loc[idx, symbol] = df_in.loc[idx, "Val"]
    else:
        index = list(df_in.columns[:-5])
        df_in.set_index(index, inplace=True)
        if gams_type == "M":
            for idx in df_in.index:
                df.loc[idx, symbol] = df_in.loc[idx, "Marginal"]
        elif gams_type == "LO":
            for idx in df_in.index:
                df.loc[idx, symbol] = df_in.loc[idx, "Lower"]
        elif gams_type == "UP":
            for idx in df_in.index:
                df.loc[idx, symbol] = df_in.loc[idx, "Upper"]
        elif gams_type == "SCALE":
            for idx in df_in.index:
                df.loc[idx, symbol] = df_in.loc[idx, "Scale"]
        else:
            raise GamsAddOnException("gams_type %s not defined" % gams_type)

    return df.fillna(fillna)


def __gdx_to_df_par(gdx_file, symbol, domain_info, fillna):
    sets = domain_info.get_sets(symbol)

    if sets is None:
        return __gdx_to_df_scalar(gdx_file, symbol)

    if any([s == "*" for s in sets]):
        (out, err) = __call_gdxdump(gdx_file, symbol)
        df = pd.read_csv(io.StringIO(out), sep=",", index_col=[idx for idx in range(len(sets))])
        df.columns = [symbol]
        return df
    else:
        set_names = []
        set_index = []

        for s in sets:
            ss = s
            i = 1
            while ss in set_names:
                ss = "%s_%02d" % (s, i)
                i += 1
            set_names.append(ss)
            idx = __gdx_to_df_set(gdx_file, s, domain_info)
            idx = idx[idx[s]].index
            set_index.append(list(idx))

        df = pd.DataFrame(index=pd.MultiIndex.from_product(set_index))
        df.index.names = set_names
        df[symbol] = fillna

        (out, err) = __call_gdxdump(gdx_file, symbol)
        df_in = pd.read_csv(io.StringIO(out), sep=",")

        index = list(df_in.columns[:-1])
        df_in.set_index(index, inplace=True)

        for idx in df_in.index:
            df.loc[idx, symbol] = df_in.loc[idx, "Val"]
        df.fillna(fillna, inplace=True)
        return df


def __gdx_to_df_scalar(gdx_file, symbol, gams_type="L", fillna=0.0):
    (out, err) = __call_gdxdump(gdx_file, symbol, gams_type)
    df = pd.read_csv(io.StringIO(out), sep=",")
    if gams_type == "L":
        return float(df.loc[0, "Val"])
    elif gams_type == "M":
        return float(df.loc[0, "Marginal"])
    elif gams_type == "LO":
        return float(df.loc[0, "Lower"])
    elif gams_type == "UP":
        return float(df.loc[0, "Upper"])
    elif gams_type == "SCALE":
        return float(df.loc[0, "Scale"])
    else:
        raise GamsAddOnException("gams_type %s not defined" % gams_type)


def __gdx_to_df_set(gdx_file, symbol, domain_info):
    sets = domain_info.get_sets(symbol)

    # Set with a undefined set, also 1-dimensional sets
    if any([s == "*" for s in sets]):
        (out, err) = __call_gdxdump(gdx_file, symbol)
        df = pd.read_csv(io.StringIO(out), sep=",", index_col=[idx for idx in range(len(sets))])
        df[symbol] = True
        if len(sets) == 1:
            df.index.names = [symbol]
        return df

    # Unique set
    elif [symbol] == sets:
        set_names = sets
        (out, err) = __call_gdxdump(gdx_file, symbol)
        df = pd.read_csv(io.StringIO(out), sep=",")
        df.set_index(sets, inplace=True)
        df[symbol] = True
        return df

    # Super sets or others
    elif [symbol] != sets:
        if type(sets) is not list:
            set_names = [sets]
        else:
            set_names = sets
        set_index = []
        for s in set_names:
            set_index.append(list(__gdx_to_df_set(gdx_file, s, domain_info).index))

        if len(set_index) > 1:
            df = pd.DataFrame(index=pd.MultiIndex.from_product(set_index))
        else:
            df = pd.DataFrame(index=set_index[0])
        df.index.names = set_names
        df[symbol] = False

        (out, err) = __call_gdxdump(gdx_file, symbol)
        df_in = pd.read_csv(io.StringIO(out), sep=",")
        df_in[symbol] = True
        index = list(df_in.columns[:-1])
        df_in.set_index(index, inplace=True)
        df.loc[df_in.index, symbol] = True
        df.index.names = set_names
        return df

    else:
        raise GamsAddOnException("Check handling of sets %s", sets)


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
