"""SEC client, cache, tag map, line-item resolver, FRED (SPEC §4–§6). Owner: A. Slices S1, S2, S3.

The only place in the app that downloads from the SEC or FRED. Every figure leaves this package as a
`src.contracts.Fact` with its source.
"""
