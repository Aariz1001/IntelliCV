/**
 * CV Builder - UI components (ASCII-only, no emojis)
 */

import figlet from 'figlet';
import boxen from 'boxen';
import Table from 'cli-table3';
import { theme, gradients, symbols } from './theme.js';

export function printLogo() {
  const logo = figlet.textSync('CV Builder', {
    font: 'ANSI Shadow',
    horizontalLayout: 'fitted',
  });
  console.log(gradients.main(logo));
  console.log(gradients.ocean('  +' + '='.repeat(58) + '+'));
  console.log(gradients.ocean('  |') + theme.white('  AI-Powered * GitHub Integration * Hiring-Manager Focus  ') + gradients.ocean('|'));
  console.log(gradients.ocean('  +' + '='.repeat(58) + '+'));
  console.log();
}

export function printMiniLogo() {
  console.log(gradients.main('\n  CV BUILDER - AI Resume Optimization\n'));
}

export function printSection(title, icon = '>') {
  const line = '='.repeat(60);
  console.log('\n' + gradients.main(`  ${icon} ${title}`));
  console.log(theme.dim(`  ${line}`));
}

export function printBox(content, title = '', borderColor = 'green') {
  const box = boxen(content, {
    padding: 1,
    margin: { top: 1, bottom: 1, left: 2, right: 2 },
    borderStyle: 'round',
    borderColor: borderColor,
    title: title,
    titleAlignment: 'center',
  });
  console.log(box);
}

export function printSuccess(msg) {
  console.log(theme.success(`  ${symbols.success} ${msg}`));
}

export function printError(msg) {
  console.log(theme.error(`  ${symbols.error} ${msg}`));
}

export function printWarning(msg) {
  console.log(theme.warning(`  ${symbols.warning} ${msg}`));
}

export function printInfo(msg) {
  console.log(theme.info(`  ${symbols.info} ${msg}`));
}

export function printStep(step, total, msg) {
  const progress = theme.dim(`[${step}/${total}]`);
  console.log(`  ${progress} ${theme.primary(msg)}`);
}

export function createTable(headers, rows, options = {}) {
  const table = new Table({
    head: headers.map(h => theme.primary(h)),
    chars: {
      'top': '-', 'top-mid': '+', 'top-left': '+', 'top-right': '+',
      'bottom': '-', 'bottom-mid': '+', 'bottom-left': '+', 'bottom-right': '+',
      'left': '|', 'left-mid': '+', 'mid': '-', 'mid-mid': '+',
      'right': '|', 'right-mid': '+', 'middle': '|'
    },
    style: { head: [], border: ['green'] },
    ...options,
  });
  
  rows.forEach(row => table.push(row));
  return table.toString();
}

export function createStatusTable(data) {
  const rows = data.map(([component, status, details]) => [
    component,
    status ? theme.success(symbols.success) : theme.warning(symbols.warning),
    theme.dim(details),
  ]);
  
  return createTable(['Component', 'Status', 'Details'], rows);
}
