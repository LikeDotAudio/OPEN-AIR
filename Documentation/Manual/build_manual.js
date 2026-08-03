const fs = require('fs');
const path = require('path');
const { marked } = require('marked');

const REPO_ROOT = path.resolve(__dirname, '../../');
const MANUAL_OUT_DIR = __dirname;
const HTML_OUT_DIR = path.join(MANUAL_OUT_DIR, 'html');
const MD_SOURCE_DIR = path.join(MANUAL_OUT_DIR, 'markdown_source');

if (!fs.existsSync(HTML_OUT_DIR)) fs.mkdirSync(HTML_OUT_DIR, { recursive: true });
if (!fs.existsSync(MD_SOURCE_DIR)) fs.mkdirSync(MD_SOURCE_DIR, { recursive: true });

// 1. INGESTION PHASE: Move all loose .md files into markdown_source
function ingestMarkdownFiles(dir) {
  if (!fs.existsSync(dir)) return;
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    // Exclude certain directories
    if (fullPath.includes('node_modules') || 
        fullPath.includes('.crawler') || 
        fullPath.includes('.git') || 
        fullPath.includes('Documentation/Manual/html') || 
        fullPath.includes('Documentation/Manual/markdown_source') || 
        fullPath.includes('nmos-testing-tool') || 
        fullPath.includes('.gemini') || 
        fullPath.includes('TESTS/Protocols/nmos')) {
      continue;
    }

    if (fs.statSync(fullPath).isDirectory()) {
      ingestMarkdownFiles(fullPath);
    } else if (fullPath.toLowerCase().endsWith('.md')) {
      let relPath = path.relative(REPO_ROOT, fullPath);
      
      // Special case: Manual CHANGELOG.md goes to Development
      if (relPath === 'Documentation/Manual/CHANGELOG.md') {
        relPath = 'Development/CHANGELOG.md';
      } else if (relPath.startsWith('Documentation/Manual/')) {
        // Skip any other md files directly in Manual that we shouldn't touch
        continue;
      }

      const destPath = path.join(MD_SOURCE_DIR, relPath);
      const destDir = path.dirname(destPath);
      
      if (!fs.existsSync(destDir)) {
        fs.mkdirSync(destDir, { recursive: true });
      }

      // Move file (Copy then delete to ensure it works across devices/mounts if any, though renameSync is fine)
      fs.copyFileSync(fullPath, destPath);
      fs.unlinkSync(fullPath);
      console.log(`Migrated: ${fullPath} -> ${destPath}`);
    }
  }
}

console.log('Starting ingestion of markdown files...');
ingestMarkdownFiles(REPO_ROOT);
console.log('Ingestion complete.');

// 2. BUILD PHASE: Generate HTML from markdown_source

function findMarkdownFilesInSource(dir, fileList = []) {
  if (!fs.existsSync(dir)) return fileList;
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    if (fs.statSync(fullPath).isDirectory()) {
      findMarkdownFilesInSource(fullPath, fileList);
    } else if (fullPath.toLowerCase().endsWith('.md')) {
      fileList.push(fullPath);
    }
  }
  return fileList;
}

const allMdFiles = findMarkdownFilesInSource(MD_SOURCE_DIR);

const topicMappings = [
  { name: 'Roadmap', match: p => p === 'Documentation/Strategies/README.md' },
  { name: 'Overview & General Docs', match: p => p === 'README.md' || p.startsWith('Documentation/') },
  { name: 'Contracts', match: p => p.startsWith('contracts/') },
  { name: 'Front End & UI Library', match: p => p.startsWith('ui/') || p.startsWith('FrontEnd/') },
  { name: 'Back End & Core', match: p => p.startsWith('BackEnd/Instruments') || p.startsWith('BackEnd/Core') },
  { name: 'Back End Protocols', match: p => p.startsWith('BackEnd/ComProtocols') },
  { name: 'Yak System', match: p => p.startsWith('BackEnd/openair-yak') },
  { name: 'Test Protocols', match: p => p.startsWith('TESTS/Protocols') },
  { name: 'Docker & Deployment', match: p => p.startsWith('docker/') || p.startsWith('Deployment/') },
  { name: 'Development', match: p => p.startsWith('Development/') },
  { name: 'Other', match: p => true }
];

const menuMap = {};
topicMappings.forEach(t => menuMap[t.name] = []);

for (const fullPath of allMdFiles) {
  let relPath = path.relative(MD_SOURCE_DIR, fullPath);
  relPath = relPath.split(path.sep).join('/');
  
  let assignedTopic = 'Other';
  for (const t of topicMappings) {
    if (t.match(relPath)) {
      assignedTopic = t.name;
      break;
    }
  }

  let subtopicName = relPath;
  if (relPath === 'Documentation/Strategies/README.md') {
    subtopicName = 'Roadmap';
  } else if (subtopicName.toLowerCase().endsWith('readme.md') || subtopicName.toLowerCase().endsWith('changelog.md')) {
    const parts = subtopicName.split('/');
    if (parts.length > 1) {
      const fileName = parts[parts.length - 1].replace(/\.md$/i, '');
      subtopicName = parts[parts.length - 2] + ' (' + fileName + ')';
    } else {
      subtopicName = 'Project ' + parts[parts.length - 1].replace(/\.md$/i, '');
    }
  } else {
    subtopicName = subtopicName.replace(/\.md$/i, '');
    const parts = subtopicName.split('/');
    subtopicName = parts[parts.length - 1];
    if (parts.length > 2) {
      subtopicName = parts[parts.length - 2] + ' / ' + subtopicName;
    }
  }

  if (relPath.includes('FrontEnd/libControl')) {
    const parts = relPath.split('/');
    const libPart = parts.slice(parts.indexOf('libControl') + 1, -1).join(' / ');
    subtopicName = libPart ? 'libControl: ' + libPart : subtopicName;
  }

  menuMap[assignedTopic].push({
    name: subtopicName,
    source: relPath,
    fullPath: fullPath
  });
}

for (const topic in menuMap) {
  menuMap[topic].sort((a, b) => a.name.localeCompare(b.name));
  if (menuMap[topic].length === 0) {
    delete menuMap[topic];
  }
}

function getOutPath(topic, sourcePath) {
  const folder = topic.replace(/[^a-z0-9]/gi, '_').toLowerCase();
  const file = sourcePath.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.html';
  return { folder, file };
}

const cssContent = `
:root {
  --bg: #1e1e1e;
  --bg-panel: #252526;
  --bg-hover: #2a2d2e;
  --text: #cccccc;
  --text-heading: #ffffff;
  --accent: #007acc;
  --border: #3c3c3c;
  --sidebar-width: 320px;
}
body {
  margin: 0;
  padding: 0;
  display: flex;
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: var(--bg);
  color: var(--text);
}
#sidebar {
  width: var(--sidebar-width);
  background-color: var(--bg-panel);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  padding: 20px;
  font-size: 1.2rem;
  font-weight: bold;
  color: var(--text-heading);
  border-bottom: 1px solid var(--border);
}
.menu-group {
  padding: 0;
}
.menu-group-title {
  padding: 10px 20px;
  font-size: 0.9rem;
  text-transform: uppercase;
  color: #858585;
  font-weight: bold;
  cursor: pointer;
  user-select: none;
  background-color: var(--bg-panel);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
}
.menu-group-title:hover {
  background-color: var(--bg-hover);
}
.menu-group-title::before {
  content: '▶';
  display: inline-block;
  margin-right: 8px;
  font-size: 0.7em;
  transition: transform 0.2s ease-in-out;
}
.menu-group.expanded .menu-group-title::before {
  transform: rotate(90deg);
}
.menu-items-container {
  display: none;
  background-color: #1a1a1a;
  padding: 5px 0;
}
.menu-group.expanded .menu-items-container {
  display: block;
}
.menu-item {
  display: block;
  padding: 8px 20px 8px 40px;
  color: var(--text);
  text-decoration: none;
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.menu-item:hover, .menu-item.active {
  background-color: var(--bg-hover);
  color: var(--text-heading);
}
#content {
  flex: 1;
  background: var(--bg);
  display: flex;
  flex-direction: column;
}
iframe {
  border: none;
  width: 100%;
  height: 100%;
  background: #ffffff;
}
`;
fs.writeFileSync(path.join(MANUAL_OUT_DIR, 'style.css'), cssContent);

let menuHtml = '';
let firstLink = '';

for (const topic of topicMappings.map(t => t.name)) {
  if (!menuMap[topic] || menuMap[topic].length === 0) continue;
  
  menuHtml += '<div class="menu-group"><div class="menu-group-title">' + topic + '</div><div class="menu-items-container">';
  for (const sub of menuMap[topic]) {
    const out = getOutPath(topic, sub.source);
    const link = 'html/' + out.folder + '/' + out.file;
    if (!firstLink) firstLink = link;
    menuHtml += '<a class="menu-item" href="' + link + '" target="contentFrame" title="' + sub.name + '">' + sub.name + '</a>';
  }
  menuHtml += '</div></div>';
}

const indexHtml = '<!DOCTYPE html>\\n' +
'<html lang="en">\\n' +
'<head>\\n' +
'  <meta charset="UTF-8">\\n' +
'  <meta name="viewport" content="width=device-width, initial-scale=1.0">\\n' +
'  <title>OPEN-AIR Manual</title>\\n' +
'  <link rel="stylesheet" href="style.css">\\n' +
'</head>\\n' +
'<body>\\n' +
'  <div id="sidebar">\\n' +
'    <div class="sidebar-header">OPEN-AIR Comprehensive Manual</div>\\n' +
'    ' + menuHtml + '\\n' +
'  </div>\\n' +
'  <div id="content">\\n' +
'    <iframe name="contentFrame" src="' + firstLink + '"></iframe>\\n' +
'  </div>\\n' +
'  <script>\\n' +
'    const groups = document.querySelectorAll(".menu-group-title");\\n' +
'    groups.forEach(title => {\\n' +
'      title.addEventListener("click", function() {\\n' +
'        this.parentElement.classList.toggle("expanded");\\n' +
'      });\\n' +
'    });\\n\\n' +
'    const links = document.querySelectorAll(".menu-item");\\n' +
'    links.forEach(link => {\\n' +
'      link.addEventListener("click", function() {\\n' +
'        links.forEach(l => l.classList.remove("active"));\\n' +
'        this.classList.add("active");\\n' +
'      });\\n' +
'    });\\n' +
'    if (links.length > 0) links[0].classList.add("active");\\n' +
'  </script>\\n' +
'</body>\\n' +
'</html>';
fs.writeFileSync(path.join(MANUAL_OUT_DIR, 'index.html'), indexHtml.replace(/\\n/g, '\n'));

const now = new Date().toLocaleString();
const pageCss = `
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  padding: 40px;
  max-width: 900px;
  margin: 0 auto;
  color: #333;
}
pre { background: #f6f8fa; padding: 16px; overflow-x: auto; border-radius: 6px; }
code { font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace; background: #f6f8fa; padding: 0.2em 0.4em; border-radius: 3px; }
table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background-color: #f2f2f2; }
blockquote { border-left: 4px solid #dfe2e5; color: #6a737d; padding-left: 1em; margin-left: 0; }
.timestamp { margin-top: 50px; font-size: 0.85em; color: #666; border-top: 1px solid #eee; padding-top: 20px; }
`;

let pagesGenerated = 0;
for (const topic in menuMap) {
  const folderName = getOutPath(topic, '').folder;
  const folderPath = path.join(HTML_OUT_DIR, folderName);
  if (!fs.existsSync(folderPath)) {
    fs.mkdirSync(folderPath, { recursive: true });
  }

  for (const sub of menuMap[topic]) {
    let mdContent = fs.readFileSync(sub.fullPath, 'utf8');
    
    if (sub.source === 'Documentation/Strategies/README.md') {
      mdContent = '# Roadmap\\n\\n' + mdContent;
    }

    const htmlContent = marked.parse(mdContent);
    const out = getOutPath(topic, sub.source);
    const filePath = path.join(folderPath, out.file);

    const fullHtml = '<!DOCTYPE html>\\n' +
'<html lang="en">\\n' +
'<head>\\n' +
'  <meta charset="UTF-8">\\n' +
'  <title>' + sub.name + ' - ' + topic + '</title>\\n' +
'  <style>' + pageCss + '</style>\\n' +
'</head>\\n' +
'<body>\\n' +
'  ' + htmlContent + '\\n' +
'  <div class="timestamp">\\n' +
'    Manual generated / updated: <strong>' + now + '</strong><br>\\n' +
'    Source file: <code>' + sub.source + '</code>\\n' +
'  </div>\\n' +
'</body>\\n' +
'</html>';

    fs.writeFileSync(filePath, fullHtml.replace(/\\n/g, '\n'));
    pagesGenerated++;
  }
}

console.log('Comprehensive Manual built successfully. Total pages generated:', pagesGenerated);
