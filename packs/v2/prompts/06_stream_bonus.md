# Bonus — a streaming parser, without an async framework

**Timebox: 20–30 minutes.** Implement `practice/round06_stream_bonus.py`.
Run `python -m pytest -q tests/test_06_stream_bonus.py -x`.

A chat transport supplies chunks of already-decoded text, not necessarily full
JSON messages. Parse newline-delimited JSON without buffering the whole response.

Valid lines look like:

```json
{"type":"token","value":"The contract says "}
{"type":"citation","value":"d7"}
```

Each line has exactly `type` and `value`; type is `token`/`citation`; value is a
string (including empty). Lines may be split anywhere across chunks or bundled
several to a chunk. Ignore blank lines; support LF/CRLF. Parse a final nonblank
line at clean EOF even without a trailing newline. Preserve Unicode and escaped
newlines inside JSON values.

Return an iterator of StreamEvent objects. Yield each complete event before
requesting more source input. Invalid JSON/schema raises InvalidStreamEvent.
Exceptions from the input source propagate unchanged, including after prior valid
events were already yielded. This is a deliberately small protocol, not SSE.

A test tries **every possible split** of a small event sequence, so do not assume
one input chunk equals one message.

## Architecture follow-up

How does byte decoding differ from this str-only exercise? What limit would you
place on an incomplete line? What would backpressure and client cancellation look
like? Would a truncated transport stream be the same as a clean end of response?
Where do citation existence and authorization validation belong?
