/**
 * CV Builder - Theme and styling configuration
 * No emojis, ASCII-only, Windows-compatible
 */

import chalk from 'chalk';
import gradient from 'gradient-string';

// Color theme - Neon green + cyan
export const theme = {
  primary: chalk.hex('#00FF88'),
  secondary: chalk.hex('#00DDFF'),
  accent: chalk.hex('#FF6B6B'),
  success: chalk.hex('#00FF88'),
  warning: chalk.hex('#FFD93D'),
  error: chalk.hex('#FF6B6B'),
  info: chalk.hex('#6C5CE7'),
  dim: chalk.gray,
  bold: chalk.bold,
  white: chalk.white,
  muted: chalk.hex('#888888'),
};

// Gradient presets
export const gradients = {
  main: gradient(['#00FF88', '#00DDFF']),
  fire: gradient(['#FF6B6B', '#FFD93D']),
  ocean: gradient(['#6C5CE7', '#00DDFF']),
  matrix: gradient(['#00FF88', '#003300']),
  sunset: gradient(['#FF6B6B', '#6C5CE7']),
};

// ASCII symbols (no unicode)
export const symbols = {
  success: '[OK]',
  error: '[X]',
  warning: '[!]',
  info: '[i]',
  arrow: '->',
  bullet: '*',
  check: '+',
  cross: 'x',
  dot: '.',
  line: '-',
  doubleLine: '=',
};

// Box drawing (ASCII)
export const box = {
  topLeft: '+',
  topRight: '+',
  bottomLeft: '+',
  bottomRight: '+',
  horizontal: '-',
  vertical: '|',
};
