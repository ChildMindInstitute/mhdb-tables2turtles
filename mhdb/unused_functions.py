#!/usr/bin/env python
"""
This program contains functions for working with spreadsheets and RDF text documents.

Authors:
    - Arno Klein, 2017-2019  (arno@childmind.org)  http://binarybottle.com
    - Jon Clucas, 2017 (jon.clucas@childmind.org)

Copyright 2017, Child Mind Institute (http://childmind.org), Apache v2.0 License

"""
import logging
import numpy as np
import pandas as pd
import sys


from mhdb.spreadsheet_io import download_google_sheet, get_cell
from mhdb.spreadsheet_io import split_on_slash
from mhdb.write_ttl import check_iri


def ICD_code(Disorder, ICD, id, X):
    # function to turtle ICD code and coding system
    ICD = str(ICD)
    ICD_uri_code = get_cell(
        Disorder,
        'ICD{0}code'.format(ICD),
        iD,
        X,
        True
    )
    if ICD_uri_code:
        ICD_uri = "ICD{0}:{1}".format(
            ICD,
            str(ICD_uri_code)
        )
        ICD_coding_string = (
            "{0} health-lifesci:codingSystem \"ICD{1}CM\"^^rdfs:Literal "
        ).format(
            ICD_uri,
            ICD
        )
    else:
        ICD_uri, ICD_coding_string = None, None
    return(ICD_uri, ICD_coding_string)


def disorder_iri(index, mentalhealth_xls=None, pre_specifiers_indices=[6, 7, 24, 25, 26],
                 post_specifiers_indices=[27, 28, 56, 78]):
    """
    Function to figure out IRIs for disorders based on
    mentalhealth.xls::Disorder
    Parameters
    ----------
    index: int
        key to lookup in Disorder table
    mentalhealth_xls: spreadsheet workbook, optional
        1MfW9yDw7e8MLlWWSBBXQAC2Q4SDiFiMMb7mRtr7y97Q
    pre_specifiers_indices: [int], optional
        list of indices of diagnostic specifiers to precede disorder names
    post_specifiers_indices: [int], optional
        list of indices of diagnostic specifiers to be preceded by disorder
        names
    Returns
    -------
    statements: dictionary
        key: string
            RDF subject
        value: dictionary
            key: string
                RDF predicate
            value: {string}
                set of RDF objects

    Example
    -------
    disorder_statements = {}
    if disorder_iris and len(disorder_iris):
        for disorder in disorder_iris:
            disorder_statements = disorder_iri(
                disorder,
                mentalhealth_xls=mentalhealth_xls,
                pre_specifiers_indices=[
                    6,
                    7,
                    24,
                    25,
                    26
                ],
                post_specifiers_indices=[
                    27,
                    28,
                    56,
                    78
                ]
            )
            statements = add_if(
                project_iri,
                "dcterms:subject",
                [
                    k for k in disorder_statements
                ][0],
                {
                    **statements,
                    **disorder_statements
                }
            )

    """
    disorder = mentalhealth_xls.parse("Disorder")
    severity = mentalhealth_xls.parse("DisorderSeverity")
    specifier = mentalhealth_xls.parse("DiagnosticSpecifier")
    criterion = mentalhealth_xls.parse("DiagnosticCriterion")
    disorderSeries = disorder[disorder["index"]==index]
    disorder_name = disorderSeries["DisorderName"].values[0]
    if (
        not isinstance(
            disorderSeries["DiagnosticSpecifier_index"].values[0],
            float
        )
    ) or (
        not np.isnan(
            disorderSeries["DiagnosticSpecifier_index"].values[0]
        )
    ):
        disorder_name = " ".join([
            specifier[
                specifier[
                    "index"
                ]==disorderSeries[
                    "DiagnosticSpecifier_index"
                ].values[0]
            ]["DiagnosticSpecifierName"].values[0],
            disorder_name
        ]) if disorderSeries[
            "DiagnosticSpecifier_index"
        ].values[0] in pre_specifiers_indices else " ".join([
            disorder_name,
            specifier[
                specifier[
                    "index"
                ]==disorderSeries[
                    "DiagnosticSpecifier_index"
                ].values[0]
            ]["DiagnosticSpecifierName"].values[0]
        ]) if disorderSeries[
            "DiagnosticSpecifier_index"
        ].values[0] in post_specifiers_indices else ", ".join([
            disorder_name,
            specifier[
                specifier[
                    "index"
                ]==disorderSeries[
                    "DiagnosticSpecifier_index"
                ].values[0]
            ]["DiagnosticSpecifierName"].values[0]
        ])
    disorder_name = " with ".join([
        disorder_name,
        criterion[
            criterion["index"]==disorderSeries[
                "DiagnosticInclusionCriterion_index"
            ]
        ]["DiagnosticCriterionName"].values[0]
    ]) if (
        not isinstance(
            disorderSeries["DiagnosticInclusionCriterion_index"].values[0],
            float
        )
    ) or (
        not np.isnan(
            disorderSeries["DiagnosticInclusionCriterion_index"].values[0]
        )
    ) else disorder_name
    disorder_name = " and ".join([
        disorder_name,
        criterion[
            criterion["index"]==disorderSeries[
                "DiagnosticInclusionCriterion2_index"
            ]
        ]["DiagnosticCriterionName"].values[0]
    ]) if (
        not isinstance(
            disorderSeries["DiagnosticInclusionCriterion2_index"].values[0],
            float
        )
    ) or (
        not np.isnan(
            disorderSeries["DiagnosticInclusionCriterion2_index"].values[0]
        )
    ) else disorder_name
    disorder_name = " without ".join([
        disorder_name,
        criterion[
            criterion["index"]==disorderSeries[
                "DiagnosticExclusionCriterion_index"
            ]
        ]["DiagnosticCriterionName"].values[0]
    ]) if (
        not isinstance(
            disorderSeries["DiagnosticExclusionCriterion_index"].values[0],
            float
        )
    ) or (
        not np.isnan(
            disorderSeries["DiagnosticExclusionCriterion_index"].values[0]
        )
    ) else disorder_name
    disorder_name = " and ".join([
        disorder_name,
        criterion[
            criterion["index"]==disorderSeries[
                "DiagnosticExclusionCriterion2_index"
            ]
        ]["DiagnosticCriterionName"].values[0]
    ]) if (
        not isinstance(
            disorderSeries["DiagnosticExclusionCriterion2_index"].values[0],
            float
        )
    ) or (
        not np.isnan(
            disorderSeries["DiagnosticExclusionCriterion2_index"].values[0]
        )
    ) else disorder_name
    disorder_name = " ".join([
        severity[
            severity[
                "index"
            ]==int(disorderSeries[
                "DisorderSeverity_index"
            ])
        ]["DisorderSeverityName"].values[0],
        disorder_name
    ]) if (
        not isinstance(
            disorderSeries[
                "DisorderSeverity_index"
            ].values[0],
            float
        )
    ) or (
        not np.isnan(
            disorderSeries[
                "DisorderSeverity_index"
            ].values[0]
        )
    ) else disorder_name
    iri = check_iri(disorder_name)
    label = language_string(disorder_name)
    statements = {iri: {"rdfs:label": [label]}}
    return(statements)


def collect_predicates(subject, row, structure_row, files, stc, prefixes):
    """
    Function to collect predicates for a given subject

    Parameters
    ----------
    subject : string
        Turtle object

    row : Series
        row from structure_to_keep
        pandas series from generator
        ie, row[1] for row in iterrows()

    structure_row : Series
        row indicated in row from structure_to_keep
        pandas series from generator
        ie, structure_row[1] for structure_row in iterrows()

    files : dictionary
        {fn: string:
        file: DataFrame}
        one entry per unique value in structure_to_keep's "File" column

    stc : DataFrame

    prefixes : iterable of 2-tuples
        (prefix_string: string
        prefix_iri: string)
        defined RDF prefixes

    Returns
    -------
    related_predicates : set
        set of 2-tuples

        predicates[0]: string
            Turtle property

        predicates[1]: string
            Turtle object
    """
    def type_pred(row, prefixes):
        """
        Function to create and return a tuple of
        Turtle property and Turtle object for a
        given label

        Parameters
        ----------
        row : Series
            row from structure_to_keep
            pandas series from generator
            ie, row[1] for row in iterrows()

        prefixes : iterable of 2-tuples
            (prefix_string: string
            prefix_iri: string)
            defined RDF prefixes

        Returns
        -------
        predicate : 2-tuple
            predicate[0]: string
                Turtle property

            predicate[1]: string
                Turtle object
        """
        prop = "rdfs:subClassOf" if row[
                                        "Class, Property or Instance"
                                    ] == "Class" else "rdfs:subPropertyOf" if row[
                                                                                  "Class, Property or Instance"
                                                                              ] == "Property" else "rdfs:type"
        predicate = tuple(
            (
                prop,
                check_iri(
                    row["Type"],
                    prefixes
                )
            )
        ) if row["Type"] else None
        return (predicate)

    related_predicates = set()
    for related_row in stc.iterrows():
        if (
            related_row[1]["File"] == row.File
        ) and (
            related_row[1]["Sheet"] == row.Sheet
        ) and (
            related_row[1]["Indexed_Entity"] == row.Column_Header
        ):
            if related_row[1]["Type"] == "foreign key":
                for foreign_pred in foreign(
                    structure_row,
                    related_row[1],
                    files,
                    stc,
                    prefixes
                ):
                    related_predicates.add(foreign_pred)
            elif (
                row["Definition or Relationship"] in [
                    "rdfs:label",
                    "schema:text"
                ]
            ):
                related_predicates = related_predicates | label(
                    row,
                    structure_row,
                    prefixes
                )
            tp = type_pred(row, prefixes)
            if tp:
                related_predicates.add(tp)
    return(related_predicates)


def follow_fk(sheet, foreign_key_header, foreign_value_header, fk):
    """
    Function to follow foreign keys to IRIs.

    Parameters
    ----------
    sheet: DataFrame

    foreign_key_header: string

    foreign_value_header: string

    fk: int or string

    Returns
    -------
    iri: string
    """
    try:
        main_value = sheet.loc[
            sheet[foreign_key_header]==fk
        ][foreign_value_header].values[0]
        if isinstance(main_value, str):
            return(main_value)
        else:
            return(
                str(sheet.loc[
                    sheet[foreign_key_header]==fk
                ][foreign_value_backup_header].values[0])
            )
    except:
        logging.info("Unexpected error (follow_fk):\n\t\t{0}\n\t{1}\n".format(
            sys.exc_info()[0],
            "\t".join([
                foreign_key_header,
                foreign_value_header,
                str(fk)
            ])
        ))


def foreign(structure_row, related_row, files, stc, prefixes):
    """
    Function to follow (a) foreign key(s) and return a set of predicate tuples

    Parameters
    ----------
    structure_row : Series
        row indicated in row from structure_to_keep
        pandas series from generator
        ie, structure_row[1] for structure_row in iterrows()

    related_row : Series
        row indicated in row from structure_to_keep
        pandas series from generator
        ie, related_row[1] for related_row in iterrows()

    files : dictionary
        {fn: string:
        file: DataFrame}
        one entry per unique value in structure_to_keep's "File" column

    stc : DataFrame

    prefixes : iterable of 2-tuples
        (prefix_string: string
        prefix_iri: string)
        defined RDF prefixes

    Returns
    -------
    foreign_predicates: set of 2-tuples

        foreign_predicates[0]: string
            Turtle property

        foreign_predicates[1]: string
            Turtle object
    """
    foreign_predicates = set()
    fks = structure_row[
        related_row["Column_Header"]
    ]
    skb = related_row["split_key_by"]
    skb = skb if isinstance(skb, str) else None
    if isinstance(fks, float) and np.isnan(fks):
        return({})
    fks = [
        int(float(fk)) for fk in str(fks).split(skb)
    ] if skb else [fks]
    svb = related_row["split_value_by"]
    svb = svb if isinstance(svb, str) else None
    if len(fks):
        for fk in fks:
            fvalues = follow_fk(
                files[
                    related_row["Foreign File"]
                ].parse(
                    related_row[
                        "Foreign Sheet"
                    ]
                ),
                related_row[
                    "Foreign Key Column_Header"
                ],
                related_row[
                    "Foreign Value Column_Header"
                ],
                fk
            )
            if (
                (fvalues is None)
                or
                (fvalues=="None")
            ) and (
                not related_row[
                    "Foreign Value Column_Backup_Header"
                ] in [
                    None,
                    np.nan,
                    "",
                    "None"
                ]
            ):
                fvalues = follow_fk(
                    files[
                        related_row["Foreign File"]
                    ].parse(
                        related_row[
                            "Foreign Sheet"
                        ]
                    ),
                    related_row[
                        "Foreign Key Column_Header"
                    ],
                    related_row[
                        "Foreign Value Column_Backup_Header"
                    ],
                    fk
                )
            fvalues = fvalues.split(
                svb
            ) if svb and fvalues else [fvalues]
            if fvalues:
                for fvalue in fvalues:
                    foreign_predicates.add(
                        (
                            check_iri(
                                related_row[
                                    "Definition or Relationship"
                                ],
                                prefixes
                            ),
                            check_iri(
                                fvalue,
                                prefixes
                            )
                        )
                    )
    return(foreign_predicates)


def label(row, structure_row, prefixes):
    """
    Function to create and return a tuple of
    Turtle property and Turtle object for a
    given label

    Parameters
    ----------

    row : Series
        row from structure_to_keep
        pandas series from generator
        ie, row[1] for row in iterrows()

    structure_row : Series
        row indicated in row from structure_to_keep
        pandas series from generator
        ie, structure_row[1] for structure_row in iterrows()

    prefixes : iterable of 2-tuples
        (prefix_string: string
        prefix_iri: string)
        defined RDF prefixes


    Returns
    -------
    predicates : set of 2-tuples
        predicate[0]: string
            Turtle property

        predicate[1]: string
            Turtle object
    """
    texts = str(
        structure_row[
            row.Column_Header
        ]
    )
    texts = texts.split(
        row.split_indexed_by
    ) if (
        isinstance(
            row.split_indexed_by,
            str
        ) and (
            row.split_indexed_by in texts
        )
    ) else [texts]

    return(
        {
            tuple(
                (
                    check_iri(
                        row["Definition or Relationship"],
                        prefixes
                    ),
                    "\"\"\"{0}\"\"\"@en".format(
                        text.replace(
                            "\n",
                            " "
                        ).replace(
                            "\"",
                            "\\\""
                        ).strip()
                    )
                )
            ) for text in texts
        }
    )


def structure_to_keep(files, prefixes=None):
    """
    Parameter
    ---------
    files : dictionary of loaded Excel workbooks
        one entry per unique value in structure_to_keep's "File" column

    prefixes : iterable of 2-tuples
        (prefix_string: string
        prefix_iri: string)
        defined RDF prefixes

    Returns
    -------
    dicts: list of dictionaries
        default = [sourced, unsourced]
        sourced : dictionary
            dictionary of sourced triples
        unsourced : dictionary
            dictionary of unsourced triples
    """

    def follow_structure(row, files, stc, prefixes=None):
        """
        Function to follow format of "structure_to_keep"

        Parameters
        ----------
        row: Series
            pandas series from generator
            ie, row[1] for row in iterrows()

        files : dictionary
            {fn: string:
            file: DataFrame}
            one entry per unique value in structure_to_keep's "File" column

        stc : DataFrame

        prefixes : iterable of 2-tuples
            (prefix_string: string
            prefix_iri: string)
            defined RDF prefixes

        Returns
        -------
        ttl_dict : dictionary
            keys: str
                subjects
            values: sets of 2-tuple (str, str)
                [0]: predicate
                [1]: object
        """
        sheet = files[row.File].parse(row.Sheet)
        ttl_dict = dict()
        if row.Type != "foreign key":
            for structure_row in sheet.iterrows():
                subjects = structure_row[1][row.Indexed_Entity]
                if isinstance(subjects, str):
                    subjects = subjects.split(
                        row.split_indexed_by
                    ) if (
                            isinstance(
                                row.split_indexed_by,
                                str
                            ) and (
                                    row.split_indexed_by in subjects
                            )
                    ) else [subjects]
                    subject = check_iri(
                        subjects[0],
                        prefixes
                    )
                    related_predicates = collect_predicates(
                        subject,
                        row,
                        structure_row[1],
                        files,
                        stc,
                        prefixes
                    )
                    ttl_dict[subject] = related_predicates if (
                            subject not in ttl_dict
                    ) else (
                            ttl_dict[subject] |
                            related_predicates
                    )
        return (ttl_dict)

    dicts = [
        dict(),
        dict()
    ]
    stcFILE = download_google_sheet(
        'data/keep.xlsx',
        "1bQmu1emZ_9J1qfrzTi2CgTELME4mRqn74hMwbY9wV-A"
    )
    stc_xls = pd.ExcelFile(stcFILE)
    stc = split_on_slash(
        stc_xls.parse("Sheet1"),
        "Indexed_Entity"
    )
    indexed_entities = stc[
        [
            "File",
            "Sheet",
            "Indexed_Entity"
        ]
    ].drop_duplicates()
    ttl_string = None
    for row in stc.iterrows():
        if row[1][
            [
                "File",
                "Sheet",
                "Column_Header"
            ]
        ].values.tolist() in indexed_entities.values.tolist():
            row_dict = follow_structure(
                row[1],
                files,
                stc,
                prefixes
            )
            for subject in row_dict:
                if subject in dicts[0]:
                    dicts[0][subject] = dicts[0][subject] | row_dict[subject]
                else:
                    sourced = False
                    for predicate in row_dict[subject]:
                        if predicate[0] == "dcterms:isReferencedBy":
                            sourced = True
                    if sourced:
                        dicts[0][subject] = row_dict[subject]
                    else:
                        dicts[1][subject] = row_dict[subject] if (
                            subject not in dicts[1]
                        ) else dicts[1][subject] | row_dict[subject]
    return(dicts)


def doi_iri(doi, title=None, statements={}):
    """
    Function to create relevant statements about a DOI.

    Parameters
    ----------
    doi: string
        Digital Object Identifier

    title: string, optional
        title of digital object

    Returns
    -------
    statements: dictionary
        key: string
            RDF subject
        value: dictionary
            key: string
                RDF predicate
            value: {string}
                set of RDF objects

    Example
    -------
    >>> print([k for k in doi_iri(
    ...     "10.1109/IEEESTD.2015.7084073",
    ...     "1872-2015 - IEEE Standard Ontologies for Robotics and Automation"
    ... )][0])
    <https://dx.doi.org/10.1109/IEEESTD.2015.7084073>
    """
    local_iri = check_iri(
        'https://dx.doi.org/{0}'.format(
            doi
        )
    )
    doi = '"""{0}"""^^rdfs:Literal'.format(doi)
    for pred in [
        ("datacite:usesIdentifierScheme", "datacite:doi"),
        ("datacite:hasIdentifier", doi)
    ]:
        statements = add_if(
            local_iri,
            pred[0],
            pred[1],
            statements
        )
    return (
        add_if(
            local_iri,
            "rdfs:label",
            language_string(
                title
            ),
            statements
        ) if title else statements
    )


def object_split_lookup(object_indices, lookup_sheet, lookup_key_column,
                        lookup_value_column, separator=","):
    """
    Function to lookup values from comma-separated key columns.

    Parameters
    ----------
    object_indices: string
        maybe-separated string of foreign keys

    lookup_sheet: DataFrame
        foreign table

    lookup_key_column: string
        foreign table key column header

    lookup_value_column: string
        foreign table value column header

    separator: string
        default=","

    Returns
    -------
    object_iris: list of strings
        list of Turtle-formatted IRIs or empty list if none

    Example
    -------
    >>> import pandas as pd
    >>> sheet = pd.DataFrame({
    ...     "index": list(range(3)),
    ...     "bird": [":duck", ":goose", ":swan"]
    ... })
    >>> print(object_split_lookup(
    ...     object_indices="0/2",
    ...     lookup_sheet=sheet,
    ...     lookup_key_column="index",
    ...     lookup_value_column="bird",
    ...     separator="/"
    ... ))
    [':duck', ':swan']
    """
    try:
        if not isinstance(
                object_indices,
                float
        ) and len(str(object_indices).strip()):
            object_indices = str(object_indices)
            if separator not in object_indices:
                object_iris = [check_iri(
                    lookup_sheet[
                        lookup_sheet[
                            lookup_key_column
                        ] == int(
                            object_indices
                        )
                        ][lookup_value_column].values[0]
                )] if lookup_sheet[
                    lookup_sheet[
                        lookup_key_column
                    ] == int(
                        object_indices
                    )
                    ][lookup_value_column].values.size else None
            else:
                object_iris = [
                    int(
                        s.strip()
                    ) for s in object_indices.split(
                        separator
                    )
                ]
                object_iris = [check_iri(
                    lookup_sheet[
                        lookup_sheet[lookup_key_column] == object_i
                        ][lookup_value_column].values[0]
                ) for object_i in object_iris]
            return (object_iris)
        else:
            return ([])
    except:
        print(str(lookup_value_column))
        print(str(object_indices))
        return ([])


def gen_questions(nb, p1=None, s1=None, dim_p1=None):
    """
    Generate the questions we can from the given prefixes and suffixes

    Parameters
    ----------
    nb: string
        "neutral behaviour"

    p1: string, optional
        prefix string

    dim_p1: string, optional
        prefix string

    s1: string, optional
        prefix string

    Returns
    -------
    qs: list of strings
        list of questions
    """
    qs = []
    nb = nb.strip()
    p1 = p1.strip() if p1 else None
    s1 = s1.strip().strip("?") if s1 else None
    dim_p1 = dim_p1.strip() if dim_p1 else None
    if p1:
        qs.append("{0} {1}?".format(p1, nb))
        if s1:
            qs.append("{0} {1} {2}?".format(p1, nb, s1))
            if dim_p1:
                qs.append("{3} {0} {1} {2}?".format(p1, nb, s1, dim_p1))
        elif dim_p1:
            qs.append("{2} {0} {1}?".format(p1, nb, dim_p1))
    elif s1:
        qs.append("{0} {1}?".format(nb, s1))
        if dim_p1:
            qs.append("{2} {0} {1}?".format(nb, s1, dim_p1))
    return(qs)
