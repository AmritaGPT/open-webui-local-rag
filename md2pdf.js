#!/usr/bin/env node

/**
 * Reusable Markdown to PDF compiler with Mermaid support and custom styling
 * Usage: node md2pdf.js -i <input.md> -o <output.pdf> [options]
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function showHelp() {
  console.log(`
📄 MD to PDF Compiler (with Mermaid support)
============================================
Compiles Markdown files with Mermaid diagrams into professional PDFs.

Usage:
  node md2pdf.js -i <input.md> -o <output.pdf> [options]

Options:
  -i, --input        [Required] Path to the input markdown file
  -o, --output       [Required] Path to save the compiled PDF
  --title            [Optional] Document title in the header (Defaults to filename)
  --confidential     [Optional] Label in header (e.g. "CONFIDENTIAL", "DRAFT", "INTERNAL USE")
  --footer-left      [Optional] Text on the left of the footer (Defaults to "Page X of Y" on right)
  --theme-color      [Optional] Hex/CSS color for headers and accents (Defaults to #1A365D / #3182CE)
  --no-header        [Optional] Disable the page header completely
  --no-footer        [Optional] Disable the page footer completely

Example:
  node md2pdf.js -i report.md -o report.pdf --title "Q3 Business Report" --confidential "INTERNAL ONLY"
  `);
  process.exit(0);
}

// Simple CLI argument parser
const args = {};
const argv = process.argv.slice(2);

if (argv.includes('-h') || argv.includes('--help') || argv.length === 0) {
  showHelp();
}

for (let i = 0; i < argv.length; i++) {
  const arg = argv[i];
  if (arg === '-i' || arg === '--input') {
    args.input = argv[++i];
  } else if (arg === '-o' || arg === '--output') {
    args.output = argv[++i];
  } else if (arg === '--title') {
    args.title = argv[++i];
  } else if (arg === '--confidential') {
    args.confidential = argv[++i];
  } else if (arg === '--footer-left') {
    args.footerLeft = argv[++i];
  } else if (arg === '--theme-color') {
    args.themeColor = argv[++i];
  } else if (arg === '--no-header') {
    args.noHeader = true;
  } else if (arg === '--no-footer') {
    args.noFooter = true;
  }
}

if (!args.input || !args.output) {
  console.error('❌ Error: Input and output file paths are required.');
  showHelp();
}

const inputPath = path.resolve(args.input);
const outputPath = path.resolve(args.output);

if (!fs.existsSync(inputPath)) {
  console.error(`❌ Error: Input file does not exist at "${inputPath}"`);
  process.exit(1);
}

// Create a unique temporary directory inside workspace
const tempDirName = `temp_pdf_${Date.now()}`;
const tempDir = path.join(__dirname, 'temp_pdf_render', tempDirName);
fs.mkdirSync(tempDir, { recursive: true });

try {
  const inputBaseName = path.basename(inputPath, '.md');
  const tempInputPath = path.join(tempDir, 'temp_input.md');
  const tempCompiledPath = path.join(tempDir, 'temp_compiled.md');
  const puppeteerConfigPath = path.join(tempDir, 'puppeteer-config.json');

  // Copy original markdown to temp directory
  fs.copyFileSync(inputPath, tempInputPath);

  // Write Puppeteer config with no-sandbox
  fs.writeFileSync(puppeteerConfigPath, JSON.stringify({ args: ["--no-sandbox"] }), 'utf8');

  // Step 1: Render Mermaid diagrams (if any)
  console.log('⏳ Scanning and rendering Mermaid diagrams...');
  let hasMermaid = false;
  const content = fs.readFileSync(tempInputPath, 'utf8');
  if (content.includes('```mermaid') || content.includes(':::mermaid')) {
    hasMermaid = true;
  }

  if (hasMermaid) {
    const mmdcCmd = `npx @mermaid-js/mermaid-cli -i "${tempInputPath}" -o "${tempCompiledPath}" --puppeteerConfigFile "${puppeteerConfigPath}"`;
    execSync(mmdcCmd, { cwd: tempDir, stdio: 'inherit' });
  } else {
    // If no mermaid, just copy as compiled
    fs.copyFileSync(tempInputPath, tempCompiledPath);
  }

  // Step 2: Inject premium YAML front-matter styles & custom headers/footers
  console.log('🎨 Ingesting styles and custom header/footer templates...');
  let compiledContent = fs.readFileSync(tempCompiledPath, 'utf8');

  // Check if the file already has front matter to avoid overriding user's custom settings
  const hasFrontMatter = compiledContent.trim().startsWith('---');

  if (!hasFrontMatter) {
    const docTitle = args.title || inputBaseName.replace(/[_-]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    const confidentiality = args.confidential || '';
    const footerLeftText = args.footerLeft || 'Document Report';
    const mainThemeColor = args.themeColor || '#1A365D';
    const accentThemeColor = args.themeColor || '#3182CE';

    // Build the dynamic header template
    const headerHtml = args.noHeader ? '' : `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 8px; color: #718096; width: 100%; display: flex; justify-content: space-between; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px; margin-left: 20mm; margin-right: 20mm;">
      <span>${docTitle}</span>
      <span style="font-weight: bold; color: ${accentThemeColor};">${confidentiality}</span>
    </div>`;

    // Build the dynamic footer template
    const footerHtml = args.noFooter ? '' : `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 8px; color: #718096; width: 100%; display: flex; justify-content: space-between; border-top: 1px solid #E2E8F0; padding-top: 8px; margin-left: 20mm; margin-right: 20mm;">
      <span>${footerLeftText}</span>
      <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
    </div>`;

    const frontMatter = `---
pdf_options:
  format: A4
  margin:
    top: ${args.noHeader ? '20mm' : '25mm'}
    bottom: ${args.noFooter ? '20mm' : '25mm'}
    left: 20mm
    right: 20mm
  printBackground: true
  headerTemplate: |${headerHtml.split('\n').map(line => '    ' + line).join('\n')}
  footerTemplate: |${footerHtml.split('\n').map(line => '    ' + line).join('\n')}
css: |
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #2D3748;
    line-height: 1.65;
    font-size: 10.5pt;
  }
  
  h1 {
    font-size: 22pt;
    color: ${mainThemeColor};
    border-bottom: 2px solid ${accentThemeColor};
    padding-bottom: 8px;
    margin-top: 0;
    margin-bottom: 20px;
    page-break-after: avoid;
  }
  
  h2 {
    font-size: 15pt;
    color: ${accentThemeColor};
    border-bottom: 1px solid #E2E8F0;
    padding-bottom: 6px;
    margin-top: 30px;
    margin-bottom: 12px;
    page-break-after: avoid;
  }
  
  h3 {
    font-size: 11.5pt;
    color: ${mainThemeColor};
    margin-top: 20px;
    margin-bottom: 8px;
    page-break-after: avoid;
  }
  
  p {
    margin-bottom: 12px;
    text-align: justify;
  }
  
  hr {
    border: 0;
    border-top: 1px solid #E2E8F0;
    margin: 25px 0;
  }
  
  /* Tables styling */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    page-break-inside: avoid;
  }
  
  th {
    background-color: #F7FAFC;
    color: #2D3748;
    font-weight: 600;
    border-bottom: 2px solid #E2E8F0;
    padding: 10px 12px;
    text-align: left;
    font-size: 9.5pt;
  }
  
  td {
    border-bottom: 1px solid #E2E8F0;
    padding: 10px 12px;
    font-size: 9pt;
    vertical-align: top;
  }
  
  tr:nth-child(even) {
    background-color: #F8FAFC;
  }
  
  /* Code blocks */
  code {
    font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, Courier, monospace;
    font-size: 8.5pt;
    background-color: #EDF2F7;
    padding: 2px 5px;
    border-radius: 4px;
    color: #805AD5;
  }
  
  pre {
    background-color: #F7FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 12px 15px;
    overflow: auto;
    page-break-inside: avoid;
    margin: 15px 0;
  }
  
  pre code {
    background-color: transparent;
    padding: 0;
    color: #2D3748;
    font-size: 8pt;
  }
  
  /* Lists */
  ul, ol {
    margin-bottom: 12px;
    padding-left: 20px;
  }
  
  li {
    margin-bottom: 5px;
  }
  
  /* Task List / Checkboxes */
  li input[type="checkbox"] {
    margin-right: 6px;
    vertical-align: middle;
    width: 12px;
    height: 12px;
  }
  
  /* Figures and Images (like Mermaid SVGs) */
  figure {
    text-align: center;
    margin: 25px 0;
    page-break-inside: avoid;
  }
  
  img {
    max-width: 95%;
    height: auto;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04);
    padding: 12px;
    background-color: #FFFFFF;
  }
  
  figcaption {
    font-size: 8.5pt;
    color: #718096;
    margin-top: 8px;
    font-style: italic;
  }
  
  /* Blockquotes / Callouts */
  blockquote {
    border-left: 4px solid ${accentThemeColor};
    background-color: #EBF8FF;
    margin: 15px 0;
    padding: 12px 18px;
    border-radius: 0 6px 6px 0;
  }
  
  blockquote p {
    margin-bottom: 0;
    color: #2B6CB0;
  }
---

`;
    compiledContent = frontMatter + compiledContent;
  }

  fs.writeFileSync(tempCompiledPath, compiledContent, 'utf8');

  // Step 3: Compile to PDF via md-to-pdf
  console.log('🚀 Generating final PDF...');
  const mdToPdfCmd = `npx md-to-pdf "${tempCompiledPath}" --launch-options '{"args": ["--no-sandbox"]}'`;
  execSync(mdToPdfCmd, { cwd: tempDir, stdio: 'inherit' });

  // Step 4: Move compiled PDF to target location
  const generatedPdfName = 'temp_compiled.pdf';
  const generatedPdfPath = path.join(tempDir, generatedPdfName);

  if (fs.existsSync(generatedPdfPath)) {
    fs.copyFileSync(generatedPdfPath, outputPath);
    console.log(`\n✨ Success! Compiled PDF saved to: ${outputPath}`);
  } else {
    throw new Error('PDF file was not created by the generator.');
  }

} catch (err) {
  console.error('\n❌ Compilation failed:', err.message || err);
} finally {
  // Clean up temporary workspace directory
  try {
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  } catch (e) {
    // Ignore cleanup errors
  }
}
