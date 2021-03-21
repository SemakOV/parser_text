"""
В данном файле представлен построчный парсер.

"""
import re
import datetime
from pathlib import Path
import typing as tp
import dataclasses as dc
import doctest


@dc.dataclass(frozen=True)
class COMPDAT:
    """ Класс для хранения секции COMPDAT. """
    name: str = 'not assigned'
    i_location: int = 0
    j_location: int = 0
    k_location_upper: int = 0
    k_location_lower: int = 0
    flag: str = 'OPEN'
    saturation_table_number: float = 0.0
    transmissibility_factor: float = 0.0
    well_bore_diameter: float = 0.3048
    kh: float = -0.1
    skin_factor: float = 0.0
    d_factor: float = -0.1
    direction: str = 'Z'
    pressure_equivalent_radius: float = 0.0


@dc.dataclass(frozen=True)
class COMPDATL(COMPDAT):
    """ Класс для хранения секции COMPDATL. """
    local_grid_name: str = 'not assigned'


@dc.dataclass
class DATES:
    """ Класс для хранения секции COMPDATL и COMPDAT отсортированных по дате. """
    date: tp.Dict[str, tp.List[tp.Union[COMPDAT, COMPDATL]]]
    no_date: tp.List[tp.Union[COMPDAT, COMPDATL]]


def open_file(filename: tp.Union[str, Path]) -> tp.Union[tp.List[str]]:
    """ Открываем файл и помещаем строки в лист.

    :param filename: Путь к schedule-файлу.

    :return: Список сырых данных без сортировки.

    """
    filename = Path(filename)
    assert filename.exists(), "Файл не существует. Проверьте корректность указания пути к файлу или его наименования."
    with filename.open(mode='r') as fo:
        file_text = []
        line = fo.readline()
        while line:
            file_text.append(line)
            line = fo.readline()
    return file_text


def pars_file_text_keywords(file_text: tp.Union[tp.List[str]], section_names: tp.List[str]) -> tp.List[str]:
    """ Сортируем сырые данные по названиям секций 'COMPDATL', 'COMPDAT', 'DATES'.

    :param str file_text: Список сырых данных без сортировки.

    :param section_names: Список имен секций.

    :return: Список данных отсортированных по названиям секций.

    """
    pars_file_text_section_names = []
    flag_block = False
    # assert
    for line in file_text:
        if line.startswith(r'/'):
            pars_file_text_section_names.append(line)
            flag_block = False
        elif line.startswith(tuple(section_names)) or flag_block:
            flag_block = True
            pars_file_text_section_names.append(line)
    return pars_file_text_section_names


regex = {'DATE': r'((?P<date>\d{2}\s\w+\s\d{4})\s/.*?\n)',
         'COMPDAT': r'(?P<compdat>^\'\w+\'\s[^\'].+?\s/)',
         'COMPDATL': r'(?P<compdatl>^\'\w+\'\s\'.+?\s/)',
         }


def sort_date_and_section_name(pars_file_text: tp.List[str]) -> \
        tp.Tuple[tp.Dict[str, tp.List[tp.List[str]]], tp.List[tp.List[str]]]:
    """ Сортируем данные по  определенной дате с указанием принадлежности к секции.

    Примечание: Mypy выдает ошибку 'Item "None" of "Optional[Match[str]]" has no attribute "group"' при присваивании
    результата работы регулярного выражения через группы. Ошибка отнесена в ignore, так как проверка на
    несоответствие результата поиска значению None определена в блоке 'if'.

    :param pars_file_text: Список данных отсортированных по названиям секций.

    :return: Кортеж из отсортированных по дате секций в словаре и списка секций без даты.

    """
    flag_date = False  # Переменная, указывающая на принадлежность данных к определенной дате
    base_date = ''  # Значение определенной даты
    dates_sort_dict: tp.Dict[str, tp.List[tp.List[str]]] = {}
    no_dates_sort_list = []
    for line_text in pars_file_text:
        if re.search(regex['DATE'], line_text) is not None:
            flag_date = True
            base_date = re.search(regex['DATE'], line_text).group('date')  # type: ignore
        elif re.search(regex['COMPDAT'], line_text, re.MULTILINE) is not None:
            description_compdat = re.search(regex['COMPDAT'], line_text, re.MULTILINE).group('compdat')  # type: ignore
            if flag_date:
                dates_sort_dict.setdefault(base_date, [])
                dates_sort_dict[base_date].append(['COMPDAT', description_compdat])
            else:
                no_dates_sort_list.append(['COMPDAT', description_compdat])
        elif re.search(regex['COMPDATL'], line_text, re.MULTILINE) is not None:
            description_compdatl = re.search(regex['COMPDATL'], line_text, re.MULTILINE).group('compdatl')# type: ignore
            if flag_date:
                dates_sort_dict.setdefault(base_date, [])
                dates_sort_dict[base_date].append(['COMPDATL', description_compdatl])
            else:
                no_dates_sort_list.append(['COMPDATL', description_compdatl])
            # elif i == ***: flag_date = False Не уточнены условия для секций без даты (при чтении полного файла)
    return dates_sort_dict, no_dates_sort_list


def split_well_description_str(description_str: str) -> tp.List[str]:
    """ Разбиваем строку описания вскрытия скважины с установкой дефолтных значений и очищаем от лишних знаков.

    :param description_str: Сырая строка описания без разделения на определенные значения.

    :return: Список c разделенными данными о вскрытии скважины (дефолтные значения отражены как "DEF").

    >>> split_well_description_str("'W1' 10 10  1   3 \tOPEN \t1* \t1\t2 \t1 \t3* \t\t\t1.0 /")
    ["'W1'", '10', '10', '1', '3', 'OPEN', 'DEF', '1', '2', '1', 'DEF', 'DEF', 'DEF', '1.0']

    >>> split_well_description_str("'W6' 'LGR1' 10 10  2   2 \tOPEN \t1* \t1\t2 \t1 \t3* \t\t\t1.0918 /")
    ["'W6'", "'LGR1'", '10', '10', '2', '2', 'OPEN', 'DEF', '1', '2', '1', 'DEF', 'DEF', 'DEF', '1.0918']

    """
    split_str_description = re.sub('\s', "+", description_str).split('+')  # Разбиваем строку
    for ind, val in enumerate(split_str_description):
        if len(val) > 1 and val[-1] == '*':  # Вставляем дефолтные значения в место пустых строк
            for position_def in range(int(val[:-1])):
                split_str_description[ind + position_def] = "DEF"
    split_str_description = [i for i in split_str_description if i != "" and i != '/']  # Убираем лишние символы
    return split_str_description


def format_well_description_str(split_str_description: tp.List[tp.Any]) -> tp.Tuple[tp.Any, ...]:
    """ Преобразуем значения строки описания вскрытия скважины к необходимому формату.

    Примечание: при указании типа split_str_description как List[str] анализатор Mypy выводит ошибку
    " No overload variant of "__setitem__" of "list" matches argument types "int", "int" ".
    Данная ошибка, предположительно, связана с инициализацией(а так же переопределением собственного значения) списка
    и обращением к нему через индекс. Для избежания данной ошибки указан тип List[Any].

    :param split_str_description: Список c разделенными данными о вскрытии скважины.

    :return: Кортеж c разделенными отформатированными данными о вскрытии скважины.

    >>> format_well_description_str(["'W1'", '10', '10', '1', '3', 'OPEN', 'DEF', '1', '2', \
    '1', 'DEF', 'DEF', 'DEF', '1.0'])
    ("'W1'", 10, 10, 1, 3, 'OPEN', 'DEF', 1.0, 2.0, 1.0, 'DEF', 'DEF', 'DEF', 1.0)

    >>> format_well_description_str(["'W6'", "'LGR1'", '10', '10', '2', '2', 'OPEN', 'DEF', '1', '2', \
    '1', 'DEF', 'DEF', 'DEF', '1.0918'])
    ("'W6'", 10, 10, 2, 2, 'OPEN', 'DEF', 1.0, 2.0, 1.0, 'DEF', 'DEF', 'DEF', 1.0918, "'LGR1'")

    """
    for ind, item in enumerate(split_str_description):
        if isinstance(item, str) and item.isdigit() and ind <= 5:
            split_str_description[ind] = int(item)
        elif isinstance(item, str) and item.replace('.', '', 1).isdigit() and ind > 5:
            split_str_description[ind] = float(item)
    if len(split_str_description) > 14:
        l_g_n = split_str_description.pop(1)
        split_str_description.append(l_g_n)
    return tuple(split_str_description)


def formatting_allocation(dates_sort_dict: tp.Dict[str, tp.List[tp.List[tp.Any]]],
                          no_dates_sort_list: tp.List[tp.List[tp.Any]]) ->\
                            tp.Tuple[tp.Dict[str, tp.List[tp.List[tp.Any]]], tp.List[tp.List[tp.Any]]]:
    """ Производим преобразование строк описания вскрытия к необходимому типу
    за счет функций split_well_description_str и format_well_description_str. Обращение
    к преобразующим функциям произведено в зависимости
    от типа аргумента с данными(дополнительно происходит проверка соответствия типов аргументов).

    :param dates_sort_dict: Словарь данных, отсортированных по секциям и дате.

    :param no_dates_sort_list: Список данных, отсортированных по секциям без даты.

    :return: Кортеж из словаря и списка с преобразованными к необходимому типу значениями.

    """
    if isinstance(no_dates_sort_list, list):
        for str_description in no_dates_sort_list:
            str_description[1] = format_well_description_str(split_well_description_str(str_description[1]))
    if isinstance(dates_sort_dict, dict):
        for key_date in dates_sort_dict:
            for str_description in dates_sort_dict[key_date]:
                str_description[1] = format_well_description_str(split_well_description_str(str_description[1]))
    return dates_sort_dict, no_dates_sort_list


def sorting_to_class(dates_sort_dict: tp.Dict[str, tp.List[tp.List[tp.Any]]],
                     no_dates_sort_list: tp.List[tp.List[tp.Any]]) -> DATES:
    """ Помещаем значения словаря и списка в объекты соответствующих классов с учетом дефолтных значений.

    :param dates_sort_dict: Словарь данных, отсортированных по секциям и дате (значения преобразованы).

    :param no_dates_sort_list: Список данных, отсортированных по секциям без даты (значения преобразованы).

    :return: Объект класса DATES с вложенными в атрибуты словарем и списком.

    """
    date: tp.Dict[str, tp.List[tp.Union[COMPDAT, COMPDATL]]] = {}
    no_date = []
    for value_date in dates_sort_dict:
        for well_description in dates_sort_dict[value_date]:
            if well_description[0] == 'COMPDAT':
                date.setdefault(value_date, [])
                date[value_date].append(COMPDAT(*[
                    val if val != "DEF" else getattr(COMPDAT, tuple(COMPDAT.__annotations__)[:15][ind]) for ind, val
                    in enumerate(well_description[1])
                ]))
            elif well_description[0] == 'COMPDATL':
                date.setdefault(value_date, [])
                date[value_date].append(COMPDATL(*[
                    val if val != "DEF" else
                    getattr(COMPDATL,
                            (tuple(COMPDATL.__base__.__annotations__)[:15] + tuple(COMPDATL.__annotations__)[:1])[ind])
                    for ind, val in enumerate(well_description[1])
                ]))
    for well_description in no_dates_sort_list:
        if well_description[0] == 'COMPDAT':
            no_date.append(COMPDAT(*[
                val if val != "DEF" else getattr(COMPDAT, tuple(COMPDAT.__annotations__)[:15][ind]) for ind, val
                in enumerate(well_description[1])
            ]))
        elif well_description[0] == 'COMPDATL':
            no_date.append(COMPDATL(*[
                val if val != "DEF" else
                getattr(COMPDATL,
                        (tuple(COMPDATL.__base__.__annotations__)[:15] + tuple(COMPDATL.__annotations__)[:1])[ind])
                for ind, val in enumerate(well_description[1])
            ]))
    return DATES(date, no_date)


def formatting_query_arguments(date: str, name: str, state: str) -> tp.Tuple[str, str, str]:
    """ Преобразуем введенные данные запроса к формату, соответствующему значениям объекта класса.

    :param date: Строка, содержащая дату.

    :param name: Строка, содержащая наименование скважены.

    :param state: Строка, содержащая значение флага открытия скважины.

    :return: Кортеж с отформатированными параметрами запроса.

    >>> formatting_query_arguments('01/10.2018', 'w3', 'OPeN')
    ('01 OCT 2018', 'W3', 'OPEN')

    >>> formatting_query_arguments('01.09.2018', 'w2', 'open')
    ('01 SEP 2018', 'W2', 'OPEN')

    """
    read_date = datetime.datetime.strptime(' '.join(re.split('\W', date)), '%d %m %Y')
    date = datetime.datetime.strftime(read_date, '%d %b %Y').upper()
    name = name.upper()
    state = state.upper()
    return date, name, state


def show_query_results(sort_data: DATES, date_key: str, name: str, state: str) -> tp.Union[COMPDAT, COMPDATL, str]:
    """ Производим поиск, и вывод результата запроса к объекту класса(содержащего отсортированные данные).

    :param sort_data: Объект, содержащий отсортированные данные.

    :param date_key: Строка, содержащая дату в необходимом формате.

    :param name: Строка, содержащая наименование в необходимом формате.

    :param state: Строка, содержащая значение флага отрытия скважеины в необходимом формате.

    :return: Объект класса секций, совпадающий по параметрам запроса.

    """
    if date_key in sort_data.date:
        for index_descriptions in range(len(sort_data.date[date_key])):
            if sort_data.date[date_key][index_descriptions].flag == state and \
                    sort_data.date[date_key][index_descriptions].name == f"'{name}'":
                return sort_data.date[date_key][index_descriptions]
    return "No open in date"


if __name__ == '__main__':
    query = '01/09.2018', 'w2', 'OPeN'
    filename = 'test_schedule.inc'
    section_names = ['COMPDATL', 'COMPDAT', 'DATES']
    file_text = open_file(filename)
    file_text_sort_section_names = pars_file_text_keywords(file_text, section_names)
    sort_dict_and_list = sort_date_and_section_name(file_text_sort_section_names)
    sort_dict_and_list = formatting_allocation(*sort_dict_and_list)
    sort_data = sorting_to_class(*sort_dict_and_list)
    format_query = formatting_query_arguments(*query)
    query_results = show_query_results(sort_data, *format_query)
    print(query_results)

    doctest.testmod()
