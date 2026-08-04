const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const MD_SOURCE_DIR = path.join(__dirname, 'markdown_source');
const MAX_AGE_DAYS = 180;
const MAX_AGE_MS = MAX_AGE_DAYS * 24 * 60 * 60 * 1000;
const now = Date.now();

function findMarkdownFiles(dir, fileList = []) {
  if (!fs.existsSync(dir)) return fileList;
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    if (fs.statSync(fullPath).isDirectory()) {
      findMarkdownFiles(fullPath, fileList);
    } else if (fullPath.toLowerCase().endsWith('.md')) {
      fileList.push(fullPath);
    }
  }
  return fileList;
}

const allMdFiles = findMarkdownFiles(MD_SOURCE_DIR);
let hasStale = false;

console.log(`Checking for documents older than ${MAX_AGE_DAYS} days...`);

for (const file of allMdFiles) {
  try {
    // Get last commit timestamp for the file
    // We use --follow just in case it was moved recently, though it may not always be perfect
    // If not in git yet, this might fail or return empty, we handle that by falling back to fs.stat
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
  console.error(`\\nERROR: Stale documentation detected. Please review and update (or touch) the stale files.`);
  console.error(`The manual is the repository of truth and must be kept up to date.`);
  process.exit(1);
} else {
  console.log('✅ No stale documents found. Manual is up to date.');
}
