import json
import pytest
from practice.round06_stream_bonus import StreamEvent, InvalidStreamEvent, parse_events


def line(kind="token", value="hello"):
    return json.dumps({"type": kind, "value": value}, ensure_ascii=False)


def test_stream_empty_input_and_blank_lines():
    assert list(parse_events([])) == []
    assert list(parse_events(["", " \n\r\n"])) == []


def test_stream_multiple_events_in_one_chunk():
    data = line(value="Hi") + "\n" + line("citation", "d7") + "\n"
    assert list(parse_events([data])) == [StreamEvent("token", "Hi"), StreamEvent("citation", "d7")]


def test_stream_every_possible_split_including_escaped_newline_and_unicode():
    data = line(value="hello\nZürich ⚖") + "\n" + line("citation", "d1")
    expected = [StreamEvent("token", "hello\nZürich ⚖"), StreamEvent("citation", "d1")]
    for split in range(len(data) + 1):
        assert list(parse_events([data[:split], data[split:]])) == expected


def test_stream_one_character_chunks():
    assert list(parse_events(iter(line(value="abc") + "\n"))) == [StreamEvent("token", "abc")]


def test_stream_no_trailing_newline_and_crlf():
    assert list(parse_events([line(value="a") + "\r\n" + line(value="b")])) == [
        StreamEvent("token", "a"), StreamEvent("token", "b")]


def test_stream_yields_before_reading_unneeded_future_input():
    def source():
        yield line(value="first") + "\n"
        raise RuntimeError("upstream broke later")
    stream = parse_events(source())
    assert next(stream) == StreamEvent("token", "first")
    with pytest.raises(RuntimeError, match="upstream broke later"):
        next(stream)


def test_stream_can_yield_two_buffered_lines_before_reading_more_input():
    def source():
        yield line(value="a") + "\n" + line(value="b") + "\n"
        raise RuntimeError("no more input")
    stream = parse_events(source())
    assert next(stream) == StreamEvent("token", "a")
    assert next(stream) == StreamEvent("token", "b")


@pytest.mark.parametrize("invalid", ["not json", "{}", "[]", '"text"',
    '{"type":"other","value":"x"}', '{"type":"token","value":12}',
    '{"type":"token","value":null}', '{"type":"token"}',
    '{"type":"token","value":"x","extra":true}', '{"type":[],"value":"x"}'])
def test_stream_invalid_json_or_schema(invalid):
    with pytest.raises(InvalidStreamEvent):
        list(parse_events([invalid + "\n"]))


def test_stream_malformed_final_line_at_eof():
    with pytest.raises(InvalidStreamEvent):
        list(parse_events(['{"type":']))


def test_stream_prior_events_remain_yielded_before_error():
    stream = parse_events([line(value="ok") + "\nnot json\n"])
    assert next(stream) == StreamEvent("token", "ok")
    with pytest.raises(InvalidStreamEvent):
        next(stream)


def test_stream_empty_token_value_is_allowed():
    assert list(parse_events([line(value="")])) == [StreamEvent("token", "")]
