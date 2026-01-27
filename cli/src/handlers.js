/**
 * CV Builder - Menu handlers
 */

import inquirer from 'inquirer';
import path from 'path';
import fs from 'fs';
import { createSpinner } from 'nanospinner';
import { theme, gradients, symbols } from './theme.js';
import { printLogo, printSection, printBox, printSuccess, printError, printInfo, printStep, createStatusTable } from './ui.js';
import { sleep, getCvFiles, getReadmeFiles, loadJson, getRootDir, findFiles } from './utils.js';
import { runPythonCommand } from './python-bridge.js';

export async function showMainMenu() {
  console.clear();
  printLogo();

  const choices = [
    { name: theme.primary('[Q] Quick Enhance') + theme.dim(' - One-click CV optimization'), value: 'quick' },
    { name: theme.primary('[C] Convert DOCX') + theme.dim(' - Extract CV to JSON'), value: 'convert' },
    { name: theme.primary('[F] Fetch GitHub') + theme.dim(' - Download project READMEs'), value: 'fetch' },
    { name: theme.primary('[O] Optimize') + theme.dim(' - Fit to page limit'), value: 'optimize' },
    { name: theme.primary('[T] AI Tailor') + theme.dim(' - Enhance with AI'), value: 'tailor' },
    { name: theme.primary('[E] Full Enhance') + theme.dim(' - Optimize + AI Tailor'), value: 'enhance' },
    { name: theme.primary('[B] Build DOCX') + theme.dim(' - Generate Word document'), value: 'build' },
    new inquirer.Separator(),
    { name: theme.secondary('[A] AI Chat') + theme.dim(' - Interactive chatbot'), value: 'chat' },
    { name: theme.secondary('[S] Settings') + theme.dim(' - View configuration'), value: 'config' },
    { name: theme.secondary('[?] Status') + theme.dim(' - Check workflow progress'), value: 'status' },
    { name: theme.accent('[X] Exit'), value: 'exit' },
  ];

  const { action } = await inquirer.prompt([
    {
      type: 'list',
      name: 'action',
      message: gradients.main('What would you like to do?'),
      choices,
      pageSize: 14,
    },
  ]);

  return action;
}

export async function selectCvFile() {
  const cvFiles = getCvFiles();
  
  if (cvFiles.length === 0) {
    printWarning('No CV JSON files found. Run "convert" first.');
    return null;
  }

  const choices = cvFiles.map(f => ({
    name: path.basename(f),
    value: f,
  }));

  const { file } = await inquirer.prompt([
    {
      type: 'list',
      name: 'file',
      message: theme.primary('Select CV file:'),
      choices,
    },
  ]);

  return file;
}

export async function selectReadmes() {
  const readmes = getReadmeFiles();
  
  if (readmes.length === 0) {
    printWarning('No README files found. Run "fetch" first.');
    return [];
  }

  // Show table first
  console.log('\n' + theme.primary('  Available READMEs:'));
  readmes.forEach((r, i) => {
    const size = `${(r.size / 1024).toFixed(1)} KB`;
    console.log(`  ${theme.secondary((i + 1) + '.')} ${r.name} ${theme.dim('(' + size + ')')}`);
  });
  console.log();

  // Use rawlist for individual selection (not checkbox)
  const { indices } = await inquirer.prompt([
    {
      type: 'input',
      name: 'indices',
      message: theme.primary('Enter numbers to select (e.g., 1,3,5) or "all":'),
      default: 'all',
    },
  ]);

  if (indices.toLowerCase() === 'all') {
    return readmes.map(r => r.file);
  }
  
  if (indices.toLowerCase() === 'none' || indices.trim() === '') {
    return [];
  }

  const selected = [];
  indices.split(',').forEach(part => {
    const num = parseInt(part.trim());
    if (!isNaN(num) && num > 0 && num <= readmes.length) {
      selected.push(readmes[num - 1].file);
    }
  });

  return selected;
}

export async function handleConvert() {
  printSection('CONVERT DOCX TO JSON', '>');

  const docxFiles = findFiles(/\.docx$/);
  
  if (docxFiles.length === 0) {
    printError('No DOCX files found in the workspace.');
    return;
  }

  const { file } = await inquirer.prompt([
    {
      type: 'list',
      name: 'file',
      message: theme.primary('Select DOCX file:'),
      choices: docxFiles.map(f => ({ name: path.basename(f), value: f })),
    },
  ]);

  const { output } = await inquirer.prompt([
    {
      type: 'input',
      name: 'output',
      message: theme.primary('Output JSON filename:'),
      default: path.basename(file, '.docx') + '.json',
    },
  ]);

  const spinner = createSpinner(theme.info('Converting DOCX to JSON...')).start();

  try {
    await runPythonCommand(['convert', file, '--output', output]);
    spinner.success({ text: theme.success(`Converted to ${output}`) });
  } catch (err) {
    spinner.error({ text: theme.error('Conversion failed') });
    console.log(theme.dim(err.message));
  }
}

export async function handleFetch() {
  printSection('FETCH GITHUB READMES', '>');

  const reposFile = path.join(getRootDir(), 'repos.txt');
  const defaultRepos = fs.existsSync(reposFile) 
    ? fs.readFileSync(reposFile, 'utf8')
    : '';

  const { repos } = await inquirer.prompt([
    {
      type: 'editor',
      name: 'repos',
      message: theme.primary('Enter GitHub repo URLs (one per line):'),
      default: defaultRepos,
    },
  ]);

  fs.writeFileSync(reposFile, repos);

  const spinner = createSpinner(theme.info('Fetching READMEs from GitHub...')).start();

  try {
    await runPythonCommand(['fetch', '--repos-file', 'repos.txt']);
    spinner.success({ text: theme.success('READMEs downloaded successfully') });
    
    const readmes = getReadmeFiles();
    printInfo(`Found ${readmes.length} README files`);
  } catch (err) {
    spinner.error({ text: theme.error('Fetch failed') });
    console.log(theme.dim(err.message));
  }
}

export async function handleOptimize() {
  printSection('OPTIMIZE FOR PAGE LIMIT', '>');

  const cvFile = await selectCvFile();
  if (!cvFile) return;

  const spinner = createSpinner(theme.info('Optimizing CV for page fit...')).start();

  try {
    const outputFile = path.basename(cvFile, '.json') + '_optimized.json';
    await runPythonCommand(['optimize', cvFile, '--output', outputFile]);
    spinner.success({ text: theme.success(`Optimized CV saved to ${outputFile}`) });
  } catch (err) {
    spinner.error({ text: theme.error('Optimization failed') });
    console.log(theme.dim(err.message));
  }
}

export async function handleTailor() {
  printSection('AI TAILORING', '>');

  const cvFile = await selectCvFile();
  if (!cvFile) return;

  const selectedReadmes = await selectReadmes();

  const { guidance } = await inquirer.prompt([
    {
      type: 'input',
      name: 'guidance',
      message: theme.primary('Custom AI guidance (optional):'),
      default: '',
    },
  ]);

  const spinner = createSpinner(theme.info('AI is tailoring your CV...')).start();

  try {
    const outputFile = path.basename(cvFile, '.json') + '_tailored.json';
    const args = ['tailor', cvFile, '--output', outputFile, '--readme-dir', '.readme_cache'];
    if (guidance) args.push('--guidance', guidance);
    
    await runPythonCommand(args);
    spinner.success({ text: theme.success(`Tailored CV saved to ${outputFile}`) });
  } catch (err) {
    spinner.error({ text: theme.error('AI tailoring failed') });
    console.log(theme.dim(err.message));
  }
}

export async function handleEnhance() {
  printSection('FULL CV ENHANCEMENT', '>');
  
  printBox(
    theme.white('This combines:\n') +
    theme.primary('  1. ') + 'Page optimization (fit to limit)\n' +
    theme.primary('  2. ') + 'AI tailoring (hiring-manager focus)\n' +
    theme.primary('  3. ') + 'GitHub integration (proof of work)',
    'INTELLIGENT ENHANCEMENT',
    'cyan'
  );

  const cvFile = await selectCvFile();
  if (!cvFile) return;

  const selectedReadmes = await selectReadmes();

  const { guidance } = await inquirer.prompt([
    {
      type: 'input',
      name: 'guidance',
      message: theme.primary('Custom AI guidance (optional):'),
      default: '',
    },
  ]);

  console.log();
  printStep(1, 3, 'Analyzing CV structure...');
  await sleep(500);
  
  printStep(2, 3, 'Optimizing for page fit...');
  
  const spinner = createSpinner(theme.info('AI is enhancing your CV...')).start();

  try {
    const outputFile = path.basename(cvFile, '.json') + '_enhanced.json';
    const args = ['enhance', cvFile, '--output', outputFile, '--readme-dir', '.readme_cache', '--skip-selection'];
    if (guidance) args.push('--guidance', guidance);
    
    await runPythonCommand(args);
    spinner.success({ text: theme.success(`Enhanced CV saved to ${outputFile}`) });
    
    const enhanced = loadJson(path.join(getRootDir(), outputFile));
    if (enhanced) {
      printBox(
        theme.primary('Name: ') + (enhanced.name || 'N/A') + '\n' +
        theme.primary('Title: ') + (enhanced.title || 'N/A') + '\n' +
        theme.primary('Summary: ') + (enhanced.summary?.length || 0) + ' bullet points\n' +
        theme.primary('Experience: ') + (enhanced.experience?.length || 0) + ' roles\n' +
        theme.primary('Projects: ') + (enhanced.projects?.length || 0) + ' projects',
        'ENHANCEMENT SUMMARY',
        'green'
      );
    }
  } catch (err) {
    spinner.error({ text: theme.error('Enhancement failed') });
    console.log(theme.dim(err.message));
  }
}

export async function handleBuild() {
  printSection('BUILD DOCX', '>');

  const cvFile = await selectCvFile();
  if (!cvFile) return;

  const { output } = await inquirer.prompt([
    {
      type: 'input',
      name: 'output',
      message: theme.primary('Output DOCX filename:'),
      default: path.basename(cvFile, '.json') + '.docx',
    },
  ]);

  const spinner = createSpinner(theme.info('Generating professional DOCX...')).start();

  try {
    await runPythonCommand(['build', cvFile, '--output', output]);
    spinner.success({ text: theme.success(`DOCX generated: ${output}`) });
    
    printBox(
      theme.success('[OK] ') + 'Professional formatting applied\n' +
      theme.success('[OK] ') + 'A4 page with 0.25" margins\n' +
      theme.success('[OK] ') + 'ATS-friendly structure\n' +
      theme.success('[OK] ') + 'Ready for submission!',
      'DOCUMENT READY',
      'green'
    );
  } catch (err) {
    spinner.error({ text: theme.error('Build failed') });
    console.log(theme.dim(err.message));
  }
}

export async function handleQuick() {
  printSection('QUICK ENHANCE WORKFLOW', '>');
  
  console.log(theme.primary('\n  >>> One-click CV enhancement pipeline <<<\n'));

  const cvFile = await selectCvFile();
  if (!cvFile) return;

  const readmes = getReadmeFiles();
  
  console.log();
  printStep(1, 4, 'Loading CV...');
  await sleep(300);
  
  printStep(2, 4, `Using ${readmes.length} GitHub READMEs...`);
  await sleep(300);
  
  printStep(3, 4, 'Running AI enhancement...');
  
  const spinner = createSpinner(gradients.main('Enhancing your CV...')).start();

  try {
    const baseName = path.basename(cvFile, '.json');
    const enhancedFile = `${baseName}_enhanced.json`;
    const docxFile = `${baseName}_final.docx`;
    
    await runPythonCommand([
      'enhance', cvFile, 
      '--output', enhancedFile, 
      '--readme-dir', '.readme_cache',
      '--skip-selection'
    ]);
    
    spinner.update({ text: theme.info('Building DOCX...') });
    
    await runPythonCommand(['build', enhancedFile, '--output', docxFile]);
    
    spinner.success({ text: theme.success('CV enhanced and built!') });
    
    printBox(
      theme.primary('Enhanced JSON: ') + enhancedFile + '\n' +
      theme.primary('Final DOCX: ') + docxFile + '\n\n' +
      gradients.main('>>> Your CV is ready to impress! <<<'),
      'WORKFLOW COMPLETE',
      'green'
    );
  } catch (err) {
    spinner.error({ text: theme.error('Quick workflow failed') });
    console.log(theme.dim(err.message));
  }
}

export async function handleConfig() {
  printSection('CONFIGURATION', '>');

  try {
    const { stdout } = await runPythonCommand(['config']);
    console.log(theme.dim(stdout));
  } catch (err) {
    printError('Could not load config');
  }
}

export async function handleStatus() {
  printSection('WORKFLOW STATUS', '>');

  const docxFiles = findFiles(/\.docx$/);
  const cvFiles = getCvFiles();
  const readmes = getReadmeFiles();
  const configExists = fs.existsSync(path.join(getRootDir(), 'my_config.md'));
  const envExists = fs.existsSync(path.join(getRootDir(), '.env'));

  const data = [
    ['DOCX Files', docxFiles.length > 0, `${docxFiles.length} file(s)`],
    ['CV JSON Files', cvFiles.length > 0, `${cvFiles.length} file(s)`],
    ['GitHub READMEs', readmes.length > 0, `${readmes.length} file(s)`],
    ['Configuration', configExists, configExists ? 'my_config.md' : 'Using defaults'],
    ['Environment', envExists, envExists ? '.env loaded' : 'Missing .env file'],
  ];

  console.log('\n' + createStatusTable(data));
}
