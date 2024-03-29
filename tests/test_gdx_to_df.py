__author__ = 'Hanspeter Hoeschle <hanspeter.hoeschle@gmail.com>'
import os
import unittest

import gams_addon as ga
from create_test_database import create_test_database


class TestGdxToDf(unittest.TestCase):
    def test_read_out_sets(self):
        gdx_file = os.path.join(os.getcwd(), 'test_database.gdx')
        create_test_database(gdx_file)

        domain_info = ga.DomainInfo(gdx_file)

        df = ga.gdx_to_df(gdx_file, 'S', domain_info=domain_info)
        self.assertEqual(len(df), 10)
        self.assertEqual(df.index.nlevels, 1)
        self.assertEqual(df.columns.values, ["S"])
        self.assertEqual(df.index.names[0], "S")

        df = ga.gdx_to_df(gdx_file, 'SubS', domain_info=domain_info)
        self.assertEqual(len(df), 5)
        self.assertEqual(len(df[df['SubS']]), 5)
        self.assertEqual(df.index.nlevels, 1)
        self.assertEqual(df.columns.values, ["SubS"])
        self.assertEqual(df.index.names[0], "S")

        df = ga.gdx_to_df(gdx_file, 'I')
        self.assertEqual(len(df), 10)
        self.assertEqual(df.index.nlevels, 1)
        self.assertEqual(df.columns.values, ["I"])
        self.assertEqual(df.index.names[0], "I")

        df = ga.gdx_to_df(gdx_file, 'SubI', domain_info=domain_info)
        self.assertEqual(len(df), 5)
        self.assertEqual(len(df[df['SubI']]), 5)
        self.assertEqual(df.index.nlevels, 1)
        self.assertEqual(df.columns.values, ["SubI"])
        self.assertEqual(df.index.names[0], "I")

        df = ga.gdx_to_df(gdx_file, 'SubSI', domain_info=domain_info)
        self.assertEqual(len(df), 25)
        self.assertEqual(len(df[df['SubSI']]), 25)
        self.assertEqual(df.index.nlevels, 2)
        self.assertEqual(df.columns.values, ["SubSI"])
        self.assertEqual(df.index.names, ["S", "I"])

        df = ga.gdx_to_df(gdx_file, 'E', domain_info=domain_info)
        self.assertTrue(df.empty)

        df = ga.gdx_to_df(gdx_file, 'M_I')
        self.assertEqual(len(df), 100)
        self.assertEqual(df.index.nlevels, 2)
        self.assertEqual(df.columns.values, ["M_I"])
        self.assertEqual(df.index.names, ["Dim1", "Dim2"])

        df = ga.gdx_to_df(gdx_file, 'M_S')
        self.assertEqual(len(df), 100)
        self.assertEqual(df.index.nlevels, 2)
        self.assertEqual(df.columns.values, ["M_S"])
        self.assertEqual(df.index.names, ["Dim1", "Dim2"])

        df = ga.gdx_to_df(gdx_file, 'M_M')
        self.assertEqual(len(df), 100)
        self.assertEqual(df.index.nlevels, 2)
        self.assertEqual(df.columns.values, ["M_M"])
        self.assertEqual(df.index.names, ["Dim1", "Dim2"])

        df = ga.gdx_to_df(gdx_file, 'MAX')
        self.assertEqual(len(df), 10)
        self.assertEqual(df.index.nlevels, 20)
        self.assertEqual(df.columns.values, ["MAX"])
        self.assertEqual(df.index.names, ["Dim%d" % d for d in range(1, 21)])

    def test_read_out_parameters(self):
        gdx_file = os.path.join(os.getcwd(), 'test_database.gdx')
        create_test_database(gdx_file)

        domain_info = ga.DomainInfo(gdx_file)

        df = ga.gdx_to_df(gdx_file, 'Scalar_P1', domain_info=domain_info)
        self.assertEqual(df, 10)
        self.assertEqual(type(df), float)

        df = ga.gdx_to_df(gdx_file, 'Scalar_P2', domain_info=domain_info)
        self.assertEqual(df, 10)
        self.assertEqual(type(df), float)

        # Parameters defined over sets
        df = ga.gdx_to_df(gdx_file, 'Param_S', domain_info=domain_info)
        self.assertEqual(len(df), 10)
        self.assertEqual(sum(df['Param_S']), 60.)
        self.assertEqual(df.index.names, ['S'])
        self.assertEqual(df.columns, ['Param_S'])

        df = ga.gdx_to_df(gdx_file, 'Param_S_S', domain_info=domain_info)
        self.assertEqual(len(df), 100)
        self.assertEqual(sum(df['Param_S_S']), 1550)
        self.assertEqual(df.index.names, ['S', 'S'])
        self.assertEqual(df.columns, ['Param_S_S'])

        df_param_s_i = ga.gdx_to_df(gdx_file, 'Param_S_I', domain_info=domain_info)
        self.assertEqual(len(df_param_s_i), 100)
        self.assertEqual(sum(df_param_s_i['Param_S_I']), 1550)
        self.assertEqual(df_param_s_i.index.names, ['S', 'I'])
        self.assertEqual(df_param_s_i.columns, ['Param_S_I'])

        df = ga.gdx_to_df(gdx_file, 'Param_S_E', domain_info=domain_info)
        self.assertTrue(df.empty)
        self.assertEqual(df.index.names, ['S', 'E'])
        self.assertEqual(df.columns, ['Param_S_E'])

        df = ga.gdx_to_df(gdx_file, 'Param_P1', domain_info=domain_info)
        self.assertEqual(len(df), 10)
        self.assertEqual(sum(df['Param_P1']), 155)
        self.assertEqual(df.index.names, ['Dim1'])
        self.assertEqual(df.columns, ['Param_P1'])

        df = ga.gdx_to_df(gdx_file, 'Param_P2', domain_info=domain_info)
        self.assertEqual(len(df), 100)
        self.assertEqual(sum(df['Param_P2']), 1550)
        self.assertEqual(df.index.names, ['Dim1', 'Dim2'])
        self.assertEqual(df.columns, ['Param_P2'])

    def test_read_out_variables(self):
        gdx_file = os.path.join(os.getcwd(), 'test_database.gdx')
        create_test_database(gdx_file)

        domain_info = ga.DomainInfo(gdx_file)

        df = ga.gdx_to_df(gdx_file, 'Scalar_V1', domain_info=domain_info)
        self.assertEqual(df, 10)
        self.assertEqual(type(df), float)

        df = ga.gdx_to_df(gdx_file, 'Scalar_V1', domain_info=domain_info, gams_type="lo")
        self.assertEqual(df, 0)
        self.assertEqual(type(df), float)

        df = ga.gdx_to_df(gdx_file, 'Scalar_V1', domain_info=domain_info, gams_type="up")
        self.assertEqual(df, 1000)
        self.assertEqual(type(df), float)

        df = ga.gdx_to_df(gdx_file, 'Scalar_V1', domain_info=domain_info, gams_type="M")
        self.assertEqual(df, 2)
        self.assertEqual(type(df), float)

        df = ga.gdx_to_df(gdx_file, 'Scalar_V1', domain_info=domain_info, gams_type="scale")
        self.assertEqual(df, 1)
        self.assertEqual(type(df), float)

    def test_own_gdx_files(self):
        gdx_file = os.path.join('C:/Users/hhoschle/Desktop/kris_master_thesis/.gams/output_data_ref_0.gdx')

        # df = ga.gdx_to_df(gdx_file, "Model_stats")
        # df = ga.gdx_to_df(gdx_file, "cap")
        # print df
