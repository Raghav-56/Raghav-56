const core = require('@actions/core');
const { exec } = require('@actions/exec');

class GitActionBase {
  constructor() {
    this.result = null;
  }
  
  /**
   * Gets an input from GitHub Actions
   * @param {string} name - The input name
   * @param {boolean} required - Whether the input is required
   * @returns {string} The input value
   */
  getInput(name, required = false) {
    return core.getInput(name, { required });
  }
  
  /**
   * Sets an output for GitHub Actions
   * @param {string} name - The output name
   * @param {string} value - The output value
   */
  setOutput(name, value) {
    core.setOutput(name, value);
  }
  
  /**
   * Logs an info message
   * @param {string} message - The message to log
   */
  info(message) {
    core.info(message);
  }
  
  /**
   * Logs an error message and fails the action
   * @param {string|Error} error - The error to log
   */
  fail(error) {
    const message = error instanceof Error ? error.message : error;
    core.setFailed(message);
  }
  
  /**
   * Executes a command
   * @param {string} command - The command to execute
   * @param {string[]} args - The arguments to pass to the command
   * @returns {Promise<number>} The exit code
   */
  async exec(command, args) {
    return await exec(command, args);
  }
  
  /**
   * Configures Git for GitHub Actions
   * @returns {Promise<void>}
   */
  async configureGit() {
    await this.exec('git', ['config', '--global', 'user.name', 'github-actions[bot]']);
    await this.exec('git', ['config', '--global', 'user.email', 'github-actions[bot]@users.noreply.github.com']);
  }
  
  /**
   * Commits and pushes changes
   * @param {string} filePath - The file path to commit
   * @param {string} commitMessage - The commit message
   * @returns {Promise<void>}
   */
  async commitChanges(filePath, commitMessage) {
    await this.configureGit();
    await this.exec('git', ['add', filePath]);
    await this.exec('git', ['commit', '-m', commitMessage]);
    await this.exec('git', ['push']);
    this.info('Changes committed and pushed successfully');
  }
}

module.exports = GitActionBase;
