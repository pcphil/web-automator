# Skill: GitHub Navigation

## When to use
Use this playbook for any task involving GitHub — browsing repos, searching code, finding trending projects, reading files, etc.

## Key URL Patterns

| Goal | URL |
|---|---|
| User profile | `https://github.com/<username>` |
| Repository | `https://github.com/<owner>/<repo>` |
| Specific file | `https://github.com/<owner>/<repo>/blob/<branch>/<path>` |
| Code search | `https://github.com/search?q=<query>&type=code` |
| Repo search | `https://github.com/search?q=<query>&type=repositories` |
| Trending repos | `https://github.com/trending` |
| Trending by language | `https://github.com/trending/<language>` |

## Common Tasks

### Find trending repos
1. Navigate to `https://github.com/trending` (or `https://github.com/trending/python` for a language).
2. Use `get_page_content` to read the list — repo names and descriptions appear as `<h2>` links.

### Search for repos or code
1. Navigate to `https://github.com/search?q=<encoded-query>&type=repositories`.
2. Wait for `.search-title` or `[data-testid="results-list"]`.
3. Use `get_page_content` or `extract` to list results.

### Read a file in a repo
1. Navigate to the file URL: `https://github.com/<owner>/<repo>/blob/main/<path>`.
2. The rendered file content is in `#read-only-cursor-text-area` or `.highlight` code blocks.
3. Use `get_page_content` to extract the text.

### Clone/download info
- The "Code" button reveals the clone URL — click `#local-panel` then read `input[aria-label="github-clone-url"]`.

## Tips
- GitHub may require sign-in for some actions; prefer read-only public URLs.
- Rate limiting can occur on rapid repeated requests — add `wait_for` calls between navigations if needed.
- The file tree on the left is inside `[aria-label="File Tree"]`; individual items are `a[role="treeitem"]`.
