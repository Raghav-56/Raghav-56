class WorkflowConstants {
  static schedules = {
    daily: "0 0 * * *",       // Daily at midnight
    hourly: "15 */1 * * *",   // 15 minutes past each hour
    weekly: "0 0 * * 0",      // Weekly on Sunday
    dailyQuote: "30 0 * * *", // 12:30am daily
    dailyStats: "45 0 * * *", // 00:45am daily
    dailyBlog: "0 12 * * *"   // Daily at noon
  };
  
  static github = {
    username: "Raghav-56",
    apiBaseUrl: "https://api.github.com",
    defaultBranch: "main"
  };
  
  static themes = {
    default: "radical",
    light: "buefy",
    dark: "tokyonight"
  };

  static sections = {
    quote: "quote",
    projects: "projects",
    stats: "stats",
    blog: "blog",
    activity: "activity",
    spotify: "spotify"
  };
  
  static actions = {
    sectionReplacer: "./.github/actions/section-replacer",
    commitChanges: "./.github/actions/commit-changes"
  };
}

module.exports = WorkflowConstants;
