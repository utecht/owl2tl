from rdflib import Graph


def read_owl_file(url, object0, object1):
    # Load Ontology
    g = Graph()
    g.parse(url, format='xml')

    # Run SPARQL query & write results to appropriate columns
    query_results = g.query(
            """
        SELECT ?term ?o0 ?o1
        WHERE {{
          ?class rdf:type owl:Class .
          ?class rdfs:label ?term .
          OPTIONAL {{?class <{}> ?o0 .}}
          OPTIONAL {{?class <{}> ?o1 .}}
        }}
        ORDER BY(?term)
         """.format(object0, object1))
    results = []
    for result in query_results:
        results.append({'term': result[0], 'o0': result[1], 'o1': result[2]})
    return results
