# -*- coding: iso-8859-1 -*-
"""
Tests for scioweb.eplm.formsheets.eplm_base
"""
import unittest


from unittest import TestCase

from whoosh.index import create_in
from whoosh.qparser import QueryParser
from whoosh.fields import Schema, ID, TEXT

#===============================================================================
# BaseTest
#===============================================================================
class BaseTest(TestCase):                          
    """Test ."""
    def setUp(self):
        pass

    def tearDown(self):
        pass
        
    def test_buil_index(self):
        schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)
        ix = create_in("whoosh_index", schema)
        writer = ix.writer()
        writer.add_document(title=u"First document", path=u"/a",
                            content=u"This is the first document we've added!")
        writer.add_document(title=u"Second document", path=u"/b",
                            content=u"The second one is even more interesting!")
        writer.commit()
        
        with ix.searcher() as searcher:
            query = QueryParser("content", ix.schema).parse(u"first")
            results = searcher.search(query)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0], {"title": u"First document", "path": u"/a"})

            # stop-word are ignored
            query = QueryParser("content", ix.schema).parse(u"is")
            results = searcher.search(query)
            self.assertEqual(len(results), 0)
        
            # case insensititve
            query = QueryParser("content", ix.schema).parse(u"EVEN")
            results = searcher.search(query)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0], {'path': u'/b', 'title': u'Second document'})
        
        
#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    unittest.main()   
