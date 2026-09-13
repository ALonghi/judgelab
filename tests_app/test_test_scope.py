"""Acceptance suites must exercise their declared targets, not just collect tests."""
import ast

import pytest

from app.engine import LESSONS, ROOT, run_code

CODE_LESSONS = [lesson for lesson in LESSONS.values() if lesson['kind'] == 'code']


def replace_body(code, target):
    tree = ast.parse(code)
    node = next(node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == target)
    node.body = [ast.Raise(exc=ast.Call(func=ast.Name(id='NotImplementedError', ctx=ast.Load()),
                                      args=[ast.Constant('target intentionally unimplemented')], keywords=[]))]
    return ast.unparse(ast.fix_missing_locations(tree))


@pytest.mark.parametrize('lesson', CODE_LESSONS, ids=lambda lesson: lesson['id'])
def test_each_acceptance_suite_passes_reference_and_rejects_unimplemented_targets(lesson):
    code = (ROOT / 'references' / lesson['pack'] / lesson['file']).read_text()
    baseline = run_code(lesson, code)
    assert baseline['success'], baseline['output']
    for target in lesson['targets']:
        result = run_code(lesson, replace_body(code, target))
        assert not result['success'], (lesson['id'], target)
        assert result['failed'] > 0, result['output']
        assert not result['collection_errors'], result['output']


def test_scoring_pass_does_not_validate_unimplemented_search():
    code = (ROOT / 'references/guided/exercise.py').read_text()
    code = replace_body(code, 'search_documents')
    assert run_code(LESSONS['g-score'], code)['success']
    result = run_code(LESSONS['g-search'], code)
    assert not result['success']
    assert result['failed'] > 0
