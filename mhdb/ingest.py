#!/usr/bin/env python3
"""
This script contains specific functions to interpret a specific set of
spreadsheets

Authors:
    - Arno Klein, 2019-2020 (arno@childmind.org)  http://binarybottle.com
    - Jon Clucas, 2017–2018 (jon.clucas@childmind.org)

Copyright 2020, Child Mind Institute (http://childmind.org), Apache v2.0 License

"""
try:
    from mhdb.spreadsheet_io import download_google_sheet
    from mhdb.write_ttl import check_iri, mhdb_iri_simple, language_string
except:
    from mhdb.mhdb.spreadsheet_io import download_google_sheet
    from mhdb.mhdb.write_ttl import check_iri, mhdb_iri_simple, language_string
import numpy as np
import pandas as pd
import re

emptyValue = 'EmptyValue'
exclude_list = [emptyValue, '', [], 'NaN', 'NAN', 'nan', np.nan, None]


def add_to_statements(subject, predicate, object, statements={},
                      exclude_list=exclude_list):
    """
    Function to add predicate and object to a dictionary, after checking predicate.

    Parameters
    ----------
    subject: string
    predicate: string
    object: string
    statements: dictionary
    exclude_list: list
        do not add statement if it contains any of these

    Return
    ------
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
    >>> print(add_to_statements(":goose", ":chases", ":it"))
    {':goose': {':chases': {':it'}}}
    """
    if subject not in exclude_list and \
        predicate not in exclude_list and \
        object not in exclude_list:
        subject.strip()
        predicate.strip()
        object.strip()

        if subject not in statements:
            statements[subject] = {}
        if predicate not in statements[subject]:
            statements[subject][predicate] = {
                object
            }
        else:
            statements[subject][predicate].add(
                object
            )

    return statements


def ingest_states(states_xls, statements={}):
    """
    Function to ingest states spreadsheet

    Parameters
    ----------
    states_xls: pandas ExcelFile

    statements:  dictionary
        key: string
            RDF subject
        value: dictionary
            key: string
                RDF predicate
            value: {string}
                set of RDF objects

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
    """

    # load worksheets as pandas dataframes
    state_classes = states_xls.parse("Classes")
    state_properties = states_xls.parse("Properties")
    states = states_xls.parse("states")
    state_types = states_xls.parse("state_types")

    # fill NANs with emptyValue
    state_classes = state_classes.fillna(emptyValue)
    state_properties = state_properties.fillna(emptyValue)
    states = states.fillna(emptyValue)
    state_types = state_types.fillna(emptyValue)

    statements = audience_statements(statements)

    # Classes worksheet
    for row in states_classes.iterrows():
        class_label = language_string(row[1]["ClassName"])
        class_iri = mhdb_iri_simple(row[1]["ClassName"])
        predicates_list = []
        predicates_list.append(("rdfs:label", class_label))
        predicates_list.append(("a", "rdf:Class"))
        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["sameAs"] not in exclude_list:
            predicates_list.append(("owl:sameAs", row[1]["sameAs"]))
        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                             equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))
        if row[1]["subClassOf"] not in exclude_list:
            predicates_list.append(("rdfs:subClassOf",
                                    mhdb_iri_simple(row[1]["subClassOf"])))
        for predicates in predicates_list:
            statements = add_to_statements(
                class_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # Properties worksheet
    for row in states_properties.iterrows():
        property_label = language_string(row[1]["property"])
        property_iri = mhdb_iri_simple(row[1]["property"])
        predicates_list = []
        predicates_list.append(("rdfs:label", property_label))
        predicates_list.append(("a", "rdf:Property"))
        if row[1]["propertyDomain"] not in exclude_list:
            predicates_list.append(("rdfs:domain",
                                    mhdb_iri_simple(row[1]["propertyDomain"])))
        if row[1]["propertyRange"] not in exclude_list:
            predicates_list.append(("rdfs:range",
                                    mhdb_iri_simple(row[1]["propertyRange"])))
        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["sameAs"] not in exclude_list:
            predicates_list.append(("owl:sameAs",
                                    row[1]["sameAs"]))
        if row[1]["equivalentProperty"] not in exclude_list:
            predicates_list.append(("rdfs:equivalentProperty",
                                    row[1]["equivalentProperty"]))
        if row[1]["subPropertyOf"] not in exclude_list:
            predicates_list.append(("rdfs:subPropertyOf",
                                    mhdb_iri_simple(row[1]["subPropertyOf"])))
        for predicates in predicates_list:
            statements = add_to_statements(
                property_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # states worksheet
    for row in states.iterrows():

        state_label = language_string(row[1]["state"])
        state_iri = check_iri(row[1]["state"])

        predicates_list = []
        predicates_list.append(("a", "m3-lite:DomainOfInterest"))
        predicates_list.append(("rdfs:label", state_label))

        indices_state_type = row[1]["indices_state_type"]
        if indices_state_type not in exclude_list:
            indices = [np.int(x) for x in
                       indices_state_type.strip().split(',') if len(x)>0]
            for index in indices:
                objectRDF = state_types[state_types["index"] ==
                                         index]["state_type"].values[0]
                if isinstance(objectRDF, str):
                    predicates_list.append((":hasDomainType",
                                            check_iri(objectRDF)))
        indices_state_category = row[1]["indices_state_category"]
        if indices_state_category not in exclude_list:
            indices = [np.int(x) for x in
                       indices_state_category.strip().split(',') if len(x)>0]
            for index in indices:
                objectRDF = states[states["index"] ==
                                         index]["state"].values[0]
                if isinstance(objectRDF, str):
                    predicates_list.append(("rdfs:subClassOf",
                                            check_iri(objectRDF)))

        for predicates in predicates_list:
            statements = add_to_statements(
                state_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # state_types worksheet
    for row in state_types.iterrows():

        state_type_label = language_string(row[1]["state_type"])
        state_type_iri = check_iri(row[1]["state_type"])

        predicates_list = []
        predicates_list.append(("a", ":DomainType"))
        predicates_list.append(("rdfs:label", state_type_label))

        for predicates in predicates_list:
            statements = add_to_statements(
                state_type_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    return statements


def ingest_disorders(disorders_xls, statements={}):
    """
    Function to ingest disorders spreadsheet

    Parameters
    ----------
    disorders_xls: pandas ExcelFile

    statements:  dictionary
        key: string
            RDF subject
        value: dictionary
            key: string
                RDF predicate
            value: {string}
                set of RDF objects

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
    >>> try:
    ...     from mhdb.spreadsheet_io import download_google_sheet
    ...     from mhdb.write_ttl import turtle_from_dict
    ... except:
    ...     from mhdb.mhdb.spreadsheet_io import download_google_sheet
    ...     from mhdb.mhdb.write_ttl import turtle_from_dict
    >>> import os
    >>> import pandas as pd
    >>> try:
    ...     disordersFILE = download_google_sheet(
    ...         'data/disorders.xlsx',
    ...         "13a0w3ouXq5sFCa0fBsg9xhWx67RGJJJqLjD_Oy1c3b0"
    ...     )
    ... except:
    ...     disordersFILE = 'data/disorders.xlsx'
    >>> disorders_xls = pd.ExcelFile(disordersFILE)
    >>> behaviors_xls = pd.ExcelFile(behaviorsFILE)
    >>> statements = ingest_disorders(disorders_xls, statements={})
    >>> print(turtle_from_dict({
    ...     statement: statements[
    ...         statement
    ...     ] for statement in statements if statement == ":despair"
    ... }).split("\\n\\t")[0])
    #mhdb:despair rdfs:label "despair"@en ;
    """
    import math

    # load worksheets as pandas dataframes
    disorders_classes = disorders_xls.parse("Classes")
    disorders_properties = disorders_xls.parse("Properties")
    disorders = disorders_xls.parse("disorders")
    sign_or_symptoms = disorders_xls.parse("sign_or_symptoms")
    examples_sign_or_symptoms = disorders_xls.parse("examples_sign_or_symptoms")
    severities = disorders_xls.parse("severities")
    diagnostic_specifiers = disorders_xls.parse("diagnostic_specifiers")
    diagnostic_criteria = disorders_xls.parse("diagnostic_criteria")
    disorder_categories = disorders_xls.parse("disorder_categories")
    disorder_subcategories = disorders_xls.parse("disorder_subcategories")
    disorder_subsubcategories = disorders_xls.parse("disorder_subsubcategories")
    disorder_subsubsubcategories = disorders_xls.parse("disorder_subsubsubcategories")
    references = disorders_xls.parse("references")

    # fill NANs with emptyValue
    disorders_classes = disorders_classes.fillna(emptyValue)
    disorders_properties = disorders_properties.fillna(emptyValue)
    disorders = disorders.fillna(emptyValue)
    sign_or_symptoms = sign_or_symptoms.fillna(emptyValue)
    examples_sign_or_symptoms = examples_sign_or_symptoms.fillna(emptyValue)
    severities = severities.fillna(emptyValue)
    diagnostic_specifiers = diagnostic_specifiers.fillna(emptyValue)
    diagnostic_criteria = diagnostic_criteria.fillna(emptyValue)
    disorder_categories = disorder_categories.fillna(emptyValue)
    disorder_subcategories = disorder_subcategories.fillna(emptyValue)
    disorder_subsubcategories = disorder_subsubcategories.fillna(emptyValue)
    disorder_subsubsubcategories = disorder_subsubsubcategories.fillna(emptyValue)
    references = references.fillna(emptyValue)

    # Classes worksheet
    for row in disorders_classes.iterrows():
        class_label = language_string(row[1]["ClassName"])
        class_iri = mhdb_iri_simple(row[1]["ClassName"])
        predicates_list = []
        predicates_list.append(("rdfs:label", class_label))
        predicates_list.append(("a", "rdf:Class"))
        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["sameAs"] not in exclude_list:
            predicates_list.append(("owl:sameAs", row[1]["sameAs"]))
        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                             equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))
        if row[1]["subClassOf"] not in exclude_list:
            predicates_list.append(("rdfs:subClassOf",
                                    mhdb_iri_simple(row[1]["subClassOf"])))
        for predicates in predicates_list:
            statements = add_to_statements(
                class_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # Properties worksheet
    for row in disorders_properties.iterrows():
        property_label = language_string(row[1]["property"])
        property_iri = mhdb_iri_simple(row[1]["property"])
        predicates_list = []
        predicates_list.append(("rdfs:label", property_label))
        predicates_list.append(("a", "rdf:Property"))
        if row[1]["propertyDomain"] not in exclude_list:
            predicates_list.append(("rdfs:domain",
                                    mhdb_iri_simple(row[1]["propertyDomain"])))
        if row[1]["propertyRange"] not in exclude_list:
            predicates_list.append(("rdfs:range",
                                    mhdb_iri_simple(row[1]["propertyRange"])))
        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["sameAs"] not in exclude_list:
            predicates_list.append(("owl:sameAs",
                                    row[1]["sameAs"]))
        if row[1]["equivalentProperty"] not in exclude_list:
            predicates_list.append(("rdfs:equivalentProperty",
                                    row[1]["equivalentProperty"]))
        if row[1]["subPropertyOf"] not in exclude_list:
            predicates_list.append(("rdfs:subPropertyOf",
                                    mhdb_iri_simple(row[1]["subPropertyOf"])))
        for predicates in predicates_list:
            statements = add_to_statements(
                property_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # sign_or_symptoms worksheet
    for row in sign_or_symptoms.iterrows():

        # sign or symptom?
        sign_or_symptom_number = np.int(row[1]["sign_or_symptom_number"])
        if sign_or_symptom_number == 1:
            sign_or_symptom = ":MedicalSign"
        elif sign_or_symptom_number == 2:
            sign_or_symptom = ":MedicalSymptom"
        else:
            sign_or_symptom = ":MedicalSignOrSymptom"

        # reference
        source = None
        if row[1]["index_reference"] not in exclude_list:
            source = references[references["index"] == row[1]["index_reference"]
                ]["title"].values[0]
            source_iri = check_iri(source)

        symptom_label = language_string(row[1]["sign_or_symptom"])
        symptom_iri = check_iri(row[1]["sign_or_symptom"])

        predicates_list = []
        predicates_list.append(("rdfs:label", symptom_label))
        predicates_list.append(("a", sign_or_symptom))
        predicates_list.append((":isReferencedBy", source_iri))

        # specific to females/males?
        if row[1]["index_gender"] not in exclude_list:
            if np.int(row[1]["index_gender"]) == 1:  # female
                predicates_list.append(
                    (":audienceType", ":Female"))
                predicates_list.append(
                    (":epidemiology", ":Female"))
            elif np.int(row[1]["index_gender"]) == 2:  # male
                predicates_list.append(
                    (":audienceType", ":Male"))
                predicates_list.append(
                    (":epidemiology", ":Male"))

        # indices for disorders
        indices_disorder = row[1]["indices_disorder"]
        if indices_disorder not in exclude_list:
            if isinstance(indices_disorder, str):
                indices_disorder = [np.int(x) for x in
                           indices_disorder.strip().split(',') if len(x) > 0]
            elif isinstance(indices_disorder, int):
                indices_disorder = [indices_disorder]
            for index in indices_disorder:
                disorder = disorders[disorders["index"] == index
                                    ]["disorder"].values[0]
                if isinstance(disorder, str):
                    if sign_or_symptom_number == 1:
                        predicates_list.append((":isMedicalSignOf",
                                                check_iri(disorder)))
                    elif sign_or_symptom_number == 2:
                        predicates_list.append((":isMedicalSymptomOf",
                                                check_iri(disorder)))
                    else:
                        predicates_list.append((":isMedicalSignOrSymptomOf",
                                                check_iri(disorder)))

        # Is the sign/symptom a subclass of other another sign/symptom?
        indices_sign_or_symptom = row[1]["indices_sign_or_symptom"]
        if indices_sign_or_symptom not in exclude_list:
            if isinstance(indices_sign_or_symptom, str):
                indices_sign_or_symptom = [np.int(x) for x in
                    indices_sign_or_symptom.strip().split(',') if len(x) > 0]
            elif isinstance(indices_sign_or_symptom, int):
                indices_sign_or_symptom = [indices_sign_or_symptom]
            for index in indices_sign_or_symptom:
                super_sign = sign_or_symptoms[sign_or_symptoms["index"] ==
                                              index]["sign_or_symptom"].values[0]
                if isinstance(super_sign, str):
                    predicates_list.append(("rdfs:subClassOf",
                                            check_iri(super_sign)))
        for predicates in predicates_list:
            statements = add_to_statements(
                symptom_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # examples_sign_or_symptoms worksheet
    for row in examples_sign_or_symptoms.iterrows():

        example_symptom_label = language_string(row[1]["examples_sign_or_symptoms"])
        example_symptom_iri = check_iri(row[1]["examples_sign_or_symptoms"])

        predicates_list = []
        predicates_list.append(("rdfs:label", example_symptom_label))

        indices_sign_or_symptom = row[1]["indices_sign_or_symptom"]
        if indices_sign_or_symptom not in exclude_list:
            if isinstance(indices_sign_or_symptom, str):
                indices_sign_or_symptom = [np.int(x) for x in
                           indices_sign_or_symptom.strip().split(',') if len(x) > 0]
            elif isinstance(indices_sign_or_symptom, int):
                indices_sign_or_symptom = [indices_sign_or_symptom]
            for index in indices_sign_or_symptom:
                objectRDF = sign_or_symptoms[sign_or_symptoms["index"] ==
                                             index]["sign_or_symptom"].values[0]
                if isinstance(objectRDF, str):
                    predicates_list.append((":isExampleOf",
                                            check_iri(objectRDF)))

        for predicates in predicates_list:
            statements = add_to_statements(
                example_symptom_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # severities worksheet
    for row in severities.iterrows():

        severity_label = language_string(row[1]["severity"])
        severity_iri = check_iri(row[1]["severity"])

        predicates_list = []
        predicates_list.append(("rdfs:label", severity_label))
        predicates_list.append(("a", ":DisorderSeverity"))

        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                             equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))
        if row[1]["subClassOf"] not in exclude_list:
            predicates_list.append(("rdfs:subClassOf",
                                    check_iri(row[1]["subClassOf"])))
        for predicates in predicates_list:
            statements = add_to_statements(
                severity_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # diagnostic_specifiers worksheet
    for row in diagnostic_specifiers.iterrows():
        if row[1]["diagnostic_specifier"] not in exclude_list:

            diagnostic_specifier_label = language_string(row[1]["diagnostic_specifier"])
            diagnostic_specifier_iri = check_iri(row[1]["diagnostic_specifier"])

            predicates_list = []
            predicates_list.append(("rdfs:label", diagnostic_specifier_label))
            predicates_list.append(("a", ":DiagnosticSpecifier"))

            if row[1]["equivalentClasses"] not in exclude_list:
                equivalentClasses = row[1]["equivalentClasses"]
                equivalentClasses = [x.strip() for x in
                                     equivalentClasses.strip().split(',') if
                                     len(x) > 0]
                for equivalentClass in equivalentClasses:
                    if equivalentClass not in exclude_list:
                        predicates_list.append(("rdfs:equivalentClass",
                                                equivalentClass))
            if row[1]["subClassOf"] not in exclude_list:
                predicates_list.append(("rdfs:subClassOf",
                                        check_iri(row[1]["subClassOf"])))
            for predicates in predicates_list:
                statements = add_to_statements(
                    diagnostic_specifier_iri,
                    predicates[0],
                    predicates[1],
                    statements,
                    exclude_list
                )

    # diagnostic_criteria worksheet
    for row in diagnostic_criteria.iterrows():
        if row[1]["diagnostic_criterion"] not in exclude_list:

            diagnostic_criterion_label = language_string(row[1]["diagnostic_criterion"])
            diagnostic_criterion_iri = check_iri(row[1]["diagnostic_criterion"])

            predicates_list = []
            predicates_list.append(("rdfs:label", diagnostic_criterion_label))
            predicates_list.append(("a", ":DiagnosticCriterion"))

            if row[1]["equivalentClasses"] not in exclude_list:
                equivalentClasses = row[1]["equivalentClasses"]
                equivalentClasses = [x.strip() for x in
                                     equivalentClasses.strip().split(',') if
                                     len(x) > 0]
                for equivalentClass in equivalentClasses:
                    if equivalentClass not in exclude_list:
                        predicates_list.append(("rdfs:equivalentClass",
                                                equivalentClass))
            if row[1]["subClassOf"] not in exclude_list:
                predicates_list.append(("rdfs:subClassOf",
                                        check_iri(row[1]["subClassOf"])))
            for predicates in predicates_list:
                statements = add_to_statements(
                    diagnostic_criterion_iri,
                    predicates[0],
                    predicates[1],
                    statements,
                    exclude_list
                )

    # disorders worksheet
    exclude_categories = []
    for row in disorders.iterrows():
        if row[1]["disorder"] not in exclude_list:

            disorder_label = row[1]["disorder"]
            disorder_iri_label = disorder_label

            predicates_list = []
            predicates_list.append(("a", ":Disorder"))

            if row[1]["equivalentClasses"] not in exclude_list:
                equivalentClasses = row[1]["equivalentClasses"]
                equivalentClasses = [x.strip() for x in
                                     equivalentClasses.strip().split(',') if
                                     len(x) > 0]
                for equivalentClass in equivalentClasses:
                    if equivalentClass not in exclude_list:
                        predicates_list.append(("rdfs:equivalentClass",
                                                equivalentClass))
            if row[1]["subClassOf"] not in exclude_list:
                predicates_list.append(("rdfs:subClassOf",
                                        check_iri(row[1]["subClassOf"])))
            if row[1]["note"] not in exclude_list:
                predicates_list.append((":hasNote",
                                        language_string(row[1]["note"])))
            if row[1]["ICD9CM"] not in exclude_list:
                ICD9 = str(row[1]["ICD9CM"])
                predicates_list.append((":hasICD9Code", "ICD9CM:" + ICD9))
                disorder_label += "; ICD9CM:{0}".format(ICD9)
                disorder_iri_label += " ICD9 {0}".format(ICD9)
            if row[1]["ICD10CM"] not in exclude_list:
                ICD10 = row[1]["ICD10CM"]
                predicates_list.append((":hasICD10Code", "ICD10CM:" + ICD10))
                disorder_label += "; ICD10CM:{0}".format(ICD10)
                disorder_iri_label += " ICD10 {0}".format(ICD10)
            if row[1]["index_diagnostic_specifier"] not in exclude_list:
                diagnostic_specifier = diagnostic_specifiers[
                diagnostic_specifiers["index"] == int(row[1]["index_diagnostic_specifier"])
                ]["diagnostic_specifier"].values[0]
                if isinstance(diagnostic_specifier, str):
                    predicates_list.append((":hasDiagnosticSpecifier",
                                            check_iri(diagnostic_specifier)))
                    disorder_label += "; specifier: {0}".format(diagnostic_specifier)
                    disorder_iri_label += " specifier {0}".format(diagnostic_specifier)

            if row[1]["index_diagnostic_inclusion_criterion"] not in exclude_list:
                diagnostic_inclusion_criterion = diagnostic_criteria[
                diagnostic_criteria["index"] == int(row[1]["index_diagnostic_inclusion_criterion"])
                ]["diagnostic_criterion"].values[0]
                if isinstance(diagnostic_inclusion_criterion, str):
                    predicates_list.append((":hasInclusionCriterion",
                                            check_iri(diagnostic_inclusion_criterion)))
                    disorder_label += \
                        "; inclusion: {0}".format(diagnostic_inclusion_criterion)
                    disorder_iri_label += \
                        " inclusion {0}".format(diagnostic_inclusion_criterion)

            if row[1]["index_diagnostic_inclusion_criterion2"] not in exclude_list:
                diagnostic_inclusion_criterion2 = diagnostic_criteria[
                diagnostic_criteria["index"] == int(row[1]["index_diagnostic_inclusion_criterion2"])
                ]["diagnostic_criterion"].values[0]
                if isinstance(diagnostic_inclusion_criterion2, str):
                    predicates_list.append((":hasInclusionCriterion",
                                            check_iri(diagnostic_inclusion_criterion2)))
                    disorder_label += \
                        ", {0}".format(diagnostic_inclusion_criterion2)
                    disorder_iri_label += \
                        " {0}".format(diagnostic_inclusion_criterion2)

            if row[1]["index_diagnostic_exclusion_criterion"] not in exclude_list:
                diagnostic_exclusion_criterion = diagnostic_criteria[
                diagnostic_criteria["index"] == int(row[1]["index_diagnostic_exclusion_criterion"])
                ]["diagnostic_criterion"].values[0]
                if isinstance(diagnostic_exclusion_criterion, str):
                    predicates_list.append((":hasExclusionCriterion",
                                            check_iri(diagnostic_exclusion_criterion)))
                    disorder_label += \
                        "; exclusion: {0}".format(diagnostic_exclusion_criterion)
                    disorder_iri_label += \
                        " exclusion {0}".format(diagnostic_exclusion_criterion)

            if row[1]["index_diagnostic_exclusion_criterion2"] not in exclude_list:
                diagnostic_exclusion_criterion2 = diagnostic_criteria[
                diagnostic_criteria["index"] == int(row[1]["index_diagnostic_exclusion_criterion2"])
                ]["diagnostic_criterion"].values[0]
                if isinstance(diagnostic_exclusion_criterion2, str):
                    predicates_list.append((":hasExclusionCriterion",
                                            check_iri(diagnostic_exclusion_criterion2)))
                    disorder_label += \
                        ", {0}".format(diagnostic_exclusion_criterion2)
                    disorder_iri_label += \
                        " {0}".format(diagnostic_exclusion_criterion2)

            if row[1]["index_severity"] not in exclude_list:
                severity = severities[
                severities["index"] == int(row[1]["index_severity"])
                ]["severity"].values[0]
                if isinstance(severity, str) and severity not in exclude_list:
                    predicates_list.append((":hasSeverity",
                                            check_iri(severity)))
                    disorder_label += \
                        "; severity: {0}".format(severity)
                    disorder_iri_label += \
                        " severity {0}".format(severity)

            if row[1]["index_disorder_subsubsubcategory"] not in exclude_list:
                disorder_subsubsubcategory = disorder_subsubsubcategories[
                    disorder_subsubsubcategories["index"] ==
                    int(row[1]["index_disorder_subsubsubcategory"])
                ]["disorder_subsubsubcategory"].values[0]
                disorder_subsubcategory = disorder_subsubcategories[
                    disorder_subsubcategories["index"] ==
                    int(row[1]["index_disorder_subsubcategory"])
                ]["disorder_subsubcategory"].values[0]
                disorder_subcategory = disorder_subcategories[
                    disorder_subcategories["index"] ==
                    int(row[1]["index_disorder_subcategory"])
                ]["disorder_subcategory"].values[0]
                disorder_category = disorder_categories[
                    disorder_categories["index"] ==
                    int(row[1]["index_disorder_category"])
                ]["disorder_category"].values[0]
                predicates_list.append(("rdfs:subClassOf",
                                        check_iri(disorder_subsubsubcategory)))
                statements = add_to_statements(
                    check_iri(disorder_subsubsubcategory),
                    "rdfs:subClassOf",
                    check_iri(disorder_subsubcategory),
                    statements,
                    exclude_list
                )
                if disorder_subsubcategory not in exclude_categories:
                    statements = add_to_statements(
                        check_iri(disorder_subsubcategory),
                        "rdfs:subClassOf",
                        check_iri(disorder_subcategory),
                        statements,
                        exclude_list
                    )
                    statements = add_to_statements(
                        check_iri(disorder_subcategory),
                        "rdfs:subClassOf",
                        check_iri(disorder_category),
                        statements,
                        exclude_list
                    )
                    exclude_categories.append(disorder_subsubcategory)
            elif row[1]["index_disorder_subsubcategory"] not in exclude_list:
                disorder_subsubcategory = disorder_subsubcategories[
                    disorder_subsubcategories["index"] ==
                    int(row[1]["index_disorder_subsubcategory"])
                ]["disorder_subsubcategory"].values[0]
                disorder_subcategory = disorder_subcategories[
                    disorder_subcategories["index"] ==
                    int(row[1]["index_disorder_subcategory"])
                ]["disorder_subcategory"].values[0]
                disorder_category = disorder_categories[
                    disorder_categories["index"] ==
                    int(row[1]["index_disorder_category"])
                ]["disorder_category"].values[0]
                predicates_list.append(("rdfs:subClassOf",
                                        check_iri(disorder_subsubcategory)))
                statements = add_to_statements(
                    check_iri(disorder_subsubcategory),
                    "rdfs:subClassOf",
                    check_iri(disorder_subcategory),
                    statements,
                    exclude_list
                )
                if disorder_subcategory not in exclude_categories:
                    statements = add_to_statements(
                        check_iri(disorder_subcategory),
                        "rdfs:subClassOf",
                        check_iri(disorder_category),
                        statements,
                        exclude_list
                    )
                    exclude_categories.append(disorder_subcategory)
            elif row[1]["index_disorder_subcategory"] not in exclude_list:
                disorder_subcategory = disorder_subcategories[
                    disorder_subcategories["index"] == int(row[1]["index_disorder_subcategory"])
                ]["disorder_subcategory"].values[0]
                disorder_category = disorder_categories[
                    disorder_categories["index"] == int(row[1]["index_disorder_category"])
                ]["disorder_category"].values[0]
                predicates_list.append(("rdfs:subClassOf",
                                        check_iri(disorder_subcategory)))
                if disorder_category not in exclude_categories:
                    statements = add_to_statements(
                        check_iri(disorder_subcategory),
                        "rdfs:subClassOf",
                        check_iri(disorder_category),
                        statements,
                        exclude_list
                    )
                    exclude_categories.append(disorder_category)
            elif row[1]["index_disorder_category"] not in exclude_list:
                disorder_category = disorder_categories[
                    disorder_categories["index"] == int(row[1]["index_disorder_category"])
                ]["disorder_category"].values[0]
                predicates_list.append(("rdfs:subClassOf",
                                        check_iri(disorder_category)))

            disorder_label = language_string(disorder_label)
            disorder_iri = check_iri(disorder_iri_label)
            predicates_list.append(("rdfs:label", disorder_label))
            for predicates in predicates_list:
                statements = add_to_statements(
                    disorder_iri,
                    predicates[0],
                    predicates[1],
                    statements,
                    exclude_list
                )

    # disorder_categories worksheet
    for row in disorder_categories.iterrows():
        if row[1]["disorder_category"] not in exclude_list:

            disorder_category_label = language_string(row[1]["disorder_category"])
            disorder_category_iri = check_iri(row[1]["disorder_category"])

            predicates_list = []
            predicates_list.append(("rdfs:label", disorder_category_label))
            predicates_list.append(("a", ":Disorder"))

            if row[1]["equivalentClasses"] not in exclude_list:
                equivalentClasses = row[1]["equivalentClasses"]
                equivalentClasses = [x.strip() for x in
                                     equivalentClasses.strip().split(',') if
                                     len(x) > 0]
                for equivalentClass in equivalentClasses:
                    if equivalentClass not in exclude_list:
                        predicates_list.append(("rdfs:equivalentClass",
                                                equivalentClass))
            if row[1]["subClassOf"] not in exclude_list:
                predicates_list.append(("rdfs:subClassOf",
                                        check_iri(row[1]["subClassOf"])))

            for predicates in predicates_list:
                statements = add_to_statements(
                    disorder_category_iri,
                    predicates[0],
                    predicates[1],
                    statements,
                    exclude_list
                )

    # disorder_subcategories worksheet
    for row in disorder_subcategories.iterrows():
        if row[1]["disorder_subcategory"] not in exclude_list:

            disorder_subcategory_label = language_string(row[1]["disorder_subcategory"])
            disorder_subcategory_iri = check_iri(row[1]["disorder_subcategory"])

            predicates_list = []
            predicates_list.append(("rdfs:label", disorder_subcategory_label))
            predicates_list.append(("a", ":Disorder"))

            if row[1]["equivalentClasses"] not in exclude_list:
                equivalentClasses = row[1]["equivalentClasses"]
                equivalentClasses = [x.strip() for x in
                                     equivalentClasses.strip().split(',') if
                                     len(x) > 0]
                for equivalentClass in equivalentClasses:
                    if equivalentClass not in exclude_list:
                        predicates_list.append(("rdfs:equivalentClass",
                                                equivalentClass))
            if row[1]["subClassOf"] not in exclude_list:
                predicates_list.append(("rdfs:subClassOf",
                                        check_iri(row[1]["subClassOf"])))

            for predicates in predicates_list:
                statements = add_to_statements(
                    disorder_subcategory_iri,
                    predicates[0],
                    predicates[1],
                    statements,
                    exclude_list
                )

    # disorder_subsubcategories worksheet
    for row in disorder_subsubcategories.iterrows():
        if row[1]["disorder_subsubcategory"] not in exclude_list:

            disorder_subsubcategory_label = language_string(row[1]["disorder_subsubcategory"])
            disorder_subsubcategory_iri = check_iri(row[1]["disorder_subsubcategory"])

            predicates_list = []
            predicates_list.append(("rdfs:label", disorder_subsubcategory_label))
            predicates_list.append(("a", ":Disorder"))

            if row[1]["equivalentClasses"] not in exclude_list:
                equivalentClasses = row[1]["equivalentClasses"]
                equivalentClasses = [x.strip() for x in
                                     equivalentClasses.strip().split(',') if
                                     len(x) > 0]
                for equivalentClass in equivalentClasses:
                    if equivalentClass not in exclude_list:
                        predicates_list.append(("rdfs:equivalentClass",
                                                equivalentClass))
            if row[1]["subClassOf"] not in exclude_list:
                predicates_list.append(("rdfs:subClassOf",
                                        check_iri(row[1]["subClassOf"])))

            for predicates in predicates_list:
                statements = add_to_statements(
                    disorder_subsubcategory_iri,
                    predicates[0],
                    predicates[1],
                    statements,
                    exclude_list
                )

    # disorder_subsubsubcategories worksheet
    for row in disorder_subsubsubcategories.iterrows():
        if row[1]["disorder_subsubsubcategory"] not in exclude_list:

            disorder_subsubsubcategory_label = language_string(row[1]["disorder_subsubsubcategory"])
            disorder_subsubsubcategory_iri = check_iri(row[1]["disorder_subsubsubcategory"])

            predicates_list = []
            predicates_list.append(("rdfs:label", disorder_subsubsubcategory_label))
            predicates_list.append(("a", ":Disorder"))

            if row[1]["equivalentClasses"] not in exclude_list:
                equivalentClasses = row[1]["equivalentClasses"]
                equivalentClasses = [x.strip() for x in
                                     equivalentClasses.strip().split(',') if
                                     len(x) > 0]
                for equivalentClass in equivalentClasses:
                    if equivalentClass not in exclude_list:
                        predicates_list.append(("rdfs:equivalentClass",
                                                equivalentClass))
            if row[1]["subClassOf"] not in exclude_list:
                predicates_list.append(("rdfs:subClassOf",
                                        check_iri(row[1]["subClassOf"])))

            for predicates in predicates_list:
                statements = add_to_statements(
                    disorder_subsubsubcategory_iri,
                    predicates[0],
                    predicates[1],
                    statements,
                    exclude_list
                )

    # references worksheet
    for row in references.iterrows():

        predicates_list = []

        # require title
        title = row[1]["title"]
        if title not in exclude_list:

            # reference IRI
            reference_iri = check_iri(title)
            predicates_list.append(("rdfs:label", language_string(title)))
            predicates_list.append((":hasTitle", language_string(title)))
            predicates_list.append(("a", ":BibliographicResource"))

            # general columns
            link = row[1]["link"]
            if link not in exclude_list:
                predicates_list.append((":hasHomePage", "<" + link.strip() + ">"))
            entry_date = row[1]["entry_date"]
            if entry_date not in exclude_list:
                predicates_list.append((":hasEntryDate", language_string(entry_date)))

            # research article-specific columns
            authors = row[1]["authors"]
            year = row[1]["year"]
            PubMedID = row[1]["PubMedID"]
            if authors not in exclude_list:
                predicates_list.append((":hasAuthorList", language_string(authors)))
            if year not in exclude_list:
                predicates_list.append((":hasPublicationYear",
                                        '"{0}"^^xsd:integer'.format(int(year))))
            if PubMedID not in exclude_list:
                predicates_list.append((":hasPubMedID",
                                        '"{0}"^^xsd:integer'.format(int(PubMedID))))

            for predicates in predicates_list:
                statements = add_to_statements(
                    reference_iri,
                    predicates[0],
                    predicates[1],
                    statements,
                    exclude_list
                )

    return statements


def ingest_resources(resources_xls, measures_xls, states_xls, statements={}):
    """
    Function to ingest resources spreadsheet

    Parameters
    ----------
    resources_xls: pandas ExcelFile

    states_xls: pandas ExcelFile

    measures_xls: pandas ExcelFile

    statements:  dictionary
        key: string
            RDF subject
        value: dictionary
            key: string
                RDF predicate
            value: {string}
                set of RDF objects

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
    """

    # load worksheets as pandas dataframes
    resources_classes = resources_xls.parse("Classes")
    resources_properties = resources_xls.parse("Properties")
    # guides worksheets
    guide_types = resources_xls.parse("guide_types")
    guides = resources_xls.parse("guides")
    # treatments, medications worksheets
    treatments = resources_xls.parse("treatments")
    medications = resources_xls.parse("medications")
    # projects worksheets
    project_types = resources_xls.parse("project_types")
    projects = resources_xls.parse("projects")
    groups = resources_xls.parse("groups")
    # guides and projects worksheets
    references = resources_xls.parse("references")
    # worksheets shared across mhdb
    people = resources_xls.parse("people")
    languages = resources_xls.parse("languages")
    licenses = resources_xls.parse("licenses")
    # imported (non-resources) worksheets
    #measures = measures_xls.parse("measures")
    #sensors = measures_xls.parse("sensors")
    #states = states_xls.parse("states")

    # fill NANs with emptyValue
    resources_classes = resources_classes.fillna(emptyValue)
    resources_properties = resources_properties.fillna(emptyValue)
    guide_types = guide_types.fillna(emptyValue)
    guides = guides.fillna(emptyValue)
    treatments = treatments.fillna(emptyValue)
    medications = medications.fillna(emptyValue)
    project_types = project_types.fillna(emptyValue)
    projects = projects.fillna(emptyValue)
    groups = groups.fillna(emptyValue)
    references = references.fillna(emptyValue)
    people = people.fillna(emptyValue)
    languages = languages.fillna(emptyValue)
    licenses = licenses.fillna(emptyValue)
    #measures = measures.fillna(emptyValue)
    #sensors = sensors.fillna(emptyValue)
    #states = states_xls.parse("states")

    # Classes worksheet
    for row in resources_classes.iterrows():
        class_label = language_string(row[1]["ClassName"])
        class_iri = mhdb_iri_simple(row[1]["ClassName"])
        predicates_list = []
        predicates_list.append(("rdfs:label", class_label))
        predicates_list.append(("a", "rdf:Class"))
        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["sameAs"] not in exclude_list:
            predicates_list.append(("owl:sameAs", row[1]["sameAs"]))
        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                             equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))
        if row[1]["subClassOf"] not in exclude_list:
            predicates_list.append(("rdfs:subClassOf",
                                    mhdb_iri_simple(row[1]["subClassOf"])))
        for predicates in predicates_list:
            statements = add_to_statements(
                class_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # Properties worksheet
    for row in resources_properties.iterrows():
        property_label = language_string(row[1]["property"])
        property_iri = mhdb_iri_simple(row[1]["property"])
        predicates_list = []
        predicates_list.append(("rdfs:label", property_label))
        predicates_list.append(("a", "rdf:Property"))
        if row[1]["propertyDomain"] not in exclude_list:
            predicates_list.append(("rdfs:domain",
                                    mhdb_iri_simple(row[1]["propertyDomain"])))
        if row[1]["propertyRange"] not in exclude_list:
            predicates_list.append(("rdfs:range",
                                    mhdb_iri_simple(row[1]["propertyRange"])))
        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["sameAs"] not in exclude_list:
            predicates_list.append(("owl:sameAs",
                                    row[1]["sameAs"]))
        if row[1]["equivalentProperty"] not in exclude_list:
            predicates_list.append(("rdfs:equivalentProperty",
                                    row[1]["equivalentProperty"]))
        if row[1]["subPropertyOf"] not in exclude_list:
            predicates_list.append(("rdfs:subPropertyOf",
                                    mhdb_iri_simple(row[1]["subPropertyOf"])))
        for predicates in predicates_list:
            statements = add_to_statements(
                property_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # guides worksheet
    for row in guides.iterrows():

        predicates_list = []

        # require title
        title = row[1]["title"]
        if title not in exclude_list:

            # guide IRI
            guide_iri = check_iri(title)
            predicates_list.append(("rdfs:label", language_string(title)))
            predicates_list.append((":hasTitle", language_string(title)))
            predicates_list.append(("a", ":BibliographicResource"))

            # link, entry date
            link = row[1]["link"]
            entry_date = row[1]["entry_date"]
            if link not in exclude_list:
                predicates_list.append((":hasHomePage",
                                        "<" + link.strip() + ">"))
            if entry_date not in exclude_list:
                predicates_list.append((":hasEntryDate",
                                        language_string(entry_date)))

            # research article-specific columns: authors, affiliation, pubdate
            authors = row[1]["authors"]
            affiliation = row[1]["affiliation"]
            pubdate = row[1]["pubdate"]
            if authors not in exclude_list:
                predicates_list.append((":hasAuthorList",
                                        language_string(authors)))
                if affiliation not in exclude_list:
                    statements = add_to_statements(
                        check_iri(authors), ":isMemberOf",
                        check_iri(affiliation), statements, exclude_list
                    )
            if pubdate not in exclude_list:
                predicates_list.append((":hasPublicationDate",
                                        language_string(pubdate)))

            # guide type
            indices_guide_type = row[1]["indices_guide_type"]
            if indices_guide_type not in exclude_list:
                if isinstance(indices_guide_type, str):
                    indices = [np.int(x) for x in
                               indices_guide_type.strip().split(',') if len(x)>0]
                elif isinstance(indices_guide_type, float):
                    indices = [np.int(indices_guide_type)]
                else:
                    indices = None
                if indices not in exclude_list:
                    for index in indices:
                        objectRDF = guide_types[
                            guide_types["index"] == index]["guide_type"].values[0]
                        if objectRDF not in exclude_list:
                            predicates_list.append((":hasReferenceType",
                                                    check_iri(objectRDF)))
            # specific to females/males?
            index_gender = row[1]["index_gender"]
            if index_gender not in exclude_list:
                if np.int(index_gender) == 1:  # female
                    predicates_list.append(
                        (":hasAudienceType", ":Female"))
                    predicates_list.append(
                        (":isAbout", ":Female"))
                elif np.int(index_gender) == 2:  # male
                    predicates_list.append(
                        (":hasAudienceType", ":Male"))
                    predicates_list.append(
                        (":isAbout", ":Male"))

            # audience, subject, language, license
            indices_audience = row[1]["indices_audience"]
            indices_subject = row[1]["indices_subject"]
            indices_language = row[1]["indices_language"]
            index_license = row[1]["index_license"]
            # if indices_audience not in exclude_list:
            #     indices = [np.int(x) for x in
            #                indices_audience.strip().split(',') if len(x)>0]
            #     for index in indices:
            #         objectRDF = people[
            #             people["index"] == index]["person"].values[0]
            #         if objectRDF not in exclude_list:
            #             predicates_list.append((":hasAudienceType",
            #                                     check_iri(objectRDF)))
            # if indices_subject not in exclude_list:
            #     indices = [np.int(x) for x in
            #                indices_subject.strip().split(',') if len(x)>0]
            #     for index in indices:
            #         objectRDF = people[
            #             people["index"] == index]["person"].values[0]
            #         if objectRDF not in exclude_list:
            #             predicates_list.append((":isAbout",
            #                                     check_iri(objectRDF)))
            # if indices_language not in exclude_list:
            #     indices = [np.int(x) for x in
            #                indices_language.strip().split(',') if len(x)>0]
            #     for index in indices:
            #         objectRDF = languages[
            #             languages["index"] == index]["language"].values[0]
            #         if objectRDF not in exclude_list:
            #             predicates_list.append((":hasLanguage",
            #                                     check_iri(objectRDF)))
            if index_license not in exclude_list:
                objectRDF = shared[licenses["index"] ==
                                       index_license]["license"].values[0]
                if objectRDF not in exclude_list:
                    predicates_list.append((":hasLicense", check_iri(objectRDF)))

            # indices to other worksheets about content of the shared
            #indices_state = row[1]["indices_state"]
            #indices_disorder = row[1]["indices_disorder"]
            #indices_disorder_category = row[1]["indices_disorder_category"]
            # if indices_state not in exclude_list:
            #     indices = [np.int(x) for x in
            #                indices_state.strip().split(',') if len(x)>0]
            #     for index in indices:
            #         objectRDF = states[states["index"] == index]["state"].values[0]
            #         if objectRDF not in exclude_list:
            #             predicates_list.append((":isAboutDomain",
            #                                     check_iri(objectRDF)))
            # if indices_disorder not in exclude_list:
            #     indices = [np.int(x) for x in
            #                indices_disorder.strip().split(',') if len(x)>0]
            #     for index in indices:
            #         objectRDF = disorders[disorders["index"] ==
            #                               index]["disorder"].values[0]
            #         if objectRDF not in exclude_list:
            #             predicates_list.append(("schema:about", check_iri(objectRDF)))
            # if indices_disorder_category not in exclude_list:
            #     indices = [np.int(x) for x in
            #                indices_disorder_category.strip().split(',') if len(x)>0]
            #     for index in indices:
            #         objectRDF = disorder_categories[disorder_categories["index"] ==
            #                          index]["disorder_category"].values[0]
            #         if objectRDF not in exclude_list:
            #             predicates_list.append(("schema:about", check_iri(objectRDF)))

            for predicates in predicates_list:
                statements = add_to_statements(
                    guide_iri,
                    predicates[0],
                    predicates[1],
                    statements,
                    exclude_list
                )

    # treatments worksheet
    for row in treatments.iterrows():

        predicates_list = []
        predicates_list.append(("a", ":Treatment"))
        predicates_list.append(("rdfs:label",
                                language_string(row[1]["treatment"])))
        treatment_iri = check_iri(row[1]["treatment"])

        # indices to parent classes
        if row[1]["indices_treatment"] not in exclude_list:
            indices = [np.int(x) for x in
                       row[1]["indices_treatment"].strip().split(',')
                       if len(x)>0]
            for index in indices:
                objectRDF = treatments[treatments["index"] ==
                                       index]["treatment"].values[0]
                if objectRDF not in exclude_list:
                    predicates_list.append(("rdfs:subClassOf",
                                            check_iri(objectRDF)))
        # aliases
        if row[1]["aliases"] not in exclude_list:
            aliases = row[1]["aliases"].split(',')
            for alias in aliases:
                predicates_list.append(("rdfs:label", language_string(alias)))

        # definition
        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))

        # equivalentClasses
        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                             equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))

        for predicates in predicates_list:
            statements = add_to_statements(
                treatment_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # medications worksheet
    for row in medications.iterrows():

        predicates_list = []
        predicates_list.append(("a", ":Medication"))
        predicates_list.append(("rdfs:label",
                                language_string(row[1]["medication"])))
        medication_iri = check_iri(row[1]["medication"])

        # indices to parent classes
        if row[1]["indices_medication"] not in exclude_list:
            indices = [np.int(x) for x in
                       row[1]["indices_medication"].strip().split(',')
                       if len(x)>0]
            for index in indices:
                objectRDF = medications[medications["index"] ==
                                       index]["medication"].values[0]
                if objectRDF not in exclude_list:
                    predicates_list.append(("rdfs:subClassOf",
                                            check_iri(objectRDF)))
        # aliases
        if row[1]["aliases"] not in exclude_list:
            aliases = row[1]["aliases"].split(',')
            for alias in aliases:
                predicates_list.append(("rdfs:label", language_string(alias)))

        # equivalentClasses
        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                             equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))

        for predicates in predicates_list:
            statements = add_to_statements(
                medication_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # projects worksheet
    for row in projects.iterrows():

        project_iri = check_iri(row[1]["project"])
        project_label = language_string(row[1]["project"])

        predicates_list = []
        predicates_list.append(("a", ":Project"))
        predicates_list.append(("rdfs:label", project_label))
        if row[1]["description"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["description"])))
        if row[1]["link"] not in exclude_list:
            predicates_list.append((":hasHomePage",
                                    "<" + row[1]["link"] + ">"))

        indices_project_type = row[1]["indices_project_type"]
        indices_group = row[1]["indices_group"]
        indices_sensor = row[1]["indices_sensor"]
        indices_measure = row[1]["indices_measure"]

        # references
        if row[1]["indices_reference"] not in exclude_list:
            indices = [np.int(x) for x in
                       row[1]["indices_reference"].strip().split(',') if len(x)>0]
            for index in indices:
                source = references[references["index"] == index]["title"].values[0]
                source_iri = check_iri(source)
                predicates_list.append((":isReferencedBy", source_iri))

        # project types
        if indices_project_type not in exclude_list:
            indices = [np.int(x) for x in
                       indices_project_type.strip().split(',') if len(x)>0]
            for index in indices:
                project_type_label = project_types[project_types["index"] ==
                                        index]["project_type"].values[0]
                project_type_iri = project_types[project_types["index"] ==
                                        index]["IRI"].values[0]
                if project_type_iri in exclude_list:
                    project_type_iri = project_type_label
                else:
                    predicates_list.append((":hasCategory",
                                            project_type_iri))
        # groups
        if indices_group not in exclude_list:
            indices = [np.int(x) for x in
                       indices_group.strip().split(',') if len(x)>0]
            for index in indices:

                if groups[groups["index"] == index]["group"].values[0] not in exclude_list:
                    groupname = groups[groups["index"] == index]["group"].values[0]
                else:
                    groupname = ""
                if groups[groups["index"] == index]["organization"].values[0] not in exclude_list:
                    orgname = groups[groups["index"] == index]["organization"].values[0]
                else:
                    orgname = ""
                objectRDF = groupname + orgname
                if objectRDF not in exclude_list:
                    predicates_list.append((":hasMaintainer",
                                            check_iri(objectRDF)))
        # # sensors and measures
        # if indices_sensor not in exclude_list:
        #     indices = [np.int(x) for x in
        #                indices_sensor.strip().split(',') if len(x)>0]
        #     for index in indices:
        #         objectRDF = sensors[sensors["index"] == index]["sensor"].values[0]
        #         if objectRDF not in exclude_list:
        #             predicates_list.append((":hasSubSystem",
        #                                     check_iri(objectRDF)))
        # if indices_measure not in exclude_list:
        #     indices = [np.int(x) for x in
        #                indices_measure.strip().split(',') if len(x)>0]
        #     for index in indices:
        #         objectRDF = measures[measures["index"] ==
        #                              index]["measure"].values[0]
        #         if objectRDF not in exclude_list:
        #             predicates_list.append((":observes",
        #                                     check_iri(objectRDF)))
        for predicates in predicates_list:
            statements = add_to_statements(
                project_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # project_types worksheet
    for row in project_types.iterrows():

        predicates_list = []
        predicates_list.append(("a", ":Category"))
        predicates_list.append(("rdfs:label",
                                language_string(row[1]["project_type"])))
        if row[1]["IRI"] not in exclude_list:
            project_type_iri = check_iri(row[1]["IRI"])
        else:
            project_type_iri = check_iri(row[1]["project_type"])

        if row[1]["indices_project_type"] not in exclude_list:
            indices = [np.int(x) for x in
                       row[1]["indices_project_type"].strip().split(',')
                       if len(x)>0]
            for index in indices:
                objectRDF = project_types[project_types["index"]  ==
                                          index]["project_type"].values[0]
                if objectRDF not in exclude_list:
                    predicates_list.append(("rdfs:subClassOf",
                                            check_iri(objectRDF)))
        for predicates in predicates_list:
            statements = add_to_statements(
                project_type_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # groups worksheet: require group or organization
    for row in groups.iterrows():

        predicates_list = []

        subject_iri = None
        if row[1]["group"] not in exclude_list:
            group_iri = check_iri(row[1]["group"])
            group_label = language_string(row[1]["group"])
            predicates_list.append(("a", ":Group"))
            predicates_list.append(("rdfs:label", group_label))
            subject_iri = group_iri

        if row[1]["organization"] not in exclude_list:
            organization_iri = check_iri(row[1]["organization"])
            statements = add_to_statements(organization_iri, "a",
                                           ":Organization", statements,
                                           exclude_list)
            statements = add_to_statements(organization_iri, "rdfs:label",
                                           language_string(
                                               row[1]["organization"]),
                                           statements, exclude_list)
            if subject_iri:
                predicates_list.append(
                    (":isPartOf", organization_iri))
            else:
                subject_iri = organization_iri

        if subject_iri:
            if row[1]["link"] not in exclude_list:
                predicates_list.append((":hasHomePage",
                                        "<" + row[1]["link"] + ">"))
            if row[1]["abbreviation"] not in exclude_list:
                predicates_list.append((":hasAbbreviation",
                                        check_iri(row[1]["abbreviation"])))
            if row[1]["member"] not in exclude_list:
                member_iri = check_iri(row[1]["member"])
                member_label = language_string(row[1]["member"])
                statements = add_to_statements(member_iri, "a", ":Person",
                                               statements, exclude_list)
                statements = add_to_statements(member_iri, ":hasName",
                                               member_label, statements,
                                               exclude_list)
                predicates_list.append((":hasMember", member_iri))

            for predicates in predicates_list:
                statements = add_to_statements(
                    subject_iri,
                    predicates[0],
                    predicates[1],
                    statements,
                    exclude_list
                )

    # languages worksheet
    for row in languages.iterrows():

        predicates_list = []
        predicates_list.append(("a", ":Language"))
        predicates_list.append(("rdfs:label",
                                language_string(row[1]["language"])))
        language_iri = check_iri(row[1]["language"])

        # indices to parent classes
        if row[1]["indices_language"] not in exclude_list:
            indices = [np.int(x) for x in
                       row[1]["indices_language"].strip().split(',')
                       if len(x)>0]
            for index in indices:
                objectRDF = languages[languages["index"] ==
                                       index]["language"].values[0]
                if objectRDF not in exclude_list:
                    predicates_list.append(("rdfs:subClassOf",
                                            check_iri(objectRDF)))
        # equivalentClasses
        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                             equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))

        for predicates in predicates_list:
            statements = add_to_statements(
                language_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # licenses worksheet
    for row in licenses.iterrows():

        predicates_list = []
        predicates_list.append(("a", ":License"))
        predicates_list.append(("rdfs:label",
                                language_string(row[1]["license"])))
        license_iri = check_iri(row[1]["license"])

        # abbreviation
        if row[1]["abbreviation"] not in exclude_list:
            abbreviation = row[1]["abbreviation"]
            predicates_list.append((":Abbreviation",
                                    language_string(abbreviation)))
        # description
        if row[1]["description"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["description"])))
        # link
        if row[1]["link"] not in exclude_list:
            predicates_list.append((":hasHomePage",
                                    "<" + row[1]["link"].strip() + ">"))
        # equivalentClasses
        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                             equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))

        for predicates in predicates_list:
            statements = add_to_statements(
                license_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # references worksheet
    for row in references.iterrows():

        predicates_list = []

        # require title
        title = row[1]["title"]
        if title not in exclude_list:

            # reference IRI
            reference_iri = check_iri(title)
            predicates_list.append(("rdfs:label", language_string(title)))
            predicates_list.append((":hasTitle", language_string(title)))
            predicates_list.append(("a", ":BibliographicResource"))

            # general columns
            link = row[1]["link"]
            if link not in exclude_list:
                predicates_list.append((":hasHomePage",
                                        "<" + link.strip() + ">"))
            entry_date = row[1]["entry_date"]
            if entry_date not in exclude_list:
                predicates_list.append((":hasEntryDate",
                                        language_string(entry_date)))

            # research article-specific columns
            authors = row[1]["authors"]
            year = row[1]["year"]
            PubMedID = row[1]["PubMedID"]
            if authors not in exclude_list:
                predicates_list.append((":hasAuthorList",
                                        language_string(authors)))
            if year not in exclude_list:
                predicates_list.append((":hasPublicationYear",
                                        '"{0}"^^xsd:integer'.format(int(year))))
            if PubMedID not in exclude_list:
                predicates_list.append((":hasPubMedID",
                                        '"{0}"^^xsd:integer'.format(int(PubMedID))))

            for predicates in predicates_list:
                statements = add_to_statements(
                    reference_iri,
                    predicates[0],
                    predicates[1],
                    statements,
                    exclude_list
                )

    return statements


def ingest_assessments(assessments_xls, resources_xls, statements={}):
    """
    Function to ingest assessments spreadsheet

    Parameters
    ----------
    assessments_xls: pandas ExcelFile

    statements:  dictionary
        key: string
            RDF subject
        value: dictionary
            key: string
                RDF predicate
            value: {string}
                set of RDF objects

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
    """

    # load worksheets as pandas dataframes
    assessments_classes = assessments_xls.parse("Classes")
    assessments_properties = assessments_xls.parse("Properties")
    # questions
    questionnaires = assessments_xls.parse("questionnaires")
    questions = assessments_xls.parse("questions")
    response_types = assessments_xls.parse("response_types")
    # tasks
    tasks = assessments_xls.parse("tasks")
    implementations = assessments_xls.parse("task_implementations")
    indicators = assessments_xls.parse("task_indicators")
    conditions = assessments_xls.parse("task_conditions")
    contrasts = assessments_xls.parse("task_contrasts")
    assertions_indices = assessments_xls.parse("task_assertions_indices")
    references = assessments_xls.parse("references")
    projects = resources_xls.parse("projects")

    # fill NANs with emptyValue
    assessments_classes = assessments_classes.fillna(emptyValue)
    assessments_properties = assessments_properties.fillna(emptyValue)
    questionnaires = questionnaires.fillna(emptyValue)
    questions = questions.fillna(emptyValue)
    response_types = response_types.fillna(emptyValue)
    tasks = tasks.fillna(emptyValue)
    implementations = implementations.fillna(emptyValue)
    indicators = indicators.fillna(emptyValue)
    conditions = conditions.fillna(emptyValue)
    contrasts = contrasts.fillna(emptyValue)
    assertions_indices = assertions_indices.fillna(emptyValue)
    references = references.fillna(emptyValue)
    projects = projects.fillna(emptyValue)

    #statements = audience_statements(statements)

    # Classes worksheet
    for row in assessments_classes.iterrows():
        class_label = language_string(row[1]["ClassName"])
        class_iri = mhdb_iri_simple(row[1]["ClassName"])
        predicates_list = []
        predicates_list.append(("rdfs:label", class_label))
        predicates_list.append(("a", "rdf:Class"))
        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["sameAs"] not in exclude_list:
            predicates_list.append(("owl:sameAs", row[1]["sameAs"]))
        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                             equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))
        if row[1]["subClassOf"] not in exclude_list:
            predicates_list.append(("rdfs:subClassOf",
                                    mhdb_iri_simple(row[1]["subClassOf"])))
        for predicates in predicates_list:
            statements = add_to_statements(
                class_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # Properties worksheet
    for row in assessments_properties.iterrows():
        property_label = language_string(row[1]["property"])
        property_iri = mhdb_iri_simple(row[1]["property"])
        predicates_list = []
        predicates_list.append(("rdfs:label", property_label))
        predicates_list.append(("a", "rdf:Property"))
        if row[1]["propertyDomain"] not in exclude_list:
            predicates_list.append(("rdfs:domain",
                                    mhdb_iri_simple(row[1]["propertyDomain"])))
        if row[1]["propertyRange"] not in exclude_list:
            predicates_list.append(("rdfs:range",
                                    mhdb_iri_simple(row[1]["propertyRange"])))
        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["sameAs"] not in exclude_list:
            predicates_list.append(("owl:sameAs",
                                    row[1]["sameAs"]))
        if row[1]["equivalentProperty"] not in exclude_list:
            predicates_list.append(("rdfs:equivalentProperty",
                                    row[1]["equivalentProperty"]))
        if row[1]["subPropertyOf"] not in exclude_list:
            predicates_list.append(("rdfs:subPropertyOf",
                                    mhdb_iri_simple(row[1]["subPropertyOf"])))
        for predicates in predicates_list:
            statements = add_to_statements(
                property_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # questionnaires worksheet
    for row in questionnaires.iterrows():

        predicates_list = []

        # require title
        title = row[1]["title"]
        if title not in exclude_list:

            # reference IRI
            questionnaire_iri = check_iri(title)
            predicates_list.append(("rdfs:label", language_string(title)))
            predicates_list.append((":hasTitle", language_string(title)))
            predicates_list.append(("a", ":BibliographicResource"))

            # general columns
            link = row[1]["link"]
            description = row[1]["description"]
            abbreviation = row[1]["abbreviation"]
            entry_date = row[1]["entry_date"]
            if link not in exclude_list:
                predicates_list.append((":hasHomePage", check_iri(link)))
            if description not in exclude_list:
                predicates_list.append(("rdfs:comment",
                                        language_string(description)))
            if abbreviation not in exclude_list:
                predicates_list.append((":hasAbbreviation",
                                        language_string(abbreviation)))
            if entry_date not in exclude_list:
                predicates_list.append((":hasEntryDate",
                                        language_string(entry_date)))

            # # specific to females/males?
            # index_gender = row[1]["index_gender"]
            # if index_gender not in exclude_list:
            #     if np.int(index_gender) == 1:  # female
            #         predicates_list.append(
            #             ("schema:audienceType", "schema:Female"))
            #         predicates_list.append(
            #             ("schema:epidemiology", "schema:Female"))
            #     elif np.int(index_gender) == 2:  # male
            #         predicates_list.append(
            #             ("schema:audienceType", "schema:Male"))
            #         predicates_list.append(
            #             ("schema:epidemiology", "schema:Male"))

            # research article-specific columns
            authors = row[1]["authors"]
            year = row[1]["year"]
            if authors not in exclude_list:
                predicates_list.append((":hasAuthorList",
                                        language_string(authors)))
            if year not in exclude_list:
                predicates_list.append((":hasPublicationYear",
                                        language_string(year)))

            # questionnaire-specific columns
            use_with_assessments = row[1]["use_with_assessments"]
            number_of_questions = row[1]["number_of_questions"]
            minutes_to_complete = row[1]["minutes_to_complete"]
            age_min = row[1]["age_min"]
            age_max = row[1]["age_max"]
            if use_with_assessments not in exclude_list:
                indices = [np.int(x) for x in
                           use_with_assessments.strip().split(',') if len(x)>0]
                for index in indices:
                    objectRDF = questionnaires[
                        questionnaires["index"] == index]["title"].values[0]
                    if objectRDF not in exclude_list:
                        predicates_list.append((":useWith",
                                                check_iri(objectRDF)))
            if number_of_questions not in exclude_list and \
                    isinstance(number_of_questions, str):
                if "-" in number_of_questions:
                    predicates_list.append((":hasNumberOfQuestions",
                                            '"{0}"^^xsd:string'.format(
                                                number_of_questions)))
                else:
                    predicates_list.append((":hasNumberOfQuestions",
                                            '"{0}"^^xsd:nonNegativeInteger'.format(
                                                number_of_questions)))
            if minutes_to_complete not in exclude_list and \
                    isinstance(minutes_to_complete, str):
                if "-" in minutes_to_complete:
                    predicates_list.append((":takesMinutesToComplete",
                        '"{0}"^^xsd:string'.format(minutes_to_complete)))
                else:
                    predicates_list.append((":takesMinutesToComplete",
                        '"{0}"^^xsd:nonNegativeInteger'.format(minutes_to_complete)))
            if age_min not in exclude_list and isinstance(age_min, str):
                predicates_list.append(("schema:requiredMinAge",
                    '"{0}"^^xsd:decimal'.format(age_min)))
            if age_max not in exclude_list and isinstance(age_max, str):
                predicates_list.append(("schema:requiredMaxAge",
                    '"{0}"^^xsd:decimal'.format(age_max)))

            # indices to other worksheets about who uses the shared
            indices_respondent = row[1]["indices_respondent"]
            indices_subject = row[1]["indices_subject"]
            indices_reference = row[1]["indices_reference"]
            index_license = row[1]["index_license"]
            indices_language = row[1]["indices_language"]
            # if indices_respondent not in exclude_list:
            #     if isinstance(indices_respondent, float):
            #         indices = [np.int(indices_respondent)]
            #     else:
            #         indices = [np.int(x) for x in
            #                    indices_respondent.strip().split(',') if len(x)>0]
            #     for index in indices:
            #         objectRDF = respondents_or_subjects[
            #             respondents_or_subjects["index"] ==
            #             index]["respondent_or_subject"].values[0]
            #         if objectRDF not in exclude_list:
            #             predicates_list.append(("schema:audienceType",
            #                                     check_iri(objectRDF)))
            # if indices_subject not in exclude_list:
            #     if isinstance(indices_subject, float):
            #         indices = [np.int(indices_subject)]
            #     else:
            #         indices = [np.int(x) for x in
            #                    indices_subject.strip().split(',') if len(x)>0]
            #     for index in indices:
            #         objectRDF = respondents_or_subjects[
            #             respondents_or_subjects["index"] ==
            #             index]["respondent_or_subject"].values[0]
            #         if objectRDF not in exclude_list:
            #             predicates_list.append(("schema:about",
            #                                     check_iri(objectRDF)))
            # if indices_reference not in exclude_list:
            #     indices = [np.int(x) for x in
            #                indices_reference.strip().split(',') if len(x)>0]
            #     for index in indices:
            #         # cited reference IRI
            #         title_cited = questionnaires[
            #             questionnaires["index"] == index]["title"].values[0]
            #         if title_cited not in exclude_list:
            #             title_cited = check_iri(title_cited)
            #             predicates_list.append((":isReferencedBy", title_cited))
            if index_license not in exclude_list:
                objectRDF = shared[licenses["index"] ==
                                       index_license]["license"].values[0]
                if objectRDF not in exclude_list:
                    predicates_list.append((":hasLicense", check_iri(objectRDF)))
            # if indices_language not in exclude_list:
            #     indices = [np.int(x) for x in
            #                indices_language.strip().split(',') if len(x)>0]
            #     for index in indices:
            #         objectRDF = languages[
            #             languages["index"] == index]["language"].values[0]
            #         if objectRDF not in exclude_list:
            #             predicates_list.append((":hasLanguage",
            #                                     check_iri(objectRDF)))

            for predicates in predicates_list:
                statements = add_to_statements(
                    questionnaire_iri,
                    predicates[0],
                    predicates[1],
                    statements,
                    exclude_list
                )

    # questions worksheet
    qnum = 1
    old_questionnaires = []
    for row in questions.iterrows():

        #print(row[1]["index"], row[1]["index_questionnaire"])
        questionnaire = questionnaires[questionnaires["index"] ==
                            row[1]["index_questionnaire"]]["title"].values[0]
        if questionnaire not in old_questionnaires:
            qnum = 1
            old_questionnaires.append(questionnaire)
        else:
            qnum += 1

        question = row[1]["question"]
        question_label = language_string(question)
        question_iri = check_iri("{0}_Q{1}".format(questionnaire, qnum))

        predicates_list = []
        predicates_list.append(("rdfs:label", question_label))
        predicates_list.append(("a", ":Question"))
        predicates_list.append((":hasQuestionText", question_label))
        predicates_list.append((":isReferencedBy", check_iri(questionnaire)))

        paper_instructions_preamble = row[1]["paper_instructions_preamble"]
        paper_instructions = row[1]["paper_instructions"]
        digital_instructions_preamble = row[1]["digital_instructions_preamble"]
        digital_instructions = row[1]["digital_instructions"]
        response_options = row[1]["response_options"]

        if paper_instructions_preamble not in exclude_list:
            predicates_list.append((":hasPaperInstructionsPreamble",
                                    language_string(paper_instructions_preamble)))
            # statements = add_to_statements(
            #     check_iri(paper_instructions_preamble),
            #     "a",
            #     ":PaperInstructions",
            #     statements,
            #     exclude_list
            # )
            # statements = add_to_statements(
            #     check_iri(paper_instructions_preamble),
            #     "rdfs:label",
            #     language_string(paper_instructions_preamble),
            #     statements,
            #     exclude_list
            # )
        if paper_instructions.strip() not in exclude_list:
            predicates_list.append((":hasPaperInstructions",
                                    language_string(paper_instructions)))
            # statements = add_to_statements(
            #     check_iri(paper_instructions),
            #     "a",
            #     ":PaperInstructions",
            #     statements,
            #     exclude_list
            # )
            # statements = add_to_statements(
            #     check_iri(paper_instructions_preamble),
            #     ":hasPaperInstructions",
            #     check_iri(paper_instructions),
            #     statements,
            #     exclude_list
            # )
            # statements = add_to_statements(
            #     check_iri(paper_instructions),
            #     "rdfs:label",
            #     language_string(paper_instructions),
            #     statements,
            #     exclude_list
            # )
        if digital_instructions_preamble not in exclude_list:
            predicates_list.append((":hasInstructionsPreamble",
                                    language_string(digital_instructions_preamble)))
            # statements = add_to_statements(
            #     check_iri(digital_instructions_preamble),
            #     "a",
            #     ":Instructions",
            #     statements,
            #     exclude_list
            # )
            # statements = add_to_statements(
            #     check_iri(digital_instructions_preamble),
            #     "rdfs:label",
            #     language_string(digital_instructions_preamble),
            #     statements,
            #     exclude_list
            # )
        if digital_instructions not in exclude_list:
            predicates_list.append((":hasInstructions",
                                    language_string(digital_instructions)))
            # statements = add_to_statements(
            #     check_iri(digital_instructions),
            #     "a",
            #     ":Instructions",
            #     statements,
            #     exclude_list
            # )
            # statements = add_to_statements(
            #     check_iri(digital_instructions_preamble),
            #     ":hasInstructions",
            #     check_iri(digital_instructions),
            #     statements,
            #     exclude_list
            # )
            # statements = add_to_statements(
            #     check_iri(digital_instructions),
            #     "rdfs:label",
            #     language_string(digital_instructions),
            #     statements,
            #     exclude_list
            # )

        if response_options not in exclude_list:
            response_options = response_options.strip('-')
            response_options = response_options.replace("\n", "")
            response_options_iri = check_iri(response_options)
            if '"' in response_options:
                response_options = re.findall('[-+]?[0-9]+=".*?"',
                                              response_options)
            else:
                response_options = response_options.split(",")
            #print(row[1]["index"], ' response options: ', response_options)

            statements = add_to_statements(
                question_iri,
                ":hasResponseOptions",
                response_options_iri,
                statements,
                exclude_list
            )
            statements = add_to_statements(response_options_iri,
                                           "a", "rdf:Seq",
                                           statements, exclude_list)
            for iresponse, response_option in enumerate(response_options):
                response = response_option.split("=")[1].strip()
                if response in exclude_list:
                    response_iri = ":Empty"
                else:
                    response_iri = check_iri(response)
                    statements = add_to_statements(
                        response_iri,
                        "rdf:label",
                        language_string(response),
                        statements,
                        exclude_list
                    )
                    statements = add_to_statements(
                        response_options_iri,
                        "rdf:_{0}".format(iresponse + 1),
                        response_iri,
                        statements,
                        exclude_list
                    )

            # response_sequence = "\n    [ a rdf:Seq ; "
            # for iresponse, response in enumerate(response_options):
            #     response_index = response.split("=")[0].strip()
            #     response = response.split("=")[1].strip()
            #     response = response.strip('"').strip()
            #     response = response.strip("'").strip()
            #     if response in [""]:
            #         response_iri = ":Empty"
            #     else:
            #         #print(row[1]["index"], response)
            #         response_iri = check_iri(response)
            #         statements = add_to_statements(
            #             response_iri,
            #             "rdf:label",
            #             language_string(response),
            #             statements,
            #             exclude_list
            #         )
            #
            #     if iresponse == len(response_options) - 1:
            #         delim = ""  # ""."
            #     else:
            #         delim = ";"
            #     response_sequence += \
            #         '\n      rdf:_{0} {1} {2}'.format(response_index,
            #                                           response_iri,
            #                                           delim)
            # response_sequence += "\n    ]"
            #
            # statements = add_to_statements(
            #     response_options_iri,
            #     "rdfs:value",
            #     response_sequence,
            #     statements,
            #     exclude_list
            # )

        indices_response_type = row[1]["indices_response_type"]
        if indices_response_type not in exclude_list:
            indices = [np.int(x) for x in
                       indices_response_type.strip().split(',') if len(x) > 0]
            for index in indices:
                objectRDF = response_types[response_types["index"] ==
                                           index]["response_type"].values[0]
                if isinstance(objectRDF, str):
                    predicates_list.append((":hasResponseType",
                                            check_iri(objectRDF)))
        # index_scale_type = row[1]["scale_type"]
        # index_value_type = row[1]["value_type"]
        # num_options = row[1]["num_options"]
        # index_neutral = row[1]["index_neutral"]
        # index_min = row[1]["index_min_extreme_oo_unclear_na_none"]
        # index_max = row[1]["index_max_extreme_oo_unclear_na_none"]
        # index_dontknow = row[1]["index_dontknow_na"]
        # if index_scale_type not in exclude_list:
        #     scale_type_iri = scale_types[scale_types["index"] ==
        #                                  index_scale_type]["IRI"].values[0]
        #     if scale_type_iri in exclude_list:
        #         scale_type_iri = check_iri(scale_types[scale_types["index"] ==
        #                                   index_scale_type]["scale_type"].values[0])
        #     if scale_type_iri not in exclude_list:
        #         predicates_list.append((":hasScaleType", check_iri(scale_type_iri)))
        # if index_value_type not in exclude_list:
        #     value_type_iri = value_types[value_types["index"] ==
        #                                  index_value_type]["IRI"].values[0]
        #     if value_type_iri in exclude_list:
        #         value_type_iri = check_iri(value_types[value_types["index"] ==
        #                                   index_value_type]["value_type"].values[0])
        #     if value_type_iri not in exclude_list:
        #         predicates_list.append((":hasValueType", check_iri(value_type_iri)))
        # if num_options not in exclude_list:
        #     predicates_list.append((":hasNumberOfOptions",
        #                             '"{0}"^^xsd:nonNegativeInteger'.format(
        #                                 num_options)))
        # if index_neutral not in exclude_list:
        #     if index_neutral not in ['oo', 'n/a']:
        #         predicates_list.append((":hasNeutralValueForResponseIndex",
        #                                 '"{0}"^^xsd:integer'.format(
        #                                     index_neutral)))
        # if index_min not in exclude_list:
        #     if index_min not in ['oo', 'n/a']:
        #         predicates_list.append((":hasExtremeValueForResponseIndex",
        #                                 '"{0}"^^xsd:integer'.format(
        #                                     index_min)))
        # if index_max not in exclude_list:
        #     if index_max not in ['oo', 'n/a']:
        #         predicates_list.append((":hasExtremeValueForResponseIndex",
        #                                 '"{0}"^^xsd:integer'.format(
        #                                     index_max)))
        # if index_dontknow not in exclude_list:
        #     predicates_list.append((":hasDontKnowOrNanForResponseIndex",
        #                             '"{0}"^^xsd:integer'.format(
        #                                 index_dontknow)))

        for predicates in predicates_list:
            statements = add_to_statements(
                question_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # response_types worksheet
    for row in response_types.iterrows():
        response_type_iri = check_iri(row[1]["response_type"])
        response_type_label = language_string(row[1]["response_type"])
        statements = add_to_statements(
            response_type_iri, "rdfs:label", response_type_label,
            statements, exclude_list)
        statements = add_to_statements(
            response_type_iri, "a", ":ResponseType",
            statements, exclude_list)

        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                                 equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))

    # tasks worksheet
    for row in tasks.iterrows():

        task_label = language_string(row[1]["name"])
        task_iri = check_iri(row[1]["name"])

        predicates_list = []
        predicates_list.append(("rdfs:label", task_label))
        predicates_list.append(("a", ":Task"))

        if row[1]["description"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["description"])))
        if row[1]["aliases"] not in exclude_list:
            aliases = row[1]["aliases"].split(',')
            for alias in aliases:
                predicates_list.append(("rdfs:label", language_string(alias)))

        # # Cognitive Atlas-specific column
        # cogatlas_node_id = check_iri(row[1]["cogatlas_node_id"])
        # if cogatlas_node_id not in exclude_list:
        #     predicates_list.append((":hasCognitiveAtlasNodeID",
        #                             cogatlas_node_id))

        for predicates in predicates_list:
            statements = add_to_statements(
                task_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # task_implementations worksheet
    for row in implementations.iterrows():

        implementation_label = language_string(row[1]["implementation"])
        implementation_iri = check_iri(row[1]["implementation"])

        predicates_list = []
        predicates_list.append(("rdfs:label", implementation_label))
        predicates_list.append(("a", ":Task"))
        if row[1]["description"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["description"])))
        if row[1]["link"] not in exclude_list:
            predicates_list.append((":hasHomePage",
                                    "<" + row[1]["link"] + ">"))

        # indices to other worksheets
        indices_task = row[1]["indices_task"]
        indices_project = row[1]["indices_project"]
        if indices_task not in exclude_list:
            indices = [np.int(x) for x in indices_task.strip().split(',')
                       if len(x)>0]
            for index in indices:
                objectRDF = tasks[tasks["index"] == index]["name"].values[0]
                if isinstance(objectRDF, str):
                    predicates_list.append(("rdfs:subClassOf",
                                            check_iri(objectRDF)))
        if indices_project not in exclude_list:
            indices = [np.int(x) for x in indices_project.strip().split(',')
                       if len(x)>0]
            for index in indices:
                objectRDF = projects[projects["index"] ==
                                     index]["project"].values[0]
                if isinstance(objectRDF, str):
                    predicates_list.append((":hasProject",
                                            check_iri(objectRDF)))

        # # Cognitive Atlas-specific column
        # cogatlas_node_id = row[1]["cogatlas_node_id"]
        # if cogatlas_node_id not in exclude_list:
        #     predicates_list.append((":hasCognitiveAtlasNodeID",
        #                             check_iri(cogatlas_node_id)))

        for predicates in predicates_list:
            statements = add_to_statements(
                implementation_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # task_indicators worksheet
    for row in indicators.iterrows():

        indicator_label = language_string(row[1]["indicator"])
        indicator_iri = check_iri(row[1]["indicator"])

        predicates_list = []
        predicates_list.append(("rdfs:label", indicator_label))
        predicates_list.append(("a", ":Indicator"))

        # # Cognitive Atlas-specific column
        # cogatlas_node_id = row[1]["cogatlas_node_id"]
        # if cogatlas_node_id not in exclude_list:
        #     predicates_list.append((":hasCognitiveAtlasNodeID",
        #                             check_iri(cogatlas_node_id)))

        for predicates in predicates_list:
            statements = add_to_statements(
                indicator_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # task_conditions worksheet
    for row in conditions.iterrows():

        condition_label = language_string(row[1]["condition"])
        condition_iri = check_iri(row[1]["condition"])

        predicates_list = []
        predicates_list.append(("rdfs:label", condition_label))
        predicates_list.append(("a", ":Condition"))
        if row[1]["description"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["description"])))

        # # Cognitive Atlas-specific column
        # cogatlas_node_id = row[1]["cogatlas_node_id"]
        # if cogatlas_node_id not in exclude_list:
        #     predicates_list.append((":hasCognitiveAtlasNodeID",
        #                             check_iri(cogatlas_node_id)))

        for predicates in predicates_list:
            statements = add_to_statements(
                condition_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # task_contrasts worksheet
    for row in contrasts.iterrows():

        contrast_label = language_string(row[1]["contrast"])
        contrast_iri = check_iri(row[1]["contrast"])

        predicates_list = []
        predicates_list.append(("rdfs:label", contrast_label))
        predicates_list.append(("a", ":Contrast"))

        # # Cognitive Atlas-specific column
        # cogatlas_node_id = row[1]["cogatlas_node_id"]
        # if cogatlas_node_id not in exclude_list:
        #     predicates_list.append((":hasCognitiveAtlasNodeID",
        #                             check_iri(cogatlas_node_id)))

        for predicates in predicates_list:
            statements = add_to_statements(
                contrast_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # task_assertions_indices worksheet
    for row in assertions_indices.iterrows():

        reln_type = str(row[1]["cogatlas_reln_type"])
        startNode = int(row[1]["cogatlas_startNode"])
        endNode = int(row[1]["cogatlas_endNode"])
        subject = ""
        object = ""

        # Find subject and object from the different worksheets

        # tasks worksheet
        if subject in exclude_list:
            subject_task = tasks[tasks['cogatlas_node_id'] == startNode]["name"]
            if not subject_task.empty:
                subject = tasks[tasks['cogatlas_node_id'] == startNode]["name"].values[0]
        if object in exclude_list:
            object_task = tasks[tasks['cogatlas_node_id'] == endNode]["name"]
            if not object_task.empty:
                object = tasks[tasks['cogatlas_node_id'] == endNode]["name"].values[0]

        # task_implementations worksheet
        if subject in exclude_list:
            subject_implementation = implementations[implementations['cogatlas_node_id'] == startNode]["implementation"]
            if not subject_implementation.empty:
                subject = implementations[implementations['cogatlas_node_id'] == startNode]["implementation"].values[0]
        if object in exclude_list:
            object_implementation = implementations[implementations['cogatlas_node_id'] == endNode]["implementation"]
            if not object_implementation.empty:
                object = implementations[implementations['cogatlas_node_id'] == endNode]["implementation"].values[0]

        # task_indicators worksheet
        if subject in exclude_list:
            subject_indicator = indicators[indicators['cogatlas_node_id'] == startNode]["indicator"]
            if not subject_indicator.empty:
                subject = indicators[indicators['cogatlas_node_id'] == startNode]["indicator"].values[0]
        if object in exclude_list:
            object_indicator = indicators[indicators['cogatlas_node_id'] == endNode]["indicator"]
            if not object_indicator.empty:
                object = indicators[indicators['cogatlas_node_id'] == endNode]["indicator"].values[0]

        # task_conditions worksheet
        if subject in exclude_list:
            subject_condition = conditions[conditions['cogatlas_node_id'] == startNode]["condition"]
            if not subject_condition.empty:
                subject = conditions[conditions['cogatlas_node_id'] == startNode]["condition"].values[0]
        if object in exclude_list:
            object_condition = conditions[conditions['cogatlas_node_id'] == endNode]["condition"]
            if not object_condition.empty:
                object = conditions[conditions['cogatlas_node_id'] == endNode]["condition"].values[0]

        # task_contrasts worksheet
        if subject in exclude_list:
            subject_contrast = contrasts[contrasts['cogatlas_node_id'] == startNode]["contrast"]
            if not subject_contrast.empty:
                subject = contrasts[contrasts['cogatlas_node_id'] == startNode]["contrast"].values[0]
        if object in exclude_list:
            object_contrast = contrasts[contrasts['cogatlas_node_id'] == endNode]["contrast"]
            if not object_contrast.empty:
                object = contrasts[contrasts['cogatlas_node_id'] == endNode]["contrast"].values[0]

        if subject not in exclude_list and object not in exclude_list and not subject == object:

            # Build subject - predicate - object triple
            subject_iri = check_iri(subject)
            object_iri = check_iri(object)

            if reln_type == "ASSERTS":
                reln_type = ":assertsCognitiveAtlasConcept"
                # task -> asserts -> concept (identify concept)
                statements = add_to_statements(
                    object_iri, "a", ":CognitiveAtlasConcept",
                    statements, exclude_list
                )
                statements = add_to_statements(
                    object_iri, "rdfs:label", language_string(object),
                    statements, exclude_list
                )
            elif reln_type == "HASCITATION":
                predicate_iri = ":hasBibliographicCitation"
            elif reln_type == "HASCONDITION":
                predicate_iri = ":hasTaskCondition"
            elif reln_type == "HASCONTRAST":
                predicate_iri = ":hasTaskContrast"
            elif reln_type == "HASIMPLEMENTATION":
                predicate_iri = ":hasTaskImplementation"
            elif reln_type == "HASINDICATOR":
                predicate_iri = ":hasTaskIndicator"
            elif reln_type == "KINDOF":
                predicate_iri = ":isKindOf"
            elif reln_type == "MEASUREDBY":
                predicate_iri = ":measuredBy"
            elif reln_type == "PARTOF":
                predicate_iri = ":isPartOf"
            else:
                predicate_iri = ""
            # if reln_type == "HASDIFFERENCE":
            # if reln_type == "CLASSIFIEDUNDER":
            # if reln_type == "ISA":
            # if reln_type == "PREDICATE":
            # if reln_type == "PREDICATE_DEF":
            # if reln_type == "SUBJECT":

            if predicate_iri not in exclude_list:
                #print('"{0}", {1}, "{2}"'.format(subject, predicate_iri, object))

                statements = add_to_statements(
                    subject_iri, predicate_iri, object_iri,
                    statements, exclude_list
                )

    # references worksheet
    for row in references.iterrows():

        predicates_list = []

        # require title
        title = row[1]["title"]
        if title not in exclude_list:

            # reference IRI
            reference_iri = check_iri(title)
            predicates_list.append(("rdfs:label", language_string(title)))
            predicates_list.append((":hasTitle", language_string(title)))
            predicates_list.append(("a", ":BibliographicResource"))

            # general columns
            link = row[1]["link"]
            if link not in exclude_list:
                predicates_list.append((":hasHomePage",
                                        "<" + link.strip() + ">"))
            entry_date = row[1]["entry_date"]
            if entry_date not in exclude_list:
                predicates_list.append((":hasEntryDate",
                                        language_string(entry_date)))

            # research article-specific columns
            authors = row[1]["authors"]
            pubdate = row[1]["pubdate"]
            PubMedID = row[1]["PubMedID"]
            if authors not in exclude_list:
                predicates_list.append((":hasAuthorList",
                                        language_string(authors)))
            if pubdate not in exclude_list:
                predicates_list.append((":hasPublicationDate",
                                        language_string(pubdate)))
            if PubMedID not in exclude_list:
                predicates_list.append((":hasPubMedID",
                                        '"{0}"^^xsd:integer'.format(int(PubMedID))))

            # # Cognitive Atlas-specific column
            # cogatlas_node_id = row[1]["cogatlas_node_id"]
            # if cogatlas_node_id not in exclude_list:
            #     predicates_list.append((":hasCognitiveAtlasNodeID",
            #                             check_iri(cogatlas_node_id)))

            for predicates in predicates_list:
                statements = add_to_statements(
                    reference_iri,
                    predicates[0],
                    predicates[1],
                    statements,
                    exclude_list
                )

    return statements


def ingest_measures(measures_xls, statements={}):
    """
    Function to ingest measures spreadsheet

    Parameters
    ----------
    measures_xls: pandas ExcelFile

    statements:  dictionary
        key: string
            RDF subject
        value: dictionary
            key: string
                RDF predicate
            value: {string}
                set of RDF objects

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
    """

    # load worksheets as pandas dataframes
    measures_classes = measures_xls.parse("Classes")
    measures_properties = measures_xls.parse("Properties")
    sensors = measures_xls.parse("sensors")
    measures = measures_xls.parse("measures")
    scales = measures_xls.parse("scales")

    # fill NANs with emptyValue
    measures_classes = measures_classes.fillna(emptyValue)
    measures_properties = measures_properties.fillna(emptyValue)
    sensors = sensors.fillna(emptyValue)
    measures = measures.fillna(emptyValue)
    scales = scales.fillna(emptyValue)

    # Classes worksheet
    for row in measures_classes.iterrows():
        class_label = language_string(row[1]["ClassName"])
        class_iri = mhdb_iri_simple(row[1]["ClassName"])
        predicates_list = []
        predicates_list.append(("rdfs:label", class_label))
        predicates_list.append(("a", "rdf:Class"))
        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["sameAs"] not in exclude_list:
            predicates_list.append(("owl:sameAs", row[1]["sameAs"]))
        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                             equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))
        if row[1]["subClassOf"] not in exclude_list:
            predicates_list.append(("rdfs:subClassOf",
                                    mhdb_iri_simple(row[1]["subClassOf"])))
        for predicates in predicates_list:
            statements = add_to_statements(
                class_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # Properties worksheet
    for row in measures_properties.iterrows():
        property_label = language_string(row[1]["property"])
        property_iri = mhdb_iri_simple(row[1]["property"])
        predicates_list = []
        predicates_list.append(("rdfs:label", property_label))
        predicates_list.append(("a", "rdf:Property"))
        if row[1]["propertyDomain"] not in exclude_list:
            predicates_list.append(("rdfs:domain",
                                    mhdb_iri_simple(row[1]["propertyDomain"])))
        if row[1]["propertyRange"] not in exclude_list:
            predicates_list.append(("rdfs:range",
                                    mhdb_iri_simple(row[1]["propertyRange"])))
        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["sameAs"] not in exclude_list:
            predicates_list.append(("owl:sameAs",
                                    row[1]["sameAs"]))
        if row[1]["equivalentProperty"] not in exclude_list:
            predicates_list.append(("rdfs:equivalentProperty",
                                    row[1]["equivalentProperty"]))
        if row[1]["subPropertyOf"] not in exclude_list:
            predicates_list.append(("rdfs:subPropertyOf",
                                    mhdb_iri_simple(row[1]["subPropertyOf"])))
        for predicates in predicates_list:
            statements = add_to_statements(
                property_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # sensors worksheet
    for row in sensors.iterrows():

        sensor_label = language_string(row[1]["sensor"])
        sensor_iri = check_iri(row[1]["sensor"])

        predicates_list = []
        predicates_list.append(("a", ":SensingDevice"))
        predicates_list.append(("rdfs:label", sensor_label))

        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                             equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))

        aliases = row[1]["aliases"]
        if aliases not in exclude_list:
            aliases = [x for x in aliases.strip().split(',') if len(x)>0]
            for alias in aliases:
                if alias not in exclude_list:
                    if isinstance(alias, str):
                        predicates_list.append(("rdfs:label", alias))

        if row[1]["indices_sensor"] not in exclude_list:
            indices = [np.int(x) for x in
                       row[1]["indices_sensor"].strip().split(',')
                       if len(x)>0]
            for index in indices:
                objectRDF = sensors[sensors["index"]  ==
                                          index]["sensor"].values[0]
                if objectRDF not in exclude_list:
                    predicates_list.append(("rdfs:subClassOf",
                                            check_iri(objectRDF)))

        indices_measure = row[1]["indices_measure"]
        if indices_measure not in exclude_list:
            if isinstance(indices_measure, int):
                indices = [indices_measure]
            else:
                indices = [np.int(x) for x in
                           indices_measure.strip().split(',') if len(x)>0]
            for index in indices:
                objectRDF = measures[measures["index"] ==
                                     index]["measure"].values[0]
                if isinstance(objectRDF, str):
                    predicates_list.append((":measuresQuantityKind",
                                            check_iri(objectRDF)))

        for predicates in predicates_list:
            statements = add_to_statements(
                sensor_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # measures worksheet
    for row in measures.iterrows():

        measure_label = language_string(row[1]["measure"])
        measure_iri = check_iri(row[1]["measure"])

        predicates_list = []
        predicates_list.append(("a", ":QuantityKind"))
        predicates_list.append(("rdfs:label", measure_label))

        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                             equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))
        aliases = row[1]["aliases"]
        if aliases not in exclude_list:
            aliases = [x for x in aliases.strip().split(',') if len(x)>0]
            for alias in aliases:
                if alias not in exclude_list:
                    if isinstance(alias, str):
                        predicates_list.append(("rdfs:label", alias))

        indices_measure = row[1]["indices_measure"]
        if indices_measure not in exclude_list:
            indices = [np.int(x) for x in
                       indices_measure.strip().split(',') if len(x)>0]
            for index in indices:
                objectRDF = measures[measures["index"] ==
                                     index]["measure"].values[0]
                if isinstance(objectRDF, str):
                    predicates_list.append(("rdfs:subClassOf",
                                            check_iri(objectRDF)))

        for predicates in predicates_list:
            statements = add_to_statements(
                measure_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    # scales worksheet
    for row in scales.iterrows():

        scale_label = language_string(row[1]["scale"])
        scale_iri = check_iri(row[1]["scale"])

        predicates_list = []
        predicates_list.append(("a", ":Scale"))
        predicates_list.append(("rdfs:label", scale_label))

        if row[1]["definition"] not in exclude_list:
            predicates_list.append(("rdfs:comment",
                                    language_string(row[1]["definition"])))
        if row[1]["equivalentClasses"] not in exclude_list:
            equivalentClasses = row[1]["equivalentClasses"]
            equivalentClasses = [x.strip() for x in
                             equivalentClasses.strip().split(',') if len(x) > 0]
            for equivalentClass in equivalentClasses:
                if equivalentClass not in exclude_list:
                    predicates_list.append(("rdfs:equivalentClass",
                                            equivalentClass))
        aliases = row[1]["aliases"]
        if aliases not in exclude_list:
            aliases = [x for x in aliases.strip().split(',') if len(x)>0]
            for alias in aliases:
                if alias not in exclude_list:
                    if isinstance(alias, str):
                        predicates_list.append(("rdfs:label", alias))

        # indices_scale = row[1]["indices_scale"]
        # if indices_scale not in exclude_list:
        #     indices = [np.int(x) for x in
        #                indices_scale.strip().split(',') if len(x)>0]
        #     for index in indices:
        #         objectRDF = scales[scales["index"] ==
        #                              index]["scale"].values[0]
        #         if isinstance(objectRDF, str):
        #             predicates_list.append(("rdfs:subClassOf",
        #                                     check_iri(objectRDF)))

        for predicates in predicates_list:
            statements = add_to_statements(
                scale_iri,
                predicates[0],
                predicates[1],
                statements,
                exclude_list
            )

    return statements

# indices to other worksheets about content of the shared
# indices_state = row[1]["indices_state"]
# comorbidity_indices_disorder = row[1]["comorbidity_indices_disorder"]
# medication_indices = row[1]["medication_indices"]
# treatment_indices = row[1]["treatment_indices"]
# indices_disorder = row[1]["indices_disorder"]
# indices_disorder_category = row[1]["indices_disorder_category"]
# if indices_state not in exclude_list:
#     indices = [np.int(x) for x in
#                indices_state.strip().split(',') if len(x)>0]
#     for index in indices:
#         objectRDF = states[states["index"] == index]["state"].values[0]
#         if objectRDF not in exclude_list:
#             predicates_list.append((":isAboutDomain",
#                                     check_iri(objectRDF)))
# if comorbidity_indices_disorder not in exclude_list:
#     indices = [np.int(x) for x in
#                comorbidity_indices_disorder.strip().split(',') if len(x)>0]
#     for index in indices:
#         objectRDF = disorders[
#             disorders["index"] == index]["disorder"].values[0]
#         if objectRDF not in exclude_list:
#             predicates_list.append(("schema:about", check_iri(objectRDF)))
# if medication_indices not in exclude_list:
#     indices = [np.int(x) for x in
#                medication_indices.strip().split(',') if len(x)>0]
#     for index in indices:
#         objectRDF = medications[
#             medications["index"] == index]["medication"].values[0]
#         if objectRDF not in exclude_list:
#             predicates_list.append(("schema:about", check_iri(objectRDF)))
# if treatment_indices not in exclude_list:
#     indices = [np.int(x) for x in
#                treatment_indices.strip().split(',') if len(x)>0]
#     for index in indices:
#         objectRDF = treatments[treatments["index"] ==
#                                index]["treatment"].values[0]
#         if objectRDF not in exclude_list:
#             predicates_list.append(("schema:about", check_iri(objectRDF)))
# if indices_disorder not in exclude_list:
#     indices = [np.int(x) for x in
#                indices_disorder.strip().split(',') if len(x)>0]
#     for index in indices:
#         objectRDF = disorders[disorders["index"] ==
#                               index]["disorder"].values[0]
#         if objectRDF not in exclude_list:
#             predicates_list.append(("schema:about", check_iri(objectRDF)))
# if indices_disorder_category not in exclude_list:
#     indices = [np.int(x) for x in
#                indices_disorder_category.strip().split(',') if len(x)>0]
#     for index in indices:
#         objectRDF = disorder_categories[disorder_categories["index"] ==
#                          index]["disorder_category"].values[0]
#         if objectRDF not in exclude_list:
#             predicates_list.append(("schema:about", check_iri(objectRDF)))

# # Cognitive Atlas-specific columns
# cogatlas_node_id = row[1]["cogatlas_node_id"]
# cogatlas_prop_id = row[1]["cogatlas_prop_id"]
# if cogatlas_node_id not in exclude_list:
#     predicates_list.append((":hasCognitiveAtlasNodeID",
#                             "cognitiveatlas_node_id_" + check_iri(cogatlas_node_id)))
# if cogatlas_prop_id not in exclude_list:
#     predicates_list.append((":hasCognitiveAtlasPropID",
#                             "cognitiveatlas_prop_id_" + check_iri(cogatlas_prop_id)))


#     # reference_types worksheet
#     for row in reference_types.iterrows():
#
#         reference_type_label = language_string(row[1]["reference_type"])
#
#         if row[1]["IRI"] not in exclude_list:
#             reference_type_iri = check_iri(row[1]["IRI"])
#         else:
#             reference_type_iri = check_iri(row[1]["reference_type"])
#
#         predicates_list = []
#         predicates_list.append(("rdfs:label",
#                                 language_string(reference_type_label)))
#         predicates_list.append(("a", ":ReferenceType"))
#
#         if row[1]["subClassOf"] not in exclude_list:
#             predicates_list.append(("rdfs:subClassOf",
#                                     check_iri(row[1]["subClassOf"])))
#
#         for predicates in predicates_list:
#             statements = add_to_statements(
#                 reference_type_iri,
#                 predicates[0],
#                 predicates[1],
#                 statements,
#                 exclude_list
#             )
#
#     # shared worksheet
#     for row in shared.iterrows():
#
#         predicates_list = []
#
#         # require title
#         title = row[1]["reference"]
#         if title not in exclude_list:
#
#             # reference IRI
#             reference_iri = check_iri(title)
#             predicates_list.append(("rdfs:label", language_string(title)))
#             predicates_list.append(("dcterms:title", language_string(title)))
#             predicates_list.append(("a", "dcterms:BibliographicResource"))
#
#             # general columns
#             link = row[1]["link"]
#             if link not in exclude_list:
#                 predicates_list.append(("foaf:homepage", check_iri(link)))
#             ingestion_date = row[1]["ingestion_date"]
#             if ingestion_date not in exclude_list:
#                 predicates_list.append((":entryDate", language_string(ingestion_date)))
#
#             # research article-specific columns
#             authors = row[1]["authors"]
#             pubdate = row[1]["pubdate"]
#             PubMedID = row[1]["PubMedID"]
#             if authors not in exclude_list:
#                 predicates_list.append(("bibo:authorList", language_string(authors)))
#             if pubdate not in exclude_list:
#                 predicates_list.append(("npg:publicationDate", language_string(pubdate)))
#                 # npg:publicationYear
#if PubMedID not in exclude_list:
#    predicates_list.append((":hasPubMedID",
#                            '"{0}"^^xsd:integer'.format(int(PubMedID))))
#
#             # indices to other worksheets about who uses the shared
#             indices_reference_type = row[1]["indices_reference_type"]
#             if indices_reference_type not in exclude_list:
#                 if isinstance(indices_reference_type, str):
#                     indices = [np.int(x) for x in
#                                indices_reference_type.strip().split(',') if len(x)>0]
#                 elif isinstance(indices_reference_type, float):
#                     indices = [np.int(indices_reference_type)]
#                 else:
#                     indices = None
#                 if indices not in exclude_list:
#                     for index in indices:
#                         objectRDF = reference_types[
#                             reference_types["index"] == index]["reference_type"].values[0]
#                         if objectRDF not in exclude_list:
#                             predicates_list.append((":hasReferenceType",
#                                                     check_iri(objectRDF)))
#             # if indices_disorder not in exclude_list:
#             #     indices = [np.int(x) for x in
#             #                indices_disorder.strip().split(',') if len(x)>0]
#             #     for index in indices:
#             #         objectRDF = disorders[disorders["index"] ==
#             #                               index]["disorder"].values[0]
#             #         if objectRDF not in exclude_list:
#             #             predicates_list.append(("schema:about", check_iri(objectRDF)))
#             # if indices_disorder_category not in exclude_list:
#             #     indices = [np.int(x) for x in
#             #                indices_disorder_category.strip().split(',') if len(x)>0]
#             #     for index in indices:
#             #         objectRDF = disorder_categories[disorder_categories["index"] ==
#             #                          index]["disorder_category"].values[0]
#             #         if objectRDF not in exclude_list:
#             #             predicates_list.append(("schema:about", check_iri(objectRDF)))
#
#             # # Cognitive Atlas-specific columns
#             # cogatlas_node_id = row[1]["cogatlas_node_id"]
#             # cogatlas_prop_id = row[1]["cogatlas_prop_id"]
#             # if cogatlas_node_id not in exclude_list:
#             #     predicates_list.append((":hasCognitiveAtlasNodeID",
#             #                             "cognitiveatlas_node_id_" + check_iri(cogatlas_node_id)))
#             # if cogatlas_prop_id not in exclude_list:
#             #     predicates_list.append((":hasCognitiveAtlasPropID",
#             #                             "cognitiveatlas_prop_id_" + check_iri(cogatlas_prop_id)))
#
#             for predicates in predicates_list:
#                 statements = add_to_statements(
#                     reference_iri,
#                     predicates[0],
#                     predicates[1],
#                     statements,
#                     exclude_list
#                 )
#
#
#     # respondents_or_subjects worksheet
#     for row in respondents_or_subjects.iterrows():
#         if row[1]["IRI"] not in exclude_list:
#             respondent_or_subject_IRI = check_iri(row[1]["IRI"])
#         else:
#             respondent_or_subject_IRI = check_iri(row[1]["respondent_or_subject"])
#         statements = add_to_statements(respondent_or_subject_IRI, "a",
#                                        "foaf:Person",
#                                        statements, exclude_list)
#         statements = add_to_statements(respondent_or_subject_IRI, "rdfs:label",
#                             language_string(row[1]["respondent_or_subject"]),
#                             statements, exclude_list)
#
#     # genders worksheet
#     # for row in genders.iterrows():
#     #     if row[1]["IRI"] not in exclude_list:
#     #         gender_iri = check_iri(row[1]["IRI"])
#     #     else:
#     #         gender_iri = check_iri(row[1]["gender"])
#     #     statements = add_to_statements(gender_iri, "rdfs:label",
#     #                         language_string(row[1]["gender"]),
#     #                         statements, exclude_list)
#
#     # medications worksheet
#     for row in medications.iterrows():
#         if row[1]["IRI"] not in exclude_list:
#             medication_iri = check_iri(row[1]["IRI"])
#         else:
#             medication_iri = check_iri(row[1]["medication"])
#         statements = add_to_statements(medication_iri, "a",
#                             ":Medication", statements, exclude_list)
#         statements = add_to_statements(medication_iri, "rdfs:label",
#                             language_string(row[1]["medication"]),
#                                        statements, exclude_list)
#
#     # treatments worksheet
#     for row in treatments.iterrows():
#         if row[1]["IRI"] not in exclude_list:
#             treatment_iri = check_iri(row[1]["IRI"])
#         else:
#             treatment_iri = check_iri(row[1]["treatment"])
#         statements = add_to_statements(treatment_iri, "a",
#                             ":Treatment", statements, exclude_list)
#         statements = add_to_statements(treatment_iri, "rdfs:label",
#                             language_string(row[1]["treatment"]),
#                                        statements, exclude_list)
#
#     return statements
