# Skill: Form Filling

## When to use
Use this playbook whenever the task involves filling out and submitting a web form (registration, contact, checkout, login, etc.).

## General Strategy

1. **Inspect the form** — call `get_page_content` or `screenshot` to understand the fields present.
2. **Match labels to inputs** — labels often use `for="<input-id>"`. The corresponding input has `id="<input-id>"`.
3. **Fill required fields first** — required fields usually have `required` attribute or a visible asterisk (*).
4. **Handle each field type**:
   - **Text / email / password / number**: use `type` tool with the appropriate CSS selector.
   - **Textarea**: same as text input (`textarea#id` or `textarea[name=...]`).
   - **Checkbox**: use `click` — check current state with `screenshot` first.
   - **Radio button**: use `click` on the specific `input[type=radio][value="<option>"]`.
   - **Select / dropdown**: use `click` on the `<select>` element, then `click` on the desired `<option>` — or type directly if it's a searchable select.
5. **Submit the form**:
   - Look for `button[type=submit]` or `input[type=submit]`.
   - Alternatively, press Enter in the last text field.
6. **Verify submission** — after clicking submit, use `get_page_content` or `screenshot` to confirm a success message or redirect.

## Selector Tips

| Field | Selector strategy |
|---|---|
| Input by label text | First find `label` with the text, read its `for` attr, then `#<that-id>` |
| Input by placeholder | `input[placeholder="Email address"]` |
| Input by name | `input[name="email"]` |
| Submit button | `button[type=submit]`, `input[type=submit]`, `button:has-text("Submit")` |
| Dropdown | `select[name="country"]` then `option[value="US"]` |

## Common Pitfalls
- **Validation errors**: after submit, look for `.error`, `.alert`, or `[aria-live]` regions that may show inline errors.
- **CAPTCHA**: if a CAPTCHA is present, note it in the `done` result — the agent cannot solve it.
- **Multi-step forms**: submit each step individually and wait for the next section to load before continuing.
- **Auto-fill conflicts**: if the browser auto-fills a field incorrectly, use `click` to focus it, then `type` to overwrite.
