const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const HTML_DIR = path.join(__dirname, 'html');
const MAX_AGE_DAYS = 180;
const MAX_AGE_MS = MAX_AGE_DAYS * 24 * 60 * 60 * 1000;
const now = Date.now();

function findHtmlFiles(dir, fileList = []) {
  if (!fs.existsSync(dir)) return fileList;
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    if (fs.statSync(fullPath).isDirectory()) {
      findHtmlFiles(fullPath, fileList);
    } else if (fullPath.toLowerCase().endsWith('.html')) {
      fileList.push(fullPath);
    }
  }
  return fileList;
}

const allHtmlFiles = findHtmlFiles(HTML_DIR);
let hasStale = false;

console.log(`Checking for HTML documents older than ${MAX_AGE_DAYS} days...`);

for (const file of allHtmlFiles) {
  try {
    // Get last commit timestamp for the file
    const gitCmd = `git log -1 --format="%at" --follow -- "${file}"`;
    let timestampStr = execSync(gitCmd, { cwd: __dirname, encoding: 'utf8' }).trim();
    
    let lastModifiedMs;
    if (timestampStr) {
      lastModifiedMs = parseInt(timestampStr, 10) * 1000;
    } else {
      // Fallback for uncommitted files
      lastModifiedMs = fs.statSync(file).mtimeMs;
    }

    const ageDays = (now - lastModifiedMs) / (1000 * 60 * 60 * 24);
    
    if (ageDays > MAX_AGE_DAYS) {
      console.error(`❌ STALE DOCUMENT FOUND: ${path.relative(__dirname, file)} (Last modified ${Math.round(ageDays)} days ago)`);
      hasStale = true;
    }
  } catch (err) {
    console.warn(`⚠️ Could not check age for ${file} (maybe not in git yet)`);
  }
}

if (hasStale) {
  console.error(`\\nERROR: Stale HTML documentation detected. Please review and update (or touch) the stale files.`);
  console.error(`The manual is the repository of truth and must be kept up to date.`);
  process.exit(1);
} else {
  console.log('✅ No stale HTML documents found. Manual is up to date.');
}
