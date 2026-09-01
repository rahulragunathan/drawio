# Known Issues

Open defects, most severe first. [ROADMAP.md](ROADMAP.md) carries the one-line index; this
file carries enough detail to pick an item up without digging.

Each entry has a stable ID — use it in branch names (`bugfix/ki-02-<slug>`) and in the
CHANGELOG entry that closes it. When fixed, delete it from here and from the ROADMAP index;
the record lives in [CHANGELOG.md](../CHANGELOG.md). IDs are never reused.

## Severity

| Level | Means |
|-------|-------|
| **Critical** | Loses or corrupts data, or sends wrong information to real recipients. |
| **High** | Silently produces a wrong result, or reports success without doing the work. |
| **Medium** | Wrong under conditions the operator can notice or work around. |
| **Low** | Cosmetic, or wrong in a field nothing consumes. |

---

<a id="ki-01"></a>
## KI-01 — The icon catalog publishes keys the generator helpers reject

**Severity:** Medium
**Where:** [references/icons.md](../references/icons.md) · [scripts/list_icons.py:253-256](../scripts/list_icons.py#L253-L256) · [assets/build_template.py:404-405](../assets/build_template.py#L404-L405)

### What happens

There are two icon key formats and the workflow crosses them.

The catalog and its tooling use a **hyphen**. `load_catalog()` splits the family off the
front of the key:

```python
key = m.group("key")
family = key.split("-", 1)[0]
```

so `--search lambda` prints `aws-lambda`, and `references/icons.md` opens with

```python
icon_box(40, 80, 220, 60, "Order Handler", fill=..., icon="aws-lambda")
```

The helpers use a **colon**. `icon_style()` in `assets/build_template.py` and in both
examples does:

```python
family, _, name = str(icon).partition(":")
kind, prefix, wrapper, glyph_key, bare = ICON_FAMILIES[family]
```

`"aws-lambda".partition(":")` yields the family `aws-lambda`, which is not a key of
`ICON_FAMILIES`, so the lookup raises. The two forms are related by replacing the first
hyphen with a colon, and nothing says so.

SKILL.md compounds it. Under "Choosing an icon" it states that names live in
`references/icons.md` as `family:name`. They do not — the catalog lists `aws-lambda` with
the draw.io name `lambda` in a separate column.

### Example scenario

Follow the documented workflow exactly:

```bash
python scripts/list_icons.py --search lambda      # prints: aws-lambda   lambda
```

Paste that key into a generator copied from the template:

```python
icon_box(620, 160, 220, 64, "<b>Handler</b>", fill=COMPUTE, icon="aws-lambda")
```

Running it raises `KeyError: 'aws-lambda'` before any XML is written. The user has to guess
that `aws:lambda` is meant. Verified against `assets/build_template.py` at the current
commit; `aws:lambda` returns
`shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;` as intended.

### Notes for a fix

Pick one format and make everything speak it. The colon form is the one the helpers, both
examples and SKILL.md already use, and it is the form that ends up in a diagram — so the
cheaper move is to change what the catalog side *emits*, not what the helpers accept:

- `--search` should print the string a user pastes (`aws:lambda`), not the internal row key.
- `references/icons.md`'s opening snippet must use the same string as its tables.
- `load_catalog()` keys the catalog dict on the row key, and `qualified_names()` and the
  `--verify` path both read `entry["family"]`. Changing the row key format touches
  `tests/test_list_icons.py`, which asserts parsed keys directly.

Accepting the hyphen form in `icon_style()` as well is a one-line alternative
(`partition(":")` then `partition("-")`), but it leaves two spellings in circulation and
does not fix the SKILL.md claim.

**The regression net is the gap that let this through:** no test builds a diagram from a key
the catalog actually publishes. Add one that reads a key out of `load_catalog()`, feeds it to
the template's `icon_style()`, and asserts a valid stencil name comes back. That test fails
today and would have caught this on the commit that introduced the catalog.
