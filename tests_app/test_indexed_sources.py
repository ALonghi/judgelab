"""Supplied source reader remains bounded before the learner's chunker runs."""
import importlib.util
from io import StringIO
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('indexed_source_words', Path(__file__).parents[1] / 'packs/indexed/source_words.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
iter_words = module.iter_words


@pytest.mark.parametrize('read_chars', [1, 2, 7, 4096])
def test_word_boundaries_unicode_and_final_word(read_chars):
    assert list(iter_words(StringIO(' Café!\t世界\nfinal'), read_chars=read_chars)) == ['Café!', '世界', 'final']


def test_reader_never_requests_whole_file_and_stops_on_oversized_word():
    class EndlessWord:
        calls = 0
        def read(self, size):
            assert size == 8
            self.calls += 1
            assert self.calls <= 3
            return 'x' * size
    with pytest.raises(ValueError, match='max_word_chars'):
        next(iter_words(EndlessWord(), read_chars=8, max_word_chars=16))
    assert list(iter_words(StringIO('x' * 16), max_word_chars=16)) == ['x' * 16]


@pytest.mark.parametrize('kwargs', [{'read_chars': 0}, {'max_word_chars': 0}])
def test_reader_validates_before_read(kwargs):
    class Unreadable:
        def read(self, size):
            raise AssertionError('Read invalid source')
    with pytest.raises(ValueError):
        next(iter_words(Unreadable(), **kwargs))
