/**
 * CV Builder - AI Chat Interface
 * 
 * Chat-first UI with Copilot-style input and /command dropdown
 */

import readline from 'readline';
import figlet from 'figlet';
import boxen from 'boxen';
import { theme, gradients, symbols } from './theme.js';
import { loadJson, saveJson, getRootDir, loadEnv, getCvFiles, getReadmeFiles, fileExists, findFiles } from './utils.js';
import { tools, getToolByName, getToolsForAI, runPythonCommand } from './python-bridge.js';
import path from 'path';
import fs from 'fs';

// State
let chatHistory = [];
let currentCv = null;
let currentCvPath = null;
let rl = null;

// Persistence file for selected CV
const STATE_FILE = '.cv_builder_state.json';

function loadState() {
  const statePath = path.join(getRootDir(), STATE_FILE);
  if (fs.existsSync(statePath)) {
    try {
      return JSON.parse(fs.readFileSync(statePath, 'utf8'));
    } catch (e) {
      return {};
    }
  }
  return {};
}

function saveState(state) {
  const statePath = path.join(getRootDir(), STATE_FILE);
  fs.writeFileSync(statePath, JSON.stringify(state, null, 2));
}

// Command definitions
const commands = {
  help:     { desc: 'Show all commands', fn: showHelp },
  status:   { desc: 'Check workflow status', fn: cmdStatus },
  files:    { desc: 'List CV and README files', fn: cmdFiles },
  load:     { desc: 'Load CV file (e.g., /load 1)', fn: cmdLoad },
  select:   { desc: 'Select and persist target CV', fn: cmdSelect },
  convert:  { desc: 'Convert DOCX to JSON', fn: cmdConvert },
  fetch:    { desc: 'Fetch GitHub READMEs', fn: cmdFetch },
  optimize: { desc: 'Optimize CV for page limit', fn: cmdOptimize },
  enhance:  { desc: 'Full AI enhancement', fn: cmdEnhance },
  build:    { desc: 'Build DOCX from JSON', fn: cmdBuild },
  quick:    { desc: 'One-click: enhance + build', fn: cmdQuick },
  config:   { desc: 'View configuration', fn: cmdConfig },
  clear:    { desc: 'Clear chat history', fn: () => { chatHistory = []; log('Chat cleared.'); } },
  exit:     { desc: 'Exit', fn: () => process.exit(0) },
  quit:     { desc: 'Exit', fn: () => process.exit(0) },
};

// Logging helpers
function log(msg) { console.log(theme.dim('  ' + msg)); }
function logOk(msg) { console.log(theme.success('  [OK] ' + msg)); }
function logErr(msg) { console.log(theme.error('  [!] ' + msg)); }
function logInfo(msg) { console.log(theme.info('  [i] ' + msg)); }

// Show help - Copilot style horizontal list
function showHelp() {
  console.log();
  Object.entries(commands).forEach(([name, { desc }]) => {
    if (name !== 'quit') {
      console.log(`    ${theme.secondary('/' + name.padEnd(14))} ${theme.dim(desc)}`);
    }
  });
  console.log();
}

// Show command suggestions dropdown (Copilot style)
function showSuggestions(partial) {
  const matching = Object.entries(commands)
    .filter(([name]) => name.startsWith(partial) && name !== 'quit');
  
  if (matching.length === 0) return;
  
  // Draw a box around suggestions
  console.log(theme.dim('    +' + '-'.repeat(55) + '+'));
  matching.forEach(([name, { desc }]) => {
    const cmdText = theme.secondary('/' + name.padEnd(14));
    const descText = theme.dim(desc);
    console.log(theme.dim('    | ') + cmdText + ' ' + descText.padEnd(38) + theme.dim(' |'));
  });
  console.log(theme.dim('    +' + '-'.repeat(55) + '+'));
}

// Status command
async function cmdStatus() {
  const cvFiles = getCvFiles();
  const readmes = getReadmeFiles();
  const configPath = path.join(getRootDir(), 'my_config.md');
  const envPath = path.join(getRootDir(), '.env');
  
  console.log('\n' + theme.primary('  WORKFLOW STATUS:'));
  console.log(`  ${cvFiles.length > 0 ? symbols.success : symbols.warning} CV Files: ${cvFiles.length}`);
  console.log(`  ${readmes.length > 0 ? symbols.success : symbols.warning} READMEs: ${readmes.length}`);
  console.log(`  ${fs.existsSync(configPath) ? symbols.success : symbols.warning} Config: ${fs.existsSync(configPath) ? 'OK' : 'Using defaults'}`);
  console.log(`  ${fs.existsSync(envPath) ? symbols.success : symbols.error} API Key: ${fs.existsSync(envPath) ? 'Configured' : 'Missing .env'}`);
  if (currentCvPath) {
    console.log(`  ${symbols.info} Loaded: ${path.basename(currentCvPath)}`);
  }
  console.log();
}

// Files command
async function cmdFiles() {
  const cvFiles = getCvFiles();
  const readmes = getReadmeFiles();
  
  console.log('\n' + theme.primary('  CV FILES:'));
  if (cvFiles.length === 0) {
    console.log(theme.dim('    No JSON CVs found. Use /convert first.'));
  } else {
    cvFiles.forEach((f, i) => {
      const loaded = f === currentCvPath ? theme.success(' [loaded]') : '';
      console.log(`    ${theme.secondary((i + 1) + '.')} ${path.basename(f)}${loaded}`);
    });
  }
  
  console.log('\n' + theme.primary('  README FILES:'));
  if (readmes.length === 0) {
    console.log(theme.dim('    No READMEs found. Use /fetch first.'));
  } else {
    readmes.forEach((r, i) => {
      console.log(`    ${theme.secondary((i + 1) + '.')} ${r.name}`);
    });
  }
  console.log();
}

// Load command
async function cmdLoad(args) {
  const cvFiles = getCvFiles();
  if (cvFiles.length === 0) {
    logErr('No CV files found. Use /convert first.');
    return;
  }
  
  if (!args || args.trim() === '') {
    logInfo('Usage: /load <number>');
    await cmdFiles();
    return;
  }
  
  const num = parseInt(args.trim());
  if (isNaN(num) || num < 1 || num > cvFiles.length) {
    logErr(`Invalid. Enter 1-${cvFiles.length}`);
    return;
  }
  
  currentCvPath = cvFiles[num - 1];
  currentCv = loadJson(currentCvPath);
  logOk(`Loaded: ${path.basename(currentCvPath)}`);
  log(`Name: ${currentCv?.name || 'N/A'}`);
  log(`Title: ${currentCv?.title || 'N/A'}`);
}

// Select command - persist CV choice
async function cmdSelect() {
  const cvFiles = getCvFiles();
  const docxFiles = findFiles(/\.docx$/);
  const allFiles = [...cvFiles, ...docxFiles];
  
  if (allFiles.length === 0) {
    logErr('No CV files found. Use /convert to create one from DOCX.');
    return;
  }
  
  console.log('\n' + theme.primary('  SELECT TARGET CV:'));
  console.log(theme.dim('  JSON files (for enhance/build):'));
  cvFiles.forEach((f, i) => {
    const selected = f === currentCvPath ? theme.success(' [selected]') : '';
    console.log(`    ${theme.secondary((i + 1) + '.')} ${path.basename(f)}${selected}`);
  });
  
  if (docxFiles.length > 0) {
    console.log(theme.dim('\n  DOCX files (source):'));
    docxFiles.forEach((f, i) => {
      console.log(`    ${theme.secondary((cvFiles.length + i + 1) + '.')} ${path.basename(f)}`);
    });
  }
  
  console.log();
  const answer = await promptInput('Select number (or Enter to cancel): ');
  
  if (!answer) return;
  
  const num = parseInt(answer);
  if (isNaN(num) || num < 1 || num > allFiles.length) {
    logErr(`Invalid. Enter 1-${allFiles.length}`);
    return;
  }
  
  const selectedFile = allFiles[num - 1];
  
  // If DOCX selected, offer to convert first
  if (selectedFile.endsWith('.docx')) {
    log('DOCX selected. Converting to JSON first...');
    try {
      const output = path.basename(selectedFile, '.docx') + '.json';
      await runPythonCommand(['convert', selectedFile, '--output', output]);
      currentCvPath = path.join(getRootDir(), output);
      currentCv = loadJson(currentCvPath);
      logOk(`Converted and loaded: ${output}`);
    } catch (err) {
      logErr(err.message);
      return;
    }
  } else {
    currentCvPath = selectedFile;
    currentCv = loadJson(currentCvPath);
    logOk(`Selected: ${path.basename(currentCvPath)}`);
  }
  
  // Persist selection
  const state = loadState();
  state.selectedCv = currentCvPath;
  saveState(state);
  log('Selection persisted for future sessions.');
  log(`Name: ${currentCv?.name || 'N/A'}`);
  log(`Title: ${currentCv?.title || 'N/A'}`);
}

// Convert command
async function cmdConvert() {
  const docxFiles = findFiles(/\.docx$/);
  
  if (docxFiles.length === 0) {
    logErr('No DOCX files found in workspace.');
    return;
  }
  
  console.log('\n' + theme.primary('  DOCX FILES:'));
  docxFiles.forEach((f, i) => {
    console.log(`    ${theme.secondary((i + 1) + '.')} ${path.basename(f)}`);
  });
  
  const answer = await promptInput('Select number: ');
  const num = parseInt(answer);
  
  if (isNaN(num) || num < 1 || num > docxFiles.length) {
    logErr('Invalid selection.');
    return;
  }
  
  const file = docxFiles[num - 1];
  const output = path.basename(file, '.docx') + '.json';
  
  log('Converting...');
  try {
    await runPythonCommand(['convert', file, '--output', output]);
    logOk(`Created: ${output}`);
  } catch (err) {
    logErr(err.message);
  }
}

// Fetch command
async function cmdFetch() {
  log('Fetching GitHub READMEs...');
  try {
    await runPythonCommand(['fetch', '--repos-file', 'repos.txt']);
    const readmes = getReadmeFiles();
    logOk(`Downloaded ${readmes.length} README(s)`);
  } catch (err) {
    logErr(err.message);
  }
}

// Optimize command
async function cmdOptimize() {
  if (!currentCvPath) {
    logErr('No CV loaded. Use /load or /files first.');
    return;
  }
  
  log('Optimizing for page fit...');
  try {
    const output = path.basename(currentCvPath, '.json') + '_optimized.json';
    await runPythonCommand(['optimize', currentCvPath, '--output', output]);
    logOk(`Saved: ${output}`);
  } catch (err) {
    logErr(err.message);
  }
}

// Enhance command
async function cmdEnhance() {
  if (!currentCvPath) {
    logErr('No CV loaded. Use /load or /files first.');
    return;
  }
  
  log('Running AI enhancement (this may take a minute)...');
  try {
    const output = path.basename(currentCvPath, '.json') + '_enhanced.json';
    await runPythonCommand(['enhance', currentCvPath, '--output', output, '--readme-dir', '.readme_cache', '--skip-selection']);
    logOk(`Saved: ${output}`);
    
    // Auto-load enhanced version
    const enhancedPath = path.join(getRootDir(), output);
    if (fs.existsSync(enhancedPath)) {
      currentCvPath = enhancedPath;
      currentCv = loadJson(currentCvPath);
      log(`Auto-loaded: ${output}`);
    }
  } catch (err) {
    logErr(err.message);
  }
}

// Build command
async function cmdBuild() {
  if (!currentCvPath) {
    logErr('No CV loaded. Use /load first.');
    return;
  }
  
  log('Building DOCX...');
  try {
    const output = path.basename(currentCvPath, '.json') + '.docx';
    await runPythonCommand(['build', currentCvPath, '--output', output]);
    logOk(`Created: ${output}`);
  } catch (err) {
    logErr(err.message);
  }
}

// Quick command (one-click)
async function cmdQuick() {
  if (!currentCvPath) {
    logErr('No CV loaded. Use /load first.');
    return;
  }
  
  log('Running quick workflow...');
  
  try {
    const baseName = path.basename(currentCvPath, '.json');
    const enhanced = baseName + '_enhanced.json';
    const docx = baseName + '_final.docx';
    
    log('[1/2] Enhancing CV...');
    await runPythonCommand(['enhance', currentCvPath, '--output', enhanced, '--readme-dir', '.readme_cache', '--skip-selection']);
    
    log('[2/2] Building DOCX...');
    await runPythonCommand(['build', enhanced, '--output', docx]);
    
    logOk('Done! Files created:');
    log(`  - ${enhanced}`);
    log(`  - ${docx}`);
  } catch (err) {
    logErr(err.message);
  }
}

// Config command
async function cmdConfig() {
  const configPath = path.join(getRootDir(), 'my_config.md');
  if (fs.existsSync(configPath)) {
    const content = fs.readFileSync(configPath, 'utf8');
    console.log('\n' + theme.primary('  CONFIGURATION:'));
    console.log(theme.dim(content.substring(0, 800)));
  } else {
    logInfo('No config file found. Using defaults.');
    log('Create my_config.md to customize (see cv_config.example.md)');
  }
}

// Prompt helper for input within chat
function promptInput(question) {
  return new Promise(resolve => {
    rl.question(theme.secondary('  ' + question), answer => {
      resolve(answer.trim());
    });
  });
}

// AI Chat function
async function chatWithAI(userMessage) {
  loadEnv();
  
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    logErr('OPENROUTER_API_KEY not found in .env file');
    return null;
  }
  
  // Build context-aware system prompt
  const systemPrompt = `You are CV Builder AI, an expert resume optimization assistant.

Current state:
- Loaded CV: ${currentCvPath ? path.basename(currentCvPath) : 'None'}
${currentCv ? `- Name: ${currentCv.name}\n- Title: ${currentCv.title}` : ''}

Available tools:
${tools.map(t => `- ${t.name}: ${t.description}`).join('\n')}

Guidelines:
1. Be concise and helpful (max 100 words unless detail needed)
2. When user wants an action, use the appropriate tool
3. Guide users through CV optimization workflow
4. Reference the loaded CV data when relevant
5. Suggest next steps after completing actions
6. For simple questions, answer directly without tools`;

  const messages = [
    { role: 'system', content: systemPrompt },
    ...chatHistory.slice(-8),
    { role: 'user', content: userMessage },
  ];
  
  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: process.env.OPENROUTER_MODEL || 'anthropic/claude-sonnet-4',
        messages,
        tools: getToolsForAI(),
        tool_choice: 'auto',
      }),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    const choice = data.choices[0];
    
    // Handle tool calls
    if (choice.message.tool_calls) {
      for (const toolCall of choice.message.tool_calls) {
        const tool = getToolByName(toolCall.function.name);
        if (tool) {
          log(`Running: ${tool.name}...`);
          try {
            const params = JSON.parse(toolCall.function.arguments || '{}');
            const result = await tool.execute(params);
            logOk('Completed');
            if (result.stdout) {
              const preview = result.stdout.substring(0, 250).trim();
              if (preview) console.log(theme.dim('  ' + preview.split('\n')[0]));
            }
          } catch (err) {
            logErr(err.message);
          }
        }
      }
    }
    
    return choice.message.content;
  } catch (err) {
    logErr(`AI error: ${err.message}`);
    return null;
  }
}

// Main chat interface
export async function startChat() {
  loadEnv();
  console.clear();
  
  // Beautiful 3D gradient header
  const logo = figlet.textSync('CV Builder', {
    font: 'ANSI Shadow',
    horizontalLayout: 'fitted',
  });
  console.log(gradients.main(logo));
  
  // Styled header box
  const headerContent = theme.white('AI-Powered') + theme.dim(' | ') + 
                        theme.white('GitHub Integration') + theme.dim(' | ') + 
                        theme.white('Hiring-Manager Focus');
  console.log(boxen(headerContent, {
    padding: { top: 0, bottom: 0, left: 2, right: 2 },
    margin: { top: 0, bottom: 1, left: 2, right: 2 },
    borderStyle: 'round',
    borderColor: 'cyan',
  }));
  
  // Instructions
  console.log(theme.dim('  Describe a task to get started.') + theme.dim(' | ') + 
              theme.white('CV Builder uses AI, so always check for mistakes.'));
  console.log();
  console.log(theme.dim('  Type ') + theme.secondary('/') + theme.dim(' or ') + 
              theme.secondary('?') + theme.dim(' to see all commands.'));
  console.log();
  
  // Load persisted CV selection, or auto-load first CV
  const state = loadState();
  const cvFiles = getCvFiles();
  
  if (state.selectedCv && fs.existsSync(state.selectedCv)) {
    currentCvPath = state.selectedCv;
    currentCv = loadJson(currentCvPath);
    console.log(theme.dim('  * Loaded CV: ') + theme.success(path.basename(currentCvPath)) + theme.dim(' (persisted)'));
  } else if (cvFiles.length > 0) {
    currentCvPath = cvFiles[0];
    currentCv = loadJson(currentCvPath);
    console.log(theme.dim('  * Loaded CV: ') + theme.success(path.basename(cvFiles[0])));
  } else {
    console.log(theme.dim('  * No CV loaded. Use /convert or /select to load one.'));
  }
  console.log();
  
  // Create readline with autocomplete
  rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    completer: (line) => {
      if (line.startsWith('/')) {
        const partial = line.slice(1);
        const hits = Object.keys(commands)
          .filter(c => c.startsWith(partial) && c !== 'quit')
          .map(c => '/' + c);
        return [hits.length ? hits : Object.keys(commands).map(c => '/' + c), line];
      }
      return [[], line];
    },
  });
  
  // Track current input for live command display
  let currentLine = '';
  let commandsShown = false;
  
  // Listen for keypress to show commands immediately on /
  process.stdin.on('keypress', (char, key) => {
    if (!key) return;
    
    // Get current line from readline
    const line = rl.line || '';
    
    // If line is exactly "/" and we haven't shown commands yet
    if (line === '/' && !commandsShown) {
      commandsShown = true;
      // Move cursor down and show commands
      console.log(); // New line after >
      showSuggestions('');
      // Redraw prompt with current input
      process.stdout.write(theme.secondary('> ') + '/');
    } else if (!line.startsWith('/')) {
      commandsShown = false;
    }
  });
  
  // Enable keypress events
  if (process.stdin.isTTY) {
    readline.emitKeypressEvents(process.stdin, rl);
  }
  
  // Main prompt loop
  const promptUser = () => {
    commandsShown = false;
    rl.question(theme.secondary('> '), async (input) => {
      const trimmed = input.trim();
      
      if (!trimmed) {
        promptUser();
        return;
      }
      
      // Show help on ? or /help
      if (trimmed === '?' || trimmed === '/help' || trimmed === 'help') {
        showHelp();
        promptUser();
        return;
      }
      
      // If user just typed "/" show all commands
      if (trimmed === '/') {
        // Commands already shown via keypress, just re-prompt
        promptUser();
        return;
      }
      
      // Handle slash commands
      if (trimmed.startsWith('/')) {
        const parts = trimmed.slice(1).split(' ');
        const cmdName = parts[0].toLowerCase();
        const args = parts.slice(1).join(' ');
        
        if (commands[cmdName]) {
          await commands[cmdName].fn(args);
        } else {
          logErr(`Unknown command: /${cmdName}`);
          showSuggestions(cmdName);
        }
        
        promptUser();
        return;
      }
      
      // AI chat
      chatHistory.push({ role: 'user', content: trimmed });
      
      process.stdout.write(theme.dim('  Thinking...'));
      const response = await chatWithAI(trimmed);
      process.stdout.write('\r               \r');
      
      if (response) {
        console.log('\n' + theme.primary('  AI: ') + theme.white(response) + '\n');
        chatHistory.push({ role: 'assistant', content: response });
      }
      
      promptUser();
    });
  };
  
  promptUser();
}
