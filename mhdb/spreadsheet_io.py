#!/usr/bin/env python
"""
This program contains generic input/output functions
to read from a spreadsheet and return desired types/formats.

Authors:
    - Arno Klein, 2017-2020  (arno@childmind.org)  http://binarybottle.com
    - Jon Clucas, 2017 (jon.clucas@childmind.org)

Copyright 2020, Child Mind Institute (http://childmind.org), Apache v2.0 License

"""
import os
import pandas as pd
import urllib.request as urllibrequest #import urllib


def download_google_sheet(filepath, docid):
    """
    Download latest version of a Google Sheet

    Parameters
    ----------
    filepath : string

    docid : string

    Returns
    -------
    filepath : string
    """
    if not os.path.exists(os.path.abspath(os.path.dirname(filepath))):
        os.makedirs(os.path.abspath(os.path.dirname(filepath)))
    urllibrequest.urlretrieve("{1}{0}{2}".format(
        docid,
        'https://docs.google.com/spreadsheets/d/',
        '/export?format=xlsx'
        ), filepath)
    return filepath


def return_none_for_nan(input_value):
    """
    Return None if input is a NaN value; otherwise, return the input.

    Parameters
    ----------
    input_value : string or number or NaN

    Returns
    -------
    value_not_nan : string or number

    """
    import numpy as np

    def is_not_nan(s):
        if s:
            if isinstance(s, float) and np.isnan(s):
                return False
            elif str(s) in ['NaN', 'nan']:
                return False
            else:
                return True
        else:
            return False

    if is_not_nan(input_value):
        return input_value
    else:
        return None


def return_float(input_number):
    """
    Return input as a float if it's a number (or string of a number).

    Parameters
    ----------
    input_number : string or number

    Returns
    -------
    output_number : float
        raise exception if not a number or string of a number

    """
    import numpy as np

    def is_number(s):
        if s:
            if isinstance(s, float) and np.isnan(s):
                return False
            else:
                try:
                    float(s)
                    return True
                except ValueError:
                    return False
        else:
            return False

    if is_number(input_number):
        return float(input_number)
    else:
        return None


def get_cell(worksheet, column_label, index, exclude=[], no_nan=True):
    """
    Fetch a worksheet cell given a row index and column header.

    Parameters
    ----------
    worksheet : pandas dataframe
        worksheet with column headers
    column_label : string
        worksheet column header
    index : integer
        worksheet row index
    exclude : list
        exclusion list
    no_nan : Boolean
        return None if NaN?

    Returns
    -------
    cell : string or number
        worksheet cell

    """
    from mhdb.spreadsheet_io import return_none_for_nan

    if column_label in worksheet.columns:
        column = worksheet[column_label]
        if index < len(column):
            cell = column[index]
            if no_nan:
                cell = return_none_for_nan(cell)
            if exclude and cell in exclude:
                return None
            else:
                return cell
        else:
            raise Exception("index={0} for column length {1}.".
                            format(index, len(column)))
    else:
        return None
        #raise Exception("column {0} not in worksheet.".format(column_label))


def get_index2(worksheet1, column1_label, index1, worksheet2):
    """
    Find the location of an 'index' value in a worksheet.

    If index1 points to a row of column1 in worksheet1, the cell contains
    an integer value. Find the corresponding row of the "index" column
    in worksheet2 with that value.

    Parameters
    ----------
    worksheet1 : pandas dataframe
        worksheet with column headers
    column1_label : string
        worksheet1 column header
    index1 : integer
        worksheet1 row index
    worksheet2 : pandas dataframe
        second worksheet with 'index' column header

    Returns
    -------
    index2 : integer
        worksheet2 row index

    """
    #import pandas as pd

    from mhdb.spreadsheet_io import get_cell
    from mhdb.spreadsheet_io import return_float

    cell = get_cell(worksheet1, column1_label, index1, exclude=[], no_nan=True)
    if cell:
        index1to2 = return_float(cell)
        if index1to2:
            try:
                index_column = worksheet2['index']
                if any(index_column.isin([index1to2])):
                    index2 = index_column[index_column == index1to2].index[0]
                    return index2
                else:
                    return None
            except ValueError:
                raise Exception("Either the worksheet2 doesn't exist or "
                                "it doesn't have an 'index' column.")
        else:
            return None
    else:
        return None


def get_cells(worksheet, index, worksheet2=None, exclude=[], no_nan=True):
    """
    Get cells from a worksheet with the following column headers:
    "equivalentClass"
    "subClassOf"
    "propertyDomain"
    "propertyRange"
    "Definition"
    "DefinitionReference_index"

    Where "DefinitionReference_index" points to worksheet2 column headers:
    "ReferenceName"
    "ReferenceLink"

    Parameters
    ----------
    worksheet : pandas dataframe
        worksheet with column headers
    index : integer
        worksheet row index
    worksheet2 : pandas dataframe
        second worksheet with definition reference information
    exclude : list
        exclusion list
    no_nan : Boolean
        return None for NaN values?

    Returns
    -------
    equivalent_class_uri : string
        equivalentClass URI
    subclassof_uri : string
        subClassOf URI
    property_domain : string
        property domain
    property_range : string
        property range
    definition : string
        definition string
    definition_source_name : string
        definition source name
    definition_source_uri : string
        definition source URI

    """
    from mhdb.spreadsheet_io import get_cell
    from mhdb.spreadsheet_io import get_index2

    # equivalentClass and subClassOf:
    equivalent_class_uri = get_cell(worksheet, 'equivalentClass', index, exclude, True)
    subclassof_uri = get_cell(worksheet, 'subClassOf', index, exclude, True)

    # Property domain and range:
    property_domain = get_cell(worksheet, 'propertyDomain', index, exclude, True)
    property_range = get_cell(worksheet, 'propertyRange', index, exclude, True)

    # Definition, reference and link:
    definition = get_cell(worksheet, 'Definition', index, exclude, True)
    definition_ref = None
    definition_ref_uri = None
    if worksheet2 is not None:
        index2 = get_index2(worksheet, 'DefinitionReference_index', index,
                            worksheet2)
        if index2:
            definition_ref = get_cell(worksheet2, 'ReferenceName', index2, exclude, True)
            definition_ref_uri = get_cell(worksheet2, 'ReferenceLink', index2, exclude, True)

    return equivalent_class_uri, subclassof_uri, \
           property_domain, property_range, \
           definition, definition_ref, definition_ref_uri


def split_on_slash(df, column, delimiter=" / "):
    """
    Function to build appropriate rows when
    splitting cells in a named column by
    " / " or named delimiter

    Parameters
    ----------
    df: DataFrame

    column: string

    delimiter: string, optional

    Returns
    -------
    df: DataFrame
    """
    df[column] = pd.Series(df[column].apply(lambda x: trysplit(
        x,
        delimiter
    )))
    s = df.apply(
        lambda x:
            pd.Series(
                x[column]
            ),
            axis=1
    ).stack().reset_index(
        level=1,
        drop=True
    )
    s.name = column
    return(df.drop(column, axis=1).join(s))


def trysplit(x, delimiter):
    """
    Function to split only if string, otherwise return x

    Parameters
    ----------
    x: anything, hopefully string

    delimiter: string

    Returns
    -------
    x: same type as parameter x
    """
    if isinstance(x, str):
        return(x.split(delimiter))
    else:
        return(x)

# def create_uri(base_uri, label):
#     """
#     Create a safe URI.
#
#     Parameters
#     ----------
#     base_uri : string
#         base URI
#     label : string
#         input string
#
#     Returns
#     -------
#     output_uri : string
#         output URI
#
#     """
#     from mhdb.spreadsheet_io import convert_string_to_label
#
#     label_safe = convert_string_to_label(label)
#     output_uri = base_uri + "#" + label_safe
#
#     return output_uri
#
#
# def write_triple(subject_string, predicate_string, object_string,
#                  third_literal=False):
#     """
#     Write a triple from three URIs.
#
#     Parameters
#     ----------
#     subject_string : string
#         subject URI
#     predicate_string : string
#         predicate URI or in ['a', 'rdf:type']
#     object_string : string
#         object URI or literal
#     third_literal : Boolean
#         is the object_string a literal?
#
#     Returns
#     -------
#     output_triple : string
#         output triple
#
#     """
#
#     if predicate_string not in ['a', 'rdf:type']:
#         predicate_string = "<0>".format(predicate_string)
#     if not third_literal:
#         object_string = "<0>".format(object_string)
#
#     output_triple = "<{0}> {1} {2}".format(subject_string,
#                                            predicate_string,
#                                            object_string)
#
#     return output_triple
