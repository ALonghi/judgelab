"""The full teaching sequence, including prerequisite and chapter boundaries."""
from app.engine import CATALOG, LESSONS


ORDER = {
    'basics': ['q-sets', 'c-latest', 'c-counts'],
    'api': ['p-fastapi', 'p-ingest', 'q-version', 'c-events'],
    'guided': ['q-score', 'g-score', 'q-tenants', 'g-permissions',
               'q-filter', 'g-categories', 'q-limit', 'g-search'],
    'core': ['c-search', 'c-index-build', 'c-index-query', 'c-fts',
             'c-chunking', 'q-context', 'c-context'],
    'async': ['a-refactor', 'a-fetch', 'q-cancel', 'a-federated', 'a-parser', 'a-llm'],
    'uploads': ['u-upload', 'u-batch', 'u-extract'],
    'architecture': ['s-api', 's-ingestion', 's-large-import',
                     's-search', 's-latency', 's-chat'],
}


def test_all_chapters_and_activities_follow_the_teaching_sequence():
    assert [t['id'] for t in CATALOG['tracks']] == list(ORDER)
    assert [l['id'] for l in CATALOG['lessons']] == [id for ids in ORDER.values() for id in ids]
    for track, ids in ORDER.items():
        assert [l['id'] for l in CATALOG['lessons'] if l['track'] == track] == ids
        assert len([id for id in ids if not LESSONS[id].get('optional')]) >= 3


def test_every_prerequisite_precedes_its_activity_and_is_required():
    position = {l['id']: i for i, l in enumerate(CATALOG['lessons'])}
    for lesson in CATALOG['lessons']:
        for prerequisite in lesson.get('depends', []):
            assert prerequisite in LESSONS, (lesson['id'], prerequisite)
            assert position[prerequisite] < position[lesson['id']], (lesson['id'], prerequisite)
            assert not LESSONS[prerequisite].get('optional'), (lesson['id'], prerequisite)
