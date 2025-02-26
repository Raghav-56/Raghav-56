# GitHub Profile Workflow Configuration

This document provides comprehensive information about the automated workflows used to keep your GitHub profile README dynamically updated.

## Architecture Overview

The system follows a modular architecture with object-oriented principles:

1. **Base Classes**: `GitActionBase.js` provides common functionality for all actions
2. **Reusable Actions**: Custom actions like `section-replacer` follow OOP principles
3. **Workflow Templates**: Reusable workflows (`common-workflow.yml`, `base-workflow.yml`) reduce duplication
4. **Centralized Configuration**: All constants are maintained in a single file

## Active Workflows

| Workflow | Schedule | Function | Implementation |
|----------|----------|----------|----------------|
| GitHub Stats | Daily at 00:45am | Updates GitHub statistics using waka-readme-stats | [github-stats.yml](.github/workflows/github-stats.yml) |
| Blog Posts | Daily at noon | Updates latest blog posts from RSS feeds | [blog-post-workflow.yml](.github/workflows/blog-post-workflow.yml) |

## Core Components

### Actions

- **GitActionBase** ([GitActionBase.js](.github/actions/GitActionBase.js))
  - Base class with common functionality (input handling, git operations, logging)
  - Provides methods like `configureGit()` and `commitChanges()`

- **SectionReplacer** ([section-replacer/index.js](.github/actions/section-replacer/index.js))
  - Class that handles finding and replacing sections in the README
  - Uses marker comments to identify section boundaries
  - Implements validation methods for file and section existence

- **Commit Changes** ([commit-changes/action.yml](.github/actions/commit-changes/action.yml))
  - Composite action for checking changes and committing them
  - Only commits when actual changes are detected

### Workflows

- **Base Workflow** ([base-workflow.yml](.github/workflows/base-workflow.yml))
  - Foundation workflow that handles repository checkout
  - Can be extended by other workflows

- **Common Workflow** ([common-workflow.yml](.github/workflows/common-workflow.yml))
  - Reusable workflow for standardized section updates
  - Handles section replacement and commits with configurable parameters

## Configuration Constants

All configuration is centralized in [workflow-constants.js](.github/config/workflow-constants.js):

```javascript
class WorkflowConstants {
  // Cron schedules for different workflows
  static schedules = {
    daily: "0 0 * * *",
    hourly: "15 */1 * * *",
    weekly: "0 0 * * 0",
    dailyQuote: "30 0 * * *",
    dailyStats: "45 0 * * *",
    dailyBlog: "0 12 * * *"
  };
  
  // GitHub-related constants
  static github = {
    username: "Raghav-56",
    apiBaseUrl: "https://api.github.com",
    defaultBranch: "main"
  };
  
  // Theme options for various components
  static themes = {
    default: "radical",
    light: "buefy",
    dark: "tokyonight"
  };

  // Section names for README updating
  static sections = {
    quote: "quote",
    projects: "projects",
    stats: "stats",
    blog: "blog",
    activity: "activity",
    spotify: "spotify"
  };
  
  // Paths to reusable actions
  static actions = {
    sectionReplacer: "./.github/actions/section-replacer",
    commitChanges: "./.github/actions/commit-changes"
  };
}
```

## Required Secrets

To use these workflows, configure these secrets in your repository settings:

- `GITHUB_TOKEN`: Automatically provided by GitHub for basic operations
- `GH_TOKEN`: (Optional) Personal access token with additional permissions for extended stats
- `WAKATIME_API_KEY`: Required for coding time statistics from WakaTime

## README Markdown Tags

There are two formats of section markers used in the README.md file:

### Format 1: BEGIN/END_SECTION
Used by the section-replacer action in workflows:

```markdown
<!-- BEGIN_SECTION:stats -->
## 📊 GitHub Stats
[This content will be automatically replaced]
<!-- END_SECTION:stats -->

<!-- BEGIN_SECTION:blog -->
## 📝 Latest Blog Posts
[This content will be automatically replaced]
<!-- END_SECTION:blog -->
```

### Format 2: SECTION_NAME:START/END
Used in the actual README.md file:

```markdown
<!-- GITHUB_STATS_SECTION:START -->
## 📊 GitHub Stats
[This content will be automatically replaced]
<!-- GITHUB_STATS_SECTION:END -->

<!-- BLOG_POST_SECTION:START -->
## 📝 Latest Blog Posts
[This content will be automatically replaced]
<!-- BLOG_POST_SECTION:END -->

<!-- QUOTE_SECTION:START -->
## 💭 Programming Quote of the Day
[This content will be automatically replaced]
<!-- QUOTE_SECTION:END -->
```

> ⚠️ **Important**: Make sure you're using the correct format when updating your README.md file or modifying the section-replacer action. The current implementation handles Format 2, but the action code is written for Format 1.

## How to Use This System

### Initial Setup

1. Fork or clone this repository
2. Add the required secrets to your repository settings:
   - Navigate to your repository → Settings → Secrets and variables → Actions
   - Add each required secret (WAKATIME_API_KEY, etc.)
3. Update your profile README.md with the appropriate section markers
4. Enable workflows from the Actions tab in your GitHub repository:
   - Go to the Actions tab
   - Select and enable each workflow

### Adding a New Section

1. Define a new section name in `WorkflowConstants.sections`
2. Add the corresponding section markers to your README.md
3. Create a new workflow file that:
   - Generates the content for your section
   - Uses the `section-replacer` action to update your README
   - Uses the `commit-changes` action to commit the changes

**Example new workflow file:**

```yaml
name: New Section Workflow

on:
  schedule:
    - cron: "0 0 * * *"  # Daily at midnight
  workflow_dispatch:      # Manual trigger

jobs:
  update-section:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Generate section content
        id: content-generator
        run: |
          # Your script to generate content
          CONTENT="## My New Section Content"
          echo "::set-output name=content::$CONTENT"

      - name: Replace section in README
        uses: ./.github/actions/section-replacer
        with:
          section-name: "my-section"
          section-content: ${{ steps.content-generator.outputs.content }}

      - uses: ./.github/actions/commit-changes
        with:
          commit-message: "Updated my section"
```

### Customizing Existing Sections

1. Locate the workflow file for the section you want to customize (e.g., `github-stats.yml`)
2. Update the workflow inputs or underlying action to customize the output
3. Commit the changes and trigger the workflow manually to test

## Troubleshooting

- **Workflow not running**: Check if workflows are enabled in your repository's Actions settings
- **Section not updating**: Ensure your README.md contains the correct section markers
- **Error in logs**: Check the full logs in the Actions tab for detailed error messages
- **API rate limits**: If seeing GitHub API rate limit errors, consider using a personal access token

## Development Guidelines

When extending this workflow system:

1. Follow object-oriented principles for better maintainability
2. Extend the base classes rather than duplicating code
3. Keep all configuration constants in the central constants file
4. Add thorough documentation for any new components
5. Use consistent section marker formats across all components
