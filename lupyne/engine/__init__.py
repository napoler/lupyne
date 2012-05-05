"""
Pythonic wrapper around `PyLucene <http://lucene.apache.org/pylucene/>`_ search engine.

Provides high-level interfaces to indexes and documents,
abstracting away java lucene primitives.
"""

import warnings
import lucene
warnings.simplefilter('default', DeprecationWarning)

from .queries import Query, SortField, TermsFilter
from .documents import Document, Field, FormatField, NestedField, NumericField, DateTimeField
from .indexers import TokenFilter, Analyzer, IndexSearcher, MultiSearcher, IndexWriter, Indexer
from .spatial import PointField, PolygonField

assert lucene.VERSION >= '3.1'
if lucene.VERSION < '3.2':
    warnings.warn('Support for lucene 3.1 will be removed in the next release.', DeprecationWarning)
