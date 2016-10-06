from rdflib import Graph
from rdflib import term


def read_owl_file(url, uris):
    # Load Ontology
    g = Graph()
    g.parse(url, format='xml')

    labels = [get_label(g, x) for x in uris]
    select_clause = ' '.join(['?{}'.format(i) for i, uri in enumerate(uris)])
    optional_wheres = '\n'.join(['OPTIONAL {{?class <{}> ?{} . }}'.format(uri, i) for i, uri in enumerate(uris)])
    query = """
        SELECT ?term ?class {}
        WHERE {{
          ?class rdf:type owl:Class .
          ?class rdfs:label ?term .
          {}
        }}
        ORDER BY(?term)
         """.format(select_clause, optional_wheres)
    # Run SPARQL query & write results to appropriate columns
    query_results = g.query(query)
    ret = {}
    results = []
    for result in query_results:
        d = {}
        d['term'] = result[0]
        d['uri'] = result[1]
        for i, s in enumerate(uris):
            d[labels[i]] = result[i + 2]
        results.append(d)
    ret['results'] = results
    ret['labels'] = labels
    ret['owl_file'] = url
    ret['name'] = url.split('/')[-1]
    return ret

def get_label(graph, uri):
    try:
        graph.load(uri)
        uri = term.URIRef(uri)
        label = graph.label(uri)
        return str(label)
    except:
        return str(uri)
