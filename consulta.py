# pip install sparqlwrapper
# https://rdflib.github.io/sparqlwrapper/

import sys
from SPARQLWrapper import SPARQLWrapper, JSON

endpoint_url = "https://wikifcd.wikibase.cloud/query/sparql"

query = """PREFIX wb: <https://wikifcd.wikibase.cloud/entity/>
PREFIX p: <https://wikifcd.wikibase.cloud/prop/>
PREFIX ps: <https://wikifcd.wikibase.cloud/prop/statement/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?food ?sodium ?sugar 
WHERE {
  
}
LIMIT 10
"""


def get_results(endpoint_url, query):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


results = get_results(endpoint_url, query)
print(results)

for result in results["results"]["bindings"]:
    print(result)