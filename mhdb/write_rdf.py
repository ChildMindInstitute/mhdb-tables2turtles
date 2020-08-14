#!/usr/bin/env python3
"""
This program contains generic functions to build an RDF text document.

Authors:
    - Arno Klein, 2017  (arno@childmind.org)  http://binarybottle.com
    - Jon Clucas, 2017 (jon.clucas@childmind.org)

Copyright 2017, Child Mind Institute (http://childmind.org), Apache v2.0 License

"""
global conceptClass
"""
Dictionary mapping OWL to OWL and SKOS to SKOS.
Otherwise, use "owl:AnnotationProperty".
"""
conceptClass = {"OWL":
                    {"equivalence": "owl:equivalentClass",
                    "subtype": "rdfs:subClassOf"
                    },
                "SKOS":
                    {"equivalence": "skos:exactMatch",
                    "subtype": "skos:broadMatch"
                    }
                }

def build_import(uri):
    """
    Build a generic RDF import substring.

    Parameters
    ----------
    uri : string
        import IRI

    Returns
    -------
    rdf_string : string
        RDF triples

    """
    if uri:
        return "owl:imports <{0}> ".format(uri)
    else:
        return None

def build_header_prefixes(prefixes):
    """
    Write turtle-formatted header prefix string for given list of (prefix,
    iri) tuples.

    Parameter
    ---------
    prefixes: list of 2-tuples
        each tuple is a prefix string and an iri string

    Returns
    -------
    header_prefix: string
    """
    header_prefix = ""
    for prefix in prefixes:
        header_prefix = """{0}@prefix {1}: <{2}> .
""".format(
            header_prefix,
            prefix[0],
            prefix[1]
        )
    header_prefix = """{0}@base <{1}> .
""".format(
        header_prefix,
        prefixes[0][1][:-1]
    )
    return(header_prefix)


def build_rdf(uri_stem, rdf_type, label, comment=None,
              index=None, worksheet=None, worksheet2=None,
              equivalent_class_uri=None, subclassof_uri=None,
              property_domain=None, property_range=None,
              exclude=[], conceptualizations={}): #, no_nan=True):
    """
    Build a generic RDF text document (with \" to escape for some strings).

    Parameters
    ----------
    uri_stem : string
        class URI stem
    rdf_type : string
        rdf:type, such as:
        ':Disorder',
        'owl:Class',
        'owl:ObjectProperty',
        'owl:DatatypeProperty',
        'owl:FunctionalProperty'
    label : string
        label
    comment : string
        comment
    index : integer
        index to row of worksheet
    worksheet : pandas dataframe
        spreadsheet worksheet containing properties
    worksheet2 : pandas dataframe
        second worksheet containing references
    equivalent_class_uri : string
        equivalentClass URI (override worksheet)
    subclassof_uri : string
        subClassOf URI (override worksheet)
    property_domain : string
        property domain (override worksheet)
    property_range : string
        property range (override worksheet)
    exclude : list
        exclusions
    conceptualizations : dictionary
        conceptualizaiton scheme (i.e., OWL or SKOS) for a given prefix
    #no_nan : Boolean
    #    return None if NaN?

    Returns
    -------
    rdf_string : string
        RDF triples

    """
    from mhdb.spreadsheet_io import return_string, get_cells #, get_cell

    # Get worksheet contents:
    class_uri, subclass_uri, prop_domain, prop_range, \
    definition, definition_ref, definition_uri = get_cells(worksheet, index,
                                                           worksheet2, exclude,
                                                           True)
    #try:
    #    coding_system = get_cell(worksheet, "health-lifesci:codingSystem",
    #                            index, exclude=[], no_nan=True)
    #except:
    #    coding_system = None
    # If arguments not provided, get from worksheet:
    if comment in exclude:
        comment = definition
    if equivalent_class_uri in exclude:
        equivalent_class_uri = class_uri
    if subclassof_uri in exclude:
        subclassof_uri = subclass_uri
    if property_domain in exclude:
        property_domain = prop_domain
    if property_range in exclude:
        property_range = prop_range
    l_con = owl_or_skos(uri_stem, conceptualizations)
    if ":" in uri_stem:
        rdf_string = """
### {0}
{1} rdf:type {2} """.format(label, uri_stem, rdf_type)
    else:
        rdf_string = """
### {0}
:{1} rdf:type {2} """.format(label, uri_stem, rdf_type)

    if label not in exclude:
        rdf_string += """;
    rdfs:label \"\"\"{0}\"\"\"^^rdfs:Literal """.format(
        label if not label[-1] == "\"" else "".join([label[:-1], "\\\""])
    )

    if comment not in exclude:
        if definition_ref in exclude:
            refstring = ""
        else:
            refstring = " [from: {0}]".format(return_string(definition_ref,
                                                            ['"'], ["'"]))
        rdf_string += """;
    rdfs:comment \"\"\"{0}{1}\"\"\"^^rdfs:Literal """.\
            format(return_string(comment, ['"'], ["'"]), refstring)

    if definition_uri not in exclude:
        rdf_string += """;
    rdfs:isDefinedBy "{0}"^^rdfs:Literal """.format(return_string(definition_uri))

    if equivalent_class_uri not in exclude:
        rel = owl_or_skos_prop(
              l_con, equivalent_class_uri, conceptualizations, "equivalence")
        if rdf_type=='owl:ObjectProperty':
            rdf_string += """;
        owl:equivalentProperty {0} """.format(return_string(equivalent_class_uri))
        else:
            rdf_string += """;
    {0} {1} """.format(rel, return_string(equivalent_class_uri))

    if subclassof_uri not in exclude:
        rel = owl_or_skos_prop(
              l_con, subclassof_uri, conceptualizations, "subtype")
        if not subclassof_uri.startswith(':') and "//" in subclassof_uri:
            subclassof_uri = "{0}".format(return_string(subclassof_uri))
        if rdf_type=='owl:ObjectProperty':
            rdf_string += """;
    rdfs:subPropertyOf {0} """.format(return_string(subclassof_uri))
        else:
            rdf_string += """;
    {0} {1} """.format(rel, return_string(subclassof_uri))

    if property_domain not in exclude:
        rdf_string += """;
    rdfs:domain :{0} """.format(return_string(property_domain))

    if property_range not in exclude:
        rdf_string += """;
    rdfs:range :{0} """.format(return_string(property_range))

    rdf_string += """.
"""

    return rdf_string


def owl_or_skos(label_safe, prefixes):
    """
    Build a generic RDF import substring.

    Parameters
    ----------
    label_safe : string
        URI

    prefixes : dictionary
        dictionary {string : string} of prefix keys and
        conceptualization values

    Returns
    -------
    conceptualisation : string
        "OWL" or "SKOS", default "OWL"

    """
    return (prefixes[label_safe.split(":")[0]] if (
        ":" in label_safe and
        "//" not in label_safe and
        not label_safe.startswith(":") and
        label_safe.split(":")[0] in prefixes
        ) else "OWL")


def owl_or_skos_prop(l_con, r, conceptualizations, gen_rel):
    """
    Return a property appropriate for the given conceptualizations.

    Parameters
    ----------
    l_con : string
        "SKOS" or "OWL"

    r : string
        class or concept IRI

    conceptualizations : dictionary
        dictionary of prefixes and conceptualizations

    gen_rel : string
        "equivalence" or "subtype"

    Returns
    -------
    rel : string
        relationship between given conceptualizations
    """
    rel = conceptClass[l_con][gen_rel] if (
        l_con == owl_or_skos(r, conceptualizations)
        ) else "rdfs:label"
    return rel


def print_header(base_uri, version, label, comment, prefixes=None):
    """
    Print out the beginning of an RDF text file.

    Parameters
    ----------
    base_uri : string
        base URI
    version : string
        version
    label : string
        label
    comment : string
        comment
    prefixes : list
        list of TTL prefix strings
    imports : list
        list of TTL import substrings

    Returns
    -------
    header : string
        owl header

    """

    header = """@prefix : <{0}#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dcterms: <http://dublincore.org/documents/2012/06/14/dcmi-terms/> .
@prefix health-lifesci: <http://health-lifesci.schema.org/> .
@prefix ICD10: <http://purl.bioontology.org/ontology/ICD10CM/> .
@prefix ICD9: <http://purl.bioontology.org/ontology/ICD9CM/> .
@prefix PATO: <http://www.ontobee.org/ontology/PATO?iri=http://purl.obolibrary.org/obo/PATO_> .
@prefix schema: <http://schema.org/> .
@prefix DOID: <http://bioportal.bioontology.org/ontologies/DOID?p=classes&conceptid=http://purl.obolibrary.org/obo/DOID> .
@base <{0}> .
""".format(base_uri) if not prefixes else build_header_prefixes(
        [("", "{0}#".format(base_uri)), *prefixes]
    )

    header = """{4}<{0}> rdf:type owl:Ontology ;
    owl:versionIRI <{0}/{1}> ;
    owl:versionInfo "{1}"^^rdfs:Literal ;
    rdfs:label "{2}"^^rdfs:Literal ;
    rdfs:comment \"\"\"{3}\"\"\"^^rdfs:Literal .

""".format(base_uri, version, label, comment, header)

    return header


def print_subheader(object_type):
    """
    Print out a subheader for a text file.
    """

    return """
#################################################################
#    {0}
#################################################################
""".format(object_type)


def print_general_axioms(disjoint_classes_list=[]):
    """

    Parameters
    ----------
    disjoint_classes_list : list of strings
        list of disjoint classes

    Returns
    -------
    general_axioms_string : string
        owl general axioms

    """

    general_axioms_string = ""

    if disjoint_classes_list:
        general_axioms_string += """
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
