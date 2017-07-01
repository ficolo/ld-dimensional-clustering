from ld_dimensional_clustering import core
from rdflib import Graph, URIRef, Literal, XSD


def test_ldi_from_class():
    item_uri = ""
    assert core.get_ldi_from_uri(item_uri, None) == dict()


def test_ldi_from_uri():
    item_uri = "http://dbpedia.org/resource/Kenneth_E._Iverson"
    rdf_graph = Graph()
    rdf_graph = rdf_graph.parse("tests/motivating_example.nt", format="nt")
    print(core.get_ldi_from_uri(item_uri, rdf_graph))


def test_v_match():
    v_1 = URIRef("http://example.com/1")
    v_2 = URIRef("http://example.com/1")
    assert core.v_match(v_1, v_2) == 1

    v_1 = Literal(24)
    v_2 = Literal(32)
    assert core.v_match(v_1, v_2) == 0.75

    v_1 = Literal("Federico López Gómez")
    v_2 = Literal("Federico López Gómez")
    assert core.v_match(v_1, v_2) == 1

    v_1 = Literal("Federico López Gömez")
    v_2 = Literal("Federico López Gómez")
    assert core.v_match(v_1, v_2) == 0.95


def test_f_match():
    f_1 = [URIRef("http://example.com/1"), URIRef("http://example.com/3")]
    f_2 = [URIRef("http://example.com/1"),
           URIRef("http://example.com/5"),
           URIRef("http://example.com/3")]
    assert core.f_match(f_1, f_2) == 1.0
