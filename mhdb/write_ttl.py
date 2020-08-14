#!/usr/bin/env python3
"""
This program contains generic functions to build a Turtle (Terse RDF Triple Language) document.

Authors:
    - Arno Klein, 2017-2020 (arno@childmind.org)  http://binarybottle.com
    - Jon Clucas, 2017–2018 (jon.clucas@childmind.org)

Copyright 2020, Child Mind Institute (http://childmind.org), Apache v2.0 License

"""
import os
import sys
top_dir = os.path.abspath(os.path.join(
    (__file__),
    os.pardir,
    os.pardir
))
if top_dir not in sys.path:
    sys.path.append(top_dir)
import numpy as np


def language_string(s, lang="en"):
    """
    Function to encode a literal as being in a specific language.

    Parameters
    ----------
    s : string

    lang : string
        ISO character code, default="en"

    Returns
    -------
    s : string
        triple quoted Turtle literal with language encoding

    Example
    -------
    >>> print(language_string("Canada goose"))
    \"""Canada goose\"""@en
    """
    return(
        "\"\"\"{0}\"\"\"@{1}".format(
            return_string(
                s,
                [
                    '"'
                ],
                [
                    "'"
                ]
            ),
            lang
        )
    )


def return_string(input_string, replace=[], replace_with=[]):
    """
    Return a stripped string with optional character replacements.

    Parameters
    ----------
    input_string : string
        arbitrary string
    replace : list of strings
        strings to substitute
    replace_with : list of strings
        strings with which to substitute 'replace' strings

    Returns
    -------
    output_string : string
        stripped input_string

    """

    if input_string:
        if not isinstance(input_string, str):
            input_string = str(input_string)
        output_string = input_string.replace(
            "\n",
            " "
        ).replace(
            "\"",
            "\\\""
        ).strip()
        if replace:
            if len(replace) == len(replace_with):
                for i, s in enumerate(replace):
                    output_string = output_string.replace(s, replace_with[i])
                return output_string
            else:
                raise Exception("replace and replace_with should be the same length.")
        else:
            return output_string
    else:
        return ""


def create_label(input_string):
    """
    Clean up a string and create a corresponding (shortened) label.

    Parameters
    ----------
    input_string : string
        arbitrary string

    Returns
    -------
    output_string : string
        stripped input_string
    label_string : string
        alphanumeric characters of input_string

    """
    from mhdb.spreadsheet_io import return_string
    from mhdb.spreadsheet_io import convert_string_to_label

    if input_string:
        if isinstance(input_string, str):
            output_string = return_string(input_string,
                                          replace=['"', '\n'],
                                          replace_with=['', ''])
            if output_string:
                label_string = convert_string_to_label(output_string)
                return output_string, label_string
            else:
                return '', ''
        else:
            raise Exception('input_string is not a string!')
    else:
        raise Exception('input_string is None!')


def convert_string_to_label(input_string, label_type='delimited'):
    """
    Remove all non-alphanumeric characters from a string.

    Parameters
    ----------
    input_string : string
        input string

    label_type: string
        'PascalCase', 'camelCase', or 'delimited'
        ('delimited' uses '_' delimiters and keeps hyphens)

    Returns
    -------
    output_string : string
        output string

    """

    def toPascal(s):
        """
        Usage: toPascal("WRITE this in pascalcase")
        'WriteThisInPascalCase'
        """
        return ''.join(x for x in s.title() if not x.isspace())

    def toCamel(s):
        """
        Usage: toCamel("WRITE this in camelcase")
        'writeThisInCamelcase'
        (from: https://stackoverflow.com/questions/8347048/
               how-to-convert-string-to-title-case-in-python)

        """
        ret = s.split(' ')
        return ret[0].lower() + \
               ''.join(x.title() for x in ret[1:] if not x.isspace())

    def toDelimit(s):
        """
        Usage: toDelimit("WRITE this-in delimited")
        'WRITE_this-in_delimited'

        """
        while " " in s:
            s = s.replace(" ", "_")
        while "__" in s:
            s = s.replace("__", "_")
        s = s.replace("_-_", "-")
        while "--" in s:
            s = s.replace("--", "-")

        return s

    # input_string = return_string(input_string,
    #                              replace=['"', '\n'],
    #                              replace_with=['', ''])

    if input_string:
        if label_type == 'PascalCase':
            output_string = toPascal(input_string)
        elif label_type == 'camelCase':
            output_string = toCamel(input_string)
        elif label_type == 'delimited':
            output_string = toDelimit(input_string)
        else:
            Exception('label_type input is incorrect')
        keep_chars = ('-', '_')

        output_string = "".join(c for c in str(output_string) if c.isalnum()
                                or c in keep_chars).rstrip()
        #output_string = ''.join(x for x in output_string if not x.isspace())

        return output_string
    else:
        raise Exception('"{0}" is not a string!'.format(input_string))


def check_iri(iri, label_type='delimited'):
    """
    Function to format IRIs by type, such as <iri> or prefix:iri

    Parameters
    ---------
    iri: string

    label_type: string
        'PascalCase', 'camelCase', or 'delimited'
        ('delimited' uses '_' delimiters and keeps hyphens)

    Removed:
    prefixes: set of 2-or-3-tuples
    prefixes={("mhdb", "mhdb-states", "mhdb-disorders", "mhdb-resources",
               "mhdb-assessments", "mhdb-measures")}

    Returns
    -------
    iri: string
    """

    #prefix_strings = {"","_"} if not prefixes else {
    #    "",
    #    "_",
    #    *[prefix[0] for prefix in prefixes]
    #}

    iri = str(iri).strip()

    if ":" in iri and not [x for x in iri if x.isspace()]:
        if iri.endswith(":"):
            return check_iri(iri[:-1], label_type) #, prefixes)
        elif ":/" in iri and \
                 not iri.startswith('<') and not iri.endswith('>'):
            return "<{0}>".format(convert_string_to_label(iri, label_type))
        # elif iri.split(":")[0] in prefix_strings:
        #     return iri
        else:
            return iri
    else:
        return ":" + convert_string_to_label(iri, label_type)


def turtle_from_dict(ttl_dict):
    """
    Function to convert a dictionary to a Terse Triple Language string

    Parameters
    ----------
    ttl_dict: dictionary
        key: string
            RDF subject
        value: dictionary
            key: string
                RDF predicate
            value: {string}
                set of RDF objects

    Returns
    -------
    ttl_string: str
        ttl

    Example
    -------
    >>> turtle_from_dict({
    ...     "duck": {
    ...         "continues": {
    ...             "sitting"
    ...         }
    ...     },
    ...    "goose": {
    ...         "begins": {
    ...             "chasing"
    ...         }
    ...     }
    ... })
    'duck continues sitting .\\n\\ngoose begins chasing .'
    """
    x = [
        ":None",
        ":nan",
        "nan",
        np.nan,
        None
    ]
    return(
        "\n\n".join([
            "{0} {1} .".format(
                subject,
                " ;\n\t".join([
                    "{0} {1}".format(
                        predicate,
                        object
                    ) for predicate in ttl_dict[
                        subject
                    ] for object in ttl_dict[
                        subject
                    ][
                        predicate
                    ]
                ])
            ) for subject in ttl_dict
        ])
    )


def write_about_statement(subject, predicate, object, predicates):
    """
    Function to write one or more rdf statements in terse triple format.

    Parameters
    ----------
    subject: string
        subject of this statement

    predicate: string
        predicate of this statement

    object: string
        object of this statement

    predicates: iterable of 2-tuples
        predicate: string
            nth property

        object: string
            nth object

    Returns
    -------
    ttl_string: string
        Turtle string

    Example
    -------
    >>> statement = {"duck": {"continues": {"sitting"}}}
    >>> predicates = {
    ...     ("source", '"Duck Duck Goose"'),
    ...     ("statementType", "role")
    ... }
    >>> for subject in statement:
    ...     for predicate in statement[subject]:
    ...         for object in statement[subject][predicate]:
    ...             print(len(write_about_statement(
    ...                 subject, predicate, object, predicates
    ...             )))
    168
    """
    return(
        write_ttl(
            "_:{0}".format(create_label("_".join([
                subject,
                predicate,
                object
            ]))),
            [
                ("rdf:type", "rdf:Statement"),
                ("rdf:subject", subject),
                ("rdf:predicate", predicate),
                ("rdf:object", object),
                *predicates
            ]
        )
    )


def write_header(base_uri, base_prefix, version, label, comment, prefixes):
    """
    Print out the beginning of an RDF text file.

    Parameters
    ----------
    base_uri : string
        base URI
    base_prefix : string
        base prefix
    version : string
        version
    label : string
        label
    comment : string
        comment
    prefixes : list
        list of 2-or-3-tuples of TTL prefix strings and prefix IRIs
        each tuple is
            [0] a prefix string
            [1] an iri string
            [2] an optional import URL
        eg, ("owl", "http://www.w3.org/2002/07/owl#")

    REMOVED:
    imports : Boolean, optional, default=False
        import external ontologies?

    Returns
    -------
    header : string
        owl header
    """

    header = write_header_prefixes(base_uri, base_prefix, prefixes)

    header = """{4}<{0}> a owl:Ontology ;
    owl:versionIRI <{0}/{1}> ;
    owl:versionInfo "{1}"^^rdfs:Literal ;
    rdfs:label "{2}"^^rdfs:Literal ;
    rdfs:comment \"\"\"{3}\"\"\"@en .

""".format(base_uri, version, label, comment, header)

    return header


def write_header_prefixes(base_uri, base_prefix, prefixes):
    """
    Write turtle-formatted header prefix string for list of (prefix, iri) tuples.

    Parameter
    ---------
    base_uri : string
        base URI

    base_prefix : string
        base prefix

    prefixes: list of 2 or 3-tuples
        each tuple is
            [0] a prefix string
            [1] an iri string
            [2] an optional import URL

    REMOVED:
    imports : Boolean, optional, default=False
        import external ontologies?

    Returns
    -------
    header_prefix: string
    """

    header_prefix = ""

    for prefix in prefixes:
        header_prefix="""{0}PREFIX {1}: <{2}> \n""".format(
            header_prefix,
            prefix[0],
            prefix[1]
        )

    #header_prefix = """{0}\nBASE <{1}#> \n""".format(
    #    header_prefix, base_uri
    #)

    header_prefix = """{0}\nPREFIX : <{1}#> \n""".format(
        header_prefix, base_uri
    )

    # if imports:
    #     header_prefix = """{0}\n<> owl:imports {1} .\n\n""".format(
    #         header_prefix,
    #         " ,\n\t".join(
    #             [check_iri(prefix[1])
    #                 if ((len(prefix) < 3) or (isinstance(prefix[2], float))
    #                 ) else check_iri(prefix[2]) for prefix in prefixes if (
    #                      (prefix[0] not in [base_prefix]) and
    #                      (prefix[1] not in [base_uri])
    #                 )
    #             ]
    #         )
    #     )

    return header_prefix


def write_ttl(subject, predicates, common_statements=None):
    """
    Function to write one or more rdf statements in terse triple format.

    Parameters
    ----------
    subject: string
        subject of all triples in these statements

    predicates: iterable of 2-tuples
        statements about subject
        predicate: string
            nth property

        object: string
            nth object

    common_statements: iterable of 2-tuples, optional
        statements about all previous statements
        predicate: string
            nth property

        object: string
            nth object

    Returns
    -------
    ttl_string: string
        Turtle string
    """
    ttl_string = ""
    if common_statements:
        ttl_string = "\n\n".join([
        write_about_statement(
            subject,
            predicate[0],
            predicate[1],
            common_statements
        ) for predicate in predicates
    ])
    ttl_string = "{0}\n\n".format(ttl_string) if len(ttl_string) else ""
    ttl_string = "".join([
        ttl_string,
        "{0} {1} .".format(
            subject,
            " ;\n\t".join([
                " ".join([
                    predicate[0],
                    predicate[1]
                ]) for predicate in predicates
            ])
        )
    ])
    return(ttl_string)
