#!/usr/bin/env node

/**
 * CV Builder CLI
 * 
 * AI-powered CV optimization with GitHub integration,
 * interactive chatbot, and hiring-manager focused content.
 * 
 * Usage:
 *   cv-builder          - Launch interactive menu
 *   cv-builder chat     - Start AI chatbot
 *   cv-builder <cmd>    - Run specific command
 */

import { Command } from 'commander';
import inquirer from 'inquirer';
import { createSpinner } from 'nanospinner';
import path from 'path';

import { theme, gradients } from './theme.js';
import { printLogo, printMiniLogo, printSuccess, printError } from './ui.js';
import { loadEnv, getRootDir } from './utils.js';
import { runPythonCommand } from './python-bridge.js';
import { startChat } from './chatbot.js';
import {
  showMainMenu,
  handleConvert,
  handleFetch,
  handleOptimize,
  handleTailor,
  handleEnhance,
  handleBuild,
  handleQuick,
  handleConfig,
  handleStatus,
} from './handlers.js';

// Load environment
loadEnv();

const program = new Command();

program
  .name('cv-builder')
  .description('AI-powered CV Builder with GitHub Integration')
  .version('2.0.0');

// Interactive menu (default)
program
  .command('menu')
  .description('Open interactive menu')
  .action(async () => {
    await runInteractiveMenu();
  });

// AI Chat
program
  .command('chat')
  .description('Start AI chatbot interface')
  .action(async () => {
    await startChat();
  });

// Direct commands
program
  .command('convert <docx>')
  .description('Convert DOCX to JSON')
  .option('-o, --output <file>', 'Output JSON file')
  .action(async (docx, options) => {
    printMiniLogo();
    const spinner = createSpinner(theme.info('Converting...')).start();
    try {
      const args = ['convert', docx];
      if (options.output) args.push('--output', options.output);
      await runPythonCommand(args);
      spinner.success({ text: theme.success('Converted successfully') });
    } catch (err) {
      spinner.error({ text: theme.error(err.message) });
    }
  });

program
  .command('fetch')
  .description('Fetch GitHub READMEs')
  .option('-f, --file <repos>', 'Repos file', 'repos.txt')
  .action(async (options) => {
    printMiniLogo();
    const spinner = createSpinner(theme.info('Fetching READMEs...')).start();
    try {
      await runPythonCommand(['fetch', '--repos-file', options.file]);
      spinner.success({ text: theme.success('READMEs downloaded') });
    } catch (err) {
      spinner.error({ text: theme.error(err.message) });
    }
  });

program
  .command('enhance <cv>')
  .description('Full CV enhancement (optimize + AI tailor)')
  .option('-o, --output <file>', 'Output JSON file')
  .option('-g, --guidance <text>', 'Custom AI guidance')
  .option('--readme-dir <dir>', 'README directory', '.readme_cache')
  .action(async (cv, options) => {
    printMiniLogo();
    const spinner = createSpinner(gradients.main('Enhancing CV...')).start();
    try {
      const args = ['enhance', cv, '--readme-dir', options.readmeDir, '--skip-selection'];
      if (options.output) args.push('--output', options.output);
      if (options.guidance) args.push('--guidance', options.guidance);
      await runPythonCommand(args);
      spinner.success({ text: theme.success('Enhanced successfully') });
    } catch (err) {
      spinner.error({ text: theme.error(err.message) });
    }
  });

program
  .command('build <cv>')
  .description('Build DOCX from JSON')
  .option('-o, --output <file>', 'Output DOCX file')
  .action(async (cv, options) => {
    printMiniLogo();
    const spinner = createSpinner(theme.info('Building DOCX...')).start();
    try {
      const args = ['build', cv];
      if (options.output) args.push('--output', options.output);
      await runPythonCommand(args);
      spinner.success({ text: theme.success('Built successfully') });
    } catch (err) {
      spinner.error({ text: theme.error(err.message) });
    }
  });

program
  .command('status')
  .description('Check workflow status')
  .action(async () => {
    printMiniLogo();
    await handleStatus();
  });

// Interactive menu loop
async function runInteractiveMenu() {
  while (true) {
    const action = await showMainMenu();
    
    switch (action) {
      case 'quick': await handleQuick(); break;
      case 'convert': await handleConvert(); break;
      case 'fetch': await handleFetch(); break;
      case 'optimize': await handleOptimize(); break;
      case 'tailor': await handleTailor(); break;
      case 'enhance': await handleEnhance(); break;
      case 'build': await handleBuild(); break;
      case 'chat': await startChat(); break;
      case 'config': await handleConfig(); break;
      case 'status': await handleStatus(); break;
      case 'exit':
        console.log(gradients.main('\n  Thanks for using CV Builder! Good luck!\n'));
        process.exit(0);
    }
    
    await inquirer.prompt([
      {
        type: 'input',
        name: 'continue',
        message: theme.dim('Press Enter to continue...'),
      },
    ]);
  }
}

// Default to chat if no command (chat-first interface)
if (process.argv.length <= 2) {
  startChat();
} else {
  program.parse();
}
