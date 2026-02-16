# Profile README Automation

This repository uses GitHub Actions to keep sections of `README.md` updated.

## Active workflows

- `.github/workflows/profile-readme-sync.yml`
  - Updates the activity section (`START_SECTION:activity`) daily.
- `.github/workflows/update-featured-projects.yml`
  - Refreshes featured repositories weekly using the GitHub API.
- `.github/workflows/update-quote.yml`
  - Refreshes the quote section daily using GitHub Zen.

## Section markers in `README.md`

The workflows depend on marker comments:

- `<!-- PROJECTS_SECTION:START -->` ... `<!-- PROJECTS_SECTION:END -->`
- `<!-- QUOTE_SECTION:START -->` ... `<!-- QUOTE_SECTION:END -->`
- `<!--START_SECTION:activity-->` ... `<!--END_SECTION:activity-->`

Keep these markers intact so automation can replace the section body safely.

## Design notes

- Root `README.md` is the only source of truth.
- Workflows commit only when content actually changes.
- Schedules are conservative to avoid noisy commit history.
