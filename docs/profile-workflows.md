# Profile README Automation

This repository uses GitHub Actions to keep sections of `README.md` updated.

## Active workflows

- `.github/workflows/profile-readme-sync.yml`
  - Updates the activity section (`START_SECTION:activity`) daily.
- `.github/workflows/update-featured-projects.yml`
  - Refreshes featured repositories weekly using the GitHub API.
- `.github/workflows/update-profile-cards.yml`
  - Generates cards daily from the pinned revision of your fork, using the repository workflow token.
- `.github/workflows/update-quote.yml`
  - Refreshes the quote section daily using GitHub Zen.

## Section markers in `README.md`

The workflows depend on marker comments:

- `<!-- PROJECTS_SECTION:START -->` ... `<!-- PROJECTS_SECTION:END -->`
- `<!-- PROFILE_CARDS:START -->` ... `<!-- PROFILE_CARDS:END -->`
- `<!-- QUOTE_SECTION:START -->` ... `<!-- QUOTE_SECTION:END -->`
- `<!--START_SECTION:activity-->` ... `<!--END_SECTION:activity-->`

Keep these markers intact so automation can replace the section body safely.

## Design notes

- Root `README.md` is the only source of truth.
- Workflows commit only when content actually changes.
- Schedules are conservative to avoid noisy commit history.

## Profile cards

The card workflow runs on GitHub-hosted Actions runners and queries GitHub's API with the temporary repository token. It stores the selected SVGs in this public repository and embeds them in the README after validating both files. It does not use a hosted card endpoint or a personal access token. The fork's analytics is disabled in this workflow.

Run **Update profile cards** from the Actions tab to generate the first cards after this workflow reaches the default branch. The fork also attempts other cards; GitHub denies its profile-details query with the repository token, so those cards are not used. If a selected card fails to generate, validation stops the workflow without committing partial output. The output is public.
