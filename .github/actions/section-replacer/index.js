const fs = require('fs');
const core = require('@actions/core');
const { exec } = require('@actions/exec');

class SectionReplacer {
  constructor(sectionName, sectionContent, readmePath) {
    this.sectionName = sectionName;
    this.sectionContent = sectionContent;
    this.readmePath = readmePath;
    
    // Support both formats of section markers
    this.possibleStartMarkers = [
      `<!-- BEGIN_SECTION:${sectionName} -->`,
      `<!-- ${sectionName.toUpperCase()}_SECTION:START -->`
    ];
    
    this.possibleEndMarkers = [
      `<!-- END_SECTION:${sectionName} -->`,
      `<!-- ${sectionName.toUpperCase()}_SECTION:END -->`
    ];
  }

  validateFile() {
    if (!fs.existsSync(this.readmePath)) {
      throw new Error(`README file not found at ${this.readmePath}`);
    }
    return this;
  }

  getReadmeContent() {
    this.readmeContent = fs.readFileSync(this.readmePath, 'utf8');
    return this;
  }

  validateSection() {
    // Find which marker pattern is used in the README
    this.startMarker = this.possibleStartMarkers.find(marker => 
      this.readmeContent.includes(marker)
    );
    
    this.endMarker = this.possibleEndMarkers.find(marker => 
      this.readmeContent.includes(marker)
    );
    
    if (!this.startMarker || !this.endMarker) {
      throw new Error(`Section markers for "${this.sectionName}" not found in README`);
    }
    
    core.info(`Found markers: "${this.startMarker}" and "${this.endMarker}"`);
    return this;
  }

  replaceSection() {
    const startIndex = this.readmeContent.indexOf(this.startMarker);
    const endIndex = this.readmeContent.indexOf(this.endMarker) + this.endMarker.length;
    
    this.newContent = 
      this.readmeContent.substring(0, startIndex) + 
      this.startMarker + '\n' +
      this.sectionContent + '\n' +
      this.endMarker +
      this.readmeContent.substring(endIndex);
    
    return this;
  }

  writeChanges() {
    fs.writeFileSync(this.readmePath, this.newContent);
    core.info(`Successfully updated section "${this.sectionName}" in ${this.readmePath}`);
    return this;
  }
}

async function run() {
  try {
    // Get inputs
    const sectionName = core.getInput('section-name');
    const sectionContent = core.getInput('section-content');
    const readmePath = core.getInput('readme-path');
    const shouldCommit = core.getInput('commit') === 'true';
    const commitMessage = core.getInput('commit-message');

    // Use the SectionReplacer class
    const replacer = new SectionReplacer(sectionName, sectionContent, readmePath);
    
    replacer
      .validateFile()
      .getReadmeContent()
      .validateSection()
      .replaceSection()
      .writeChanges();

    // Commit changes if requested
    if (shouldCommit) {
      await exec('git', ['config', '--global', 'user.name', 'github-actions[bot]']);
      await exec('git', ['config', '--global', 'user.email', 'github-actions[bot]@users.noreply.github.com']);
      await exec('git', ['add', readmePath]);
      await exec('git', ['commit', '-m', commitMessage]);
      await exec('git', ['push']);
      core.info('Changes committed and pushed successfully');
    }

  } catch (error) {
    core.setFailed(`Action failed with error: ${error.message}`);
  }
}

run();
