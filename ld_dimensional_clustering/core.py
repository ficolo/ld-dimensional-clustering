from rdflib import URIRef, Graph
from difflib import SequenceMatcher


def get_ldi_from_uri(item_uri, rdf_graph):
    """
    Generates the Linked Data Items (ldis) for
    every entity belonging to a class
    :param item_uri: Item URI for the ldi
    :param rdf_graph: RDF graph
    :return: An ldi dictionary
    """
    ldi = dict()
    if not item_uri or not rdf_graph:
        return ldi
    ldi['uri'] = item_uri
    ldi['features'] = dict()
    item_uri = URIRef(item_uri)
    for s, p, o in rdf_graph.triples((item_uri, None, None)):
        property_uri = str(p)
        if property_uri not in ldi['features']:
            ldi['features'][property_uri] = []
        ldi['features'][property_uri].append(o)
    return ldi


def v_match(v_i, v_j):

    if type(v_i) == type(v_j) == URIRef:
        if v_i.eq(v_j):
            return 1.0
        else:
            return 0.0

    v_i = v_i.toPython()
    v_j = v_j.toPython()

    if type(v_i) == type(v_j) == int:
        return float(min(v_i, v_j) / max(v_i, v_j))

    if type(v_i) == type(v_j) == str:
        return SequenceMatcher(None, v_i, v_j).ratio()


def f_match(f_i, f_j):
    sum_max = 0.0
    for v_s in f_i:
        max_v_match = 0.0
        for v_t in f_j:
            max_v_match = max(max_v_match, v_match(v_s, v_t))
        sum_max += max_v_match

    result = sum_max / len(f_i)
    return result


def ldi_match(ldi_i, ldi_j, dimension):
    sum_n = 0.0
    for f_i_name, f_i_values in ldi_i['features'].items():
        sum_m = 0.0
        for f_j_name, f_j_values in ldi_j['features'].items():
            if f_i_name == f_j_name and f_i_name in dimension:
                if len(f_i_values) <= len(f_j_values):
                    f_match_value = f_match(f_i_values, f_j_values)
                    sum_m += f_match_value
                else:
                    f_match_value = f_match(f_j_values, f_i_values)
                    sum_m += f_match_value
        sum_n += sum_m
    result = sum_n / len(set(ldi_i['features'].keys()) & set(dimension))
    return result


def get_ldis(uris, rdf_graph):
    ldis = [get_ldi_from_uri(uri, rdf_graph) for uri in uris]
    return ldis


def get_pi_and_sigma_matrix(ldis, dimension):
    sigma_matrix = [[0 for x in range(len(ldis))] for y in range(len(ldis))]
    pi_matrix = [[set() for x in range(len(ldis))] for x in range(len(ldis))]
    for i in range(len(ldis)):
        ldi_i = ldis[i]
        for j in range(i, len(ldis)):
            ldi_j = ldis[j]
            if len(ldi_i['features']) <= len(ldi_j['features']):
                sigma_matrix[i][j] = ldi_match(ldi_i, ldi_j, dimension)
            else:
                sigma_matrix[i][j] = ldi_match(ldi_j, ldi_i, dimension)
            i_features = set(ldi_i['features'].keys())
            j_features = set(ldi_j['features'].keys())
            i_j_features = i_features & j_features
            pi_features = i_j_features & set(dimension)
            pi_matrix[i][j] = pi_features
    return dict(sigma_matrix=sigma_matrix, pi_matrix=pi_matrix)


def hcfplus(corpus, dimension):
    matrixes = get_pi_and_sigma_matrix(corpus, dimension)
    sigma_matrix = matrixes['sigma_matrix']
    pi_matrix = matrixes['pi_matrix']
    k = len(corpus)

    clusters = []

    for i, ldi_r in enumerate(corpus):
        pi_r = set(ldi_r['features'].keys()) & set(dimension)
        clr = dict(ldis=[ldi_r], sigma=1.0, pi=pi_r)
        clusters.append(clr)

    while not check_zeros(sigma_matrix):
        max_pos = get_matrix_max(sigma_matrix)
        i = max_pos['i']
        j = max_pos['j']

        clk_ldis = clusters[i]['ldis'] + clusters[j]['ldis']

        clk = dict(ldis=clk_ldis,
                   sigma=sigma_matrix[i][j],
                   pi=pi_matrix[i][j])
        clusters.append(clk)

        for line in sigma_matrix:
            line.append(0)

        print()
        sigma_matrix.append([0 for x in range(k + 1)])

        for line in pi_matrix:
            line.append(set())

        pi_matrix.append([set() for x in range(k + 1)])

        for z in range(0, k + 1):
            pi_matrix[z][k] = pi_matrix[z][i] & pi_matrix[z][j] & clk['pi']
            if bool(pi_matrix[z][k]):
                sigma_matrix[z][k] = min(sigma_matrix[z][i],
                                         sigma_matrix[z][j])
            else:
                sigma_matrix[z][k] = 0

        for x in range(k + 1):
            for y in range(k + 1):
                if pi_matrix[x][y] <= pi_matrix[i][j]:
                    sigma_matrix[x][y] = 0
            print(sigma_matrix[x])
        k += 1
    return clusters


def get_matrix_max(matrix):
    matrix_max = 0.0
    max_pos = dict(i=0, j=0)
    for i, line in enumerate(matrix):
        for j, value_i_j in enumerate(line):
            if i == j:
                continue
            max_pos['i'] = i if matrix_max < value_i_j else max_pos['i']
            max_pos['j'] = j if matrix_max < value_i_j else max_pos['j']
            matrix_max = max(matrix_max, value_i_j)
    print("matrix_max: ", matrix_max)
    return max_pos


def check_zeros(matrix):
    for i, line in enumerate(matrix):
        for j, value_j in enumerate(line):
            if value_j != 0 and i != j:
                return False
    return True


uris_test = ["http://dbpedia.org/resource/Charles_P._Thacker",
             "http://dbpedia.org/resource/Glen_Culler",
             "http://dbpedia.org/resource/Kenneth_E._Iverson"]
rdf_graph_test = Graph()
corpus_test = get_ldis(uris_test,
                       rdf_graph_test.parse(
                           "tests/motivating_example.nt",
                           format="nt"))
dimension_test = ["http://dbpedia.org/ontology/nationality",
                  "http://dbpedia.org/property/birthPlace",
                  "http://dbpedia.org/ontology/deathPlace"]
dimension_test_1 = ["http://dbpedia.org/ontology/field",
                    "http://dbpedia.org/ontology/almaMater",
                    "http://dbpedia.org/ontology/award"]
clusters_test = hcfplus(corpus_test, dimension_test)

for index, cluster in enumerate(clusters_test):
    print("Cluster ", index, ": ")
    for ldi in cluster['ldis']:
        print(ldi['uri'])
        # for feature in cluster['pi']:
        #     print(ldi['features'][feature])
    print(cluster['pi'])
