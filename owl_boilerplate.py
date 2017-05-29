#!/usr/bin/env python
"""
This is a program to construct boilerplate owl rdf document text.

Authors:
    - Arno Klein, 2017  (arno@childmind.org)  http://binarybottle.com

Copyright 2017, Child Mind Institute (http://childmind.org), Apache v2.0 License

"""

base_uri = "http://www.purl.org/mentalhealth"
version = "1.0.0"
label = "Ontology of Mental & Psychiatric Health"
comment = "This ontology relates mental health disorders, " \
          "symptoms, questionnaires, publications, people, " \
          "and technologies."

def print_header(base_uri, version, label, comment):

    header = """
@prefix : <{0}#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@base <{0}> .

<{0}> rdf:type owl:Ontology ;
                                    owl:versionIRI <{0}/{1}> ;
                                    rdfs:label "{2}"^^rdfs:Literal ;
                                    owl:versionInfo "{1}"^^rdfs:Literal ;
                                    rdfs:comment "{3}"^^rdfs:Literal .

""".format(base_uri, version, label, comment)

    return header


def print_object_properties_header():
    return """
#################################################################
#    Object Properties
#################################################################
"""


def print_data_properties_header():
    return """
#################################################################
#    Data properties
#################################################################
"""


def print_classes_header():
    return """
#################################################################
#    Classes
#################################################################
"""


def print_general_axioms_header():
    return """
#################################################################
#    General axioms
#################################################################
"""


def print_object_property(base_uri, property_name, domain='', range=''):

    object_property_string = """
###  {0}#{1}
:{1} rdf:type owl:ObjectProperty ;
     rdfs:subPropertyOf :relational_property ;
     rdf:type owl:FunctionalProperty
""".format(base_uri, property_name, domain_string, range_string)

    if domain:
        object_property_string += """;
     rdfs:domain :{0} """.format(domain)

    if range:
        object_property_string += """;
     rdfs:range :{0} """.format(range)

    object_property_string += ".";

    return object_property_string


def print_data_property(base_uri, property_name):

    data_property_string = """
###  {0}#{1}
<{0}> rdf:type owl:DatatypeProperty .
""".format(base_uri, property_name)

    return data_property_string


def print_class(base_uri, class_name, equivalentURI, subClassOf_name):

    class_string = """
###  {0}#{1}
:{1} rdf:type owl:Class """

    if equivalentURI:
        class_string += """;
        owl:equivalentClass [ rdf:type owl:Restriction ;
                              owl:onProperty <{0}>
                            ] """.format(equivalentURI)
    if subClassOf_name:
        class_string += """;
        rdfs:subClassOf :{0} """.format(subClassOf_name)

    class_string += "."

    return class_string


def print_general_axioms(disjoint_classes_list):

    if disjoint_classes_list:
        general_axioms_string = """
[ rdf:type owl:AllDisjointClasses ;
  owl:members ( :{0} """.format(disjoint_classes_list[0])

        if len(disjoint_classes_list) > 1:
            for i in range(1, len(disjoint_classes_list)):
                general_axioms_string += """
  owl:members ( :{0} """.format(disjoint_classes_list[i])

        general_axioms_string += """
              )
] .
"""

    return general_axioms_string

