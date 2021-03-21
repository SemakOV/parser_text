import unittest
import parser_new_beta as tps

filename = 'test_schedule.inc'
section_names = ['COMPDATL', 'COMPDAT', 'DATES']
file_text = tps.open_file(filename)


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.file_text = file_text
        self.file_text_sort_section_names = tps.pars_file_text_keywords(self.file_text, section_names)
        self.sort_dict_and_list = tps.sort_date_and_section_name(self.file_text_sort_section_names)
        self.sort_dict_and_list = tps.formatting_allocation(*self.sort_dict_and_list)
        self.sort_data = tps.sorting_to_class(*self.sort_dict_and_list)
        self.format_query = tps.formatting_query_arguments('01/10.2018', 'w3', 'OPeN')
        self.query_results = tps.show_query_results(self.sort_data, *self.format_query)

    def tearDown(self):
        self.doCleanups()

    def test_pars_file_text_keywords_result(self):
        result = tps.pars_file_text_keywords(self.file_text, section_names)
        self.assertEqual(result, self.file_text_sort_section_names)

    def test_pars_file_text_keywords_type(self):
        result = tps.pars_file_text_keywords(self.file_text, section_names)
        self.assertEqual(type(result[-1]), type(self.file_text_sort_section_names[-1]))

    @unittest.expectedFailure
    def test_pars_file_text_keywords_error(self):
        result = tps.pars_file_text_keywords(self.file_text, ['', '', '1'])
        self.assertEqual(result[5], self.file_text_sort_section_names[5])

    def test_sorting_to_class_result_no_date(self):
        result = tps.sorting_to_class(*self.sort_dict_and_list)
        self.assertEqual(result.no_date, self.sort_data.no_date)

    def test_sorting_to_class_result_date(self):
        result = tps.sorting_to_class(*self.sort_dict_and_list)
        self.assertEqual(result.date, self.sort_data.date)

    def test_sorting_to_class_result_value(self):
        result = tps.sorting_to_class(*self.sort_dict_and_list)
        self.assertEqual(result.no_date[-1].local_grid_name, "'LGR1'")

    def test_sorting_to_class_type(self):
        result = tps.sorting_to_class(*self.sort_dict_and_list)
        self.assertEqual(type(result), type(self.sort_data))

    @unittest.expectedFailure
    def test_sorting_to_class_error(self):
        result = tps.sorting_to_class(*('', ''))
        self.assertEqual(result, self.sort_data)

    def test_sort_date_and_section_name_value(self):
        result = tps.sort_date_and_section_name(self.file_text_sort_section_names)
        self.assertEqual(result[1][0][1], "'W1' 10 10  1   3 \tOPEN \t1* \t1\t2 \t1 \t3* \t\t\t1.0 /")

    def test_sort_date_and_section_name_value2(self):
        result = tps.sort_date_and_section_name(self.file_text_sort_section_names)
        self.assertEqual(result[-1][-1][1], "'W6' 'LGR1' 10 10  2   2 \tOPEN \t1* \t1\t2 \t1 \t3* \t\t\t1.0918 /")

    @unittest.expectedFailure
    def test_sort_date_and_section_name_error(self):
        result = tps.sort_date_and_section_name('')
        self.assertEqual(result[1][0][1], "'W1' 10 10  1   3 \tOPEN \t1* \t1\t2 \t1 \t3* \t\t\t1.0 /")

    def test_show_query_results_open(self):
        format_q = ('01 JUL 2018', 'W3', 'OPEN')
        result = tps.show_query_results(self.sort_data, *format_q)
        self.assertEqual(result.name, self.sort_data.date['01 JUL 2018'][0].name)

    def test_show_query_results_open2(self):
        format_q = ('01 OCT 2018', 'W3', 'OPEN')
        result = tps.show_query_results(self.sort_data, *format_q)
        self.assertEqual(result.name, self.sort_data.date['01 OCT 2018'][0].name)

    def test_show_query_results_no_open(self):
        format_q = ('02 OCT 2018', 'W3', 'OPEN')
        result = tps.show_query_results(self.sort_data, *format_q)
        self.assertEqual(result, "No open in date")

    @unittest.expectedFailure
    def test_split_well_description_str(self):
        result = tps.split_well_description_str('')
        self.assertEqual(result, ["'W6'", "'LGR1'", '10', '10', '2', '2', 'OPEN', 'DEF', '1', '2', '1', 'DEF', 'DEF',
                                  'DEF', '1.0918'])

    @unittest.expectedFailure
    def test_format_well_description_str(self):
        result = format_well_description_str('')
        self.assertEqual(result, ("'W6'", 10, 10, 2, 2, 'OPEN', 'DEF', 1.0, 2.0, 1.0, 'DEF', 'DEF', 'DEF', 1.0918,
                                  "'LGR1'"))

    @unittest.expectedFailure
    def test_formatting_query_arguments(self):
        result = tps.formatting_query_arguments('', '', '')
        self.assertEqual(result, ('01 JUL 2018', 'W3', 'OPEN'))

    def test_formatting_allocation_no_dates_sort_list(self):
        result = tps.formatting_allocation(*(tps.sort_date_and_section_name(self.file_text_sort_section_names)))
        self.assertEqual(result[1], self.sort_dict_and_list[1])

    def test_formatting_allocation_dates_sort_dict(self):
        result = tps.formatting_allocation(*(tps.sort_date_and_section_name(self.file_text_sort_section_names)))
        self.assertEqual(result[0], self.sort_dict_and_list[0])

    @unittest.expectedFailure
    def test_formatting_allocation_error(self):
        result = tps.formatting_allocation(*('', ''))
        self.assertEqual(result, self.sort_dict_and_list)


if __name__ == '__main__':
    unittest.main(verbosity=2)
