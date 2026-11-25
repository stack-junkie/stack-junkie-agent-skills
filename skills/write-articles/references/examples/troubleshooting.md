> Instructional troubleshooting example, created October 4, 2026. Not attributed to the owner. RFC 8259 checked on that date. The illustrated rejection and corrected parse were reproduced with the local Node.js runtime; no application's configuration schema was tested.

# Fix a trailing comma in strict JSON

A comma immediately before the closing brace is invalid in a JSON object. The grammar permits a comma between members, followed by another member, rather than a final separator on its own. [RFC 8259, section 4](https://www.rfc-editor.org/rfc/rfc8259.html#section-4).

Consider this deliberately broken input:

```text
{"theme":"dark",}
```

The useful clue is the comma after `"dark"`. The closing brace follows it instead of another property. This example is small enough to diagnose without changing anything else.

## Confirm the syntax failure

If Node.js is already available, start its interactive prompt with `node` and enter:

```javascript
JSON.parse('{"theme":"dark",}')
```

The authoring check rejected that string with a `SyntaxError`. Exact wording can vary, so the diagnostic point is rejection of this input, not a particular sentence. A production application's error should still be read on its own terms.

Before editing a real configuration, confirm that the application expects strict JSON. This diagnosis concerns the illustrated grammar error. Do not remove punctuation from a different format merely because it looks similar.

## Make the smallest correction

Remove only the final comma:

```json
{"theme":"dark"}
```

Check the corrected string in the same Node prompt:

```javascript
JSON.parse('{"theme":"dark"}').theme
```

The reproduced result was the string `dark`. No property was renamed and no value changed. For a real file, preserve a copy before editing, then use the application's normal configuration-loading path after checking syntax.

## If the application still refuses the file

Successful parsing answers a narrow question: the parser accepted the text. It does not show that the application recognizes `theme` or accepts `dark` as a value. Those names are demonstration data, not a claim about a particular product.

Inspect the application's own schema or documentation. Compare the reported property and value with its allowed configuration. If parsing still fails instead, examine the reported location for another syntax issue before changing unrelated settings.

Keep the repair minimal. One isolated correction and one clear confirmation are more useful than speculative edits that make the original cause impossible to identify.
