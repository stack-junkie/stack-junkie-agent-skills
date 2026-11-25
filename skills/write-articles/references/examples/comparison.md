> Instructional comparison example, created October 4, 2026. Not attributed to the owner. RFC 9110 checked on that date. This compares protocol semantics, not measured client behavior.

# HTTP 307 or 308: choose by the lifetime of the move

Choose 307 for a temporary redirect and 308 for a permanent move when the request method must be preserved. The intended lifetime of the destination determines the choice. [RFC 9110's redirection definitions](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.4).

## Compare the same criteria

| Criterion | 307 | 308 |
| --- | --- | --- |
| Move | Temporary | Permanent |
| Method on automatic redirect | Preserved | Preserved |
| Future references | Original URI | New permanent URI |

The [307 definition](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.4.8) and [308 definition](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.4.9) establish these meanings. The table does not claim that every deployed client implements them correctly.

## A temporary intake route

Suppose a service accepts requests at `/intake`, while maintenance temporarily routes work to `/intake-backup`. This is an illustrative design scenario, not a running service.

The requirement is to preserve the method while keeping `/intake` as the address callers should use later. That makes 307 the fit under the documented temporary-redirect semantics. [RFC 9110, section 15.4.8](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.4.8).

Write down the intended return date or condition before choosing the implementation. That decision belongs in the operational plan.

## A permanent intake migration

Now suppose `/intake-v2` becomes the intended permanent address. The method requirement remains, but future references should move. That points to 308. [RFC 9110, section 15.4.9](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.4.9).

Identify callers and define a check that observes the destination request, including the method and relevant content. Run it in an authorized test environment rather than inferring behavior from a name.

For example, the service owner might agree on a sample request, record what reaches each endpoint, and check the client after the redirect is removed or retained as planned. These are proposed validation steps, not results obtained for this article.

Decide whether the move is temporary or permanent, preserve the method requirement, and test the actual caller.
