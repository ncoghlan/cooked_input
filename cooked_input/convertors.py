"""
This file contains convertors classes for cooked_input

Author: Len Wanger
Copyright: Len Wanger, 2017
"""

import dateparser
import csv
from io import StringIO
from future.utils import raise_from
from abc import ABCMeta, abstractmethod


from .error_callbacks import ConvertorError


TABLE_ID = 0
TABLE_VALUE = 1
TABLE_ID_OR_VALUE = -1


###
### Convertors:
###
class Convertor(object):
    # Abstract base class for conversion classes
    __metaclass__ = ABCMeta

    def __init__(self, value_error_str):
        self.value_error_str = value_error_str

    @abstractmethod
    def __call__(self, value, error_callback, convertor_fmt_str):
        pass


class IntConvertor(Convertor):
    """
    convert the cleaned input to an integer.

    :param base:  the radix base to use for the int conversion (default=10)
    :param value_error_str: (optional) the error string to use when an improper value is input

    :return: an `int` value


    Legal values for the `base` parameter are 0 and 2-36. See the Python `int <https://docs.python.org/3/library/functions.html#int>`_
    built-in function for more information.
    """
    def __init__(self, base=10, value_error_str='an integer number'):
        self._base = base
        super(IntConvertor, self).__init__(value_error_str)

    def __call__(self, value, error_callback, convertor_fmt_str):
        try:
            return int(value, self._base)
        except (ValueError) as ve:
            error_callback(convertor_fmt_str, value, self.value_error_str)
            raise_from(ConvertorError(str(ve)), ve)

    def __repr__(self):
        return 'IntConvertor(base=%d, value_error_str=%s)' % (self._base, self.value_error_str)


class FloatConvertor(Convertor):
    """
    convert to a floating point number.

    :param value_error_str: (optional) the error string to use when an improper value is input

    :return: a `float` value

    """
    def __init__(self, value_error_str='a float number'):
        super(FloatConvertor, self).__init__(value_error_str)

    def __call__(self, value, error_callback, convertor_fmt_str):
        try:
            return float(value)
        except ValueError as ve:
            error_callback(convertor_fmt_str, value, self.value_error_str)
            raise_from(ConvertorError(str(ve)), ve)

    def __repr__(self):
        return 'FloatConvertor(%s)' % self.value_error_str


class BooleanConvertor(Convertor):
    """
    convert to a boolean value (**True** or **False**.)

    :param value_error_str: (optional) the error string to use when an improper value is input

    :return: a `boolean` value


    `BooleanConvertor` returns **True** for input values: 't', 'true', 'y', 'yes', and '1'. `BooleanConvertor` returns
    **False** for input values: 'f', 'false', 'n', 'no', '0'.
    """
    def __init__(self, value_error_str='true or false'):
        super(BooleanConvertor, self).__init__(value_error_str)

    def __call__(self, value, error_callback, convertor_fmt_str):
        true_set = {'t', 'true', 'y', 'yes', '1'}
        false_set = {'f', 'false', 'n', 'no', '0'}

        if value.lower() in true_set:
            return True
        elif value.lower() in false_set:
            return False
        else:
            error_callback(convertor_fmt_str, value, self.value_error_str)
            raise ConvertorError('value not true or false.')

    def __repr__(self):
        return 'BooleanConvertor(%s)' % self.value_error_str


class ListConvertor(Convertor):
    """
    convert to a list.

    :param value_error_str: (optional) the error string for improper value inputs
    :param delimiter: (optional) the single character delimiter to use for parsing the list. If None, will sniff the value
        (ala CSV library.)
    :param elem_convertor: (optional) the convertor function to use for each element of the list (e.g. setting `elem_convertor` to
        `IntConvertor` will return a list where each element is an integer

    :return: a `list` values, where each item in the list is of the type returned by `elem_convertor`

    For example, the accept a list of integers separated by colons (':') and return it as a Python list of ints::

      prompt_str = 'Enter a list of integers (separated by ":")'
      lc = ListConvertor(delimiter=':', elem_convertor=IntConvertor())
      result = get_input(prompt=prompt_str, convertor=lc)
    """
    def __init__(self, value_error_str='list of values', delimiter=',', elem_convertor=None):
        self._delimeter = delimiter
        self._elem_convertor = elem_convertor
        super(ListConvertor, self).__init__(value_error_str)


    def __call__(self, value, error_callback, convertor_fmt_str):
        buffer = StringIO(value)

        if self._delimeter is None:
            dialect = csv.Sniffer().sniff(value)
            dialect.skipinitialspace = True
        else:
            csv.register_dialect('my_dialect', delimiter=self._delimeter, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True)
            dialect = csv.get_dialect('my_dialect')

        reader = csv.reader(buffer, dialect)
        lst = next(reader)

        try:
            if self._elem_convertor:
                converted_list = [self._elem_convertor(item, error_callback, convertor_fmt_str) for item in lst]
            else:
                converted_list = lst
        except ConvertorError:
            raise ConvertorError(self._elem_convertor.value_error_str)

        return converted_list

    def __repr__(self):
        return 'ListConvertor(%s)' % self.value_error_str


class DateConvertor(Convertor):
    """
    convert to a `datetime <https://docs.python.org/3/library/datetime.html#datetime.datetime>`_ value.

    :param value_error_str: (optional) the error string to use when an improper value is input

    :return: a `datetime <https://docs.python.org/3/library/datetime.html#datetime.datetime>`_ value

    Converts the cleaned input to an datetime value. Dateparser is used for the parsing, allowing
    a lot of flexibility in how date input is entered (e.g. '12/12/12', 'October 1, 2015', 'today', or 'next Tuesday').
    For more information about dateparser see: `<https://dateparser.readthedocs.io/en/latest/>`_
    """
    def __init__(self, value_error_str='a date'):
        super(DateConvertor, self).__init__(value_error_str)

    def __call__(self, value, error_callback, convertor_fmt_str):
        result = dateparser.parse(value)
        if result:
            return result
        else:
            error_callback(convertor_fmt_str, value, self.value_error_str)
            raise ConvertorError('value not a valid date')

    def __repr__(self):
        return 'DateConvertor(%s)' % self.value_error_str


class YesNoConvertor(Convertor):
    """
    convert to 'yes' or 'no'.

    :param value_error_str: (optional) the error string to use when an improper value is input

    :return: a string set to either **"yes"** or **"no"**


    **YesNoConvertor** returns `yes` for input values: 'y', 'yes', 'yeah', 'yup', 'aye', 'qui', 'si', 'ja', 'ken',
    'hai', 'gee', 'da', 'tak', 'affirmative'. `YesNoConvertor` returns `no` for input values: 'n', 'no', 'nope',
    'na', 'nae', 'non', 'negatory', 'nein', 'nie', 'nyet', 'lo'.
    """
    def __init__(self, value_error_str='yes or no'):
        super(YesNoConvertor, self).__init__(value_error_str)

    def __call__(self, value, error_callback, convertor_fmt_str):
        yes_set = {'y', 'yes', 'yeah', 'yup', 'aye', 'qui', 'si', 'ja', 'ken', 'hai', 'gee', 'da', 'tak', 'affirmative'}
        no_set = {'n', 'no', 'nope', 'na', 'nae', 'non', 'negatory', 'nein', 'nie', 'nyet', 'lo'}

        if value.lower() in yes_set:
            return 'yes'
        elif value.lower() in no_set:
            return 'no'
        else:
            error_callback(convertor_fmt_str, value, self.value_error_str)
            raise ConvertorError('value not yes or no.')

    def __repr__(self):
        return 'YesNoConvertor(%s)' % self.value_error_str


class ChoiceConvertor(Convertor):
    """
    Convert a value to its mapped value in a dictionary.

    :param value_dict:  a dictionary containing keys to map from and values to map to
    :param value_error_str: (optional) the error string to use when an improper value is input

    :return: the `value` associated with the choice in ``value_dict`` (e.g. `value_dict[value]`)

    convert a value to it's return value in a dictionary (i.e. value_dict[value]). Can be used to map the row
    index from a table of values or to map multiple tags to a single choice.

    For example, to use a number to pick from a list of colors::

      value_map = {'1': 'red', '2': 'green', '3': 'blue'}
      choice_convertor = ci.ChoiceConvertor(value_dict=value_map)
      result = ci.get_input(convertor=choice_convertor, prompt='Pick a color (1 - red, 2 - green, 3 - blue)')
    """
    def __init__(self, value_dict, value_error_str='a valid row number'):
        self._choices = value_dict
        super(ChoiceConvertor, self).__init__(value_error_str)

    def __call__(self, value, error_callback, convertor_fmt_str):
        try:
            return self._choices[value]
        except (KeyError) as ve:
            error_callback(convertor_fmt_str, value, self.value_error_str)
            raise_from(ConvertorError(str(ve)), ve)

    def __repr__(self):
        return 'ChoiceConvertor(choices={}, value_error_str={})'.format(self._choices, self.value_error_str)
