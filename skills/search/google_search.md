# Skill: Google Search

## When to use
Use this playbook whenever the task requires searching for information on Google.

## Steps

1. **Navigate** to `https://www.google.com`.
2. **Locate the search input** using the selector `input[name=q]`.
3. **Type** the search query into the input.
4. **Submit** the search by pressing Enter (`\n` appended to the text) or by clicking the search button (`input[type=submit][value="Google Search"]`).
5. **Wait** for results: `#search` or `#rso` should appear.
6. **Read results** from `#search` — each result is typically an `<h3>` inside an `<a>` within `#rso`.

## Tips
- If the "I'm Feeling Lucky" button intercepts the form, use the `input[name=q]` selector and append `\n` to the text to submit.
- Google sometimes shows a cookie/consent dialog — look for and click "Accept all" (`button` containing "Accept all") before searching.
- Use `get_page_content` after results load to extract text without needing complex selectors.
