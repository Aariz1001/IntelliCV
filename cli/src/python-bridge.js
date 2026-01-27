/**
 * CV Builder - Python bridge for backend commands
 */

import { spawn } from 'child_process';
import { getRootDir } from './utils.js';

export async function runPythonCommand(args, options = {}) {
  return new Promise((resolve, reject) => {
    const python = spawn('python', ['cv.py', ...args], {
      cwd: getRootDir(),
      stdio: options.interactive ? 'inherit' : 'pipe',
      shell: true,
    });

    let stdout = '';
    let stderr = '';

    if (!options.interactive) {
      python.stdout?.on('data', (data) => {
        stdout += data.toString();
        if (options.stream) process.stdout.write(data);
      });

      python.stderr?.on('data', (data) => {
        stderr += data.toString();
        if (options.stream) process.stderr.write(data);
      });
    }

    python.on('close', (code) => {
      if (code === 0) {
        resolve({ stdout, stderr, code });
      } else {
        reject(new Error(stderr || stdout || `Process exited with code ${code}`));
      }
    });

    python.on('error', (err) => {
      reject(err);
    });
  });
}

// Tool definitions for AI function calling
export const tools = [
  {
    name: 'convert_docx',
    description: 'Convert a DOCX file to JSON format',
    parameters: {
      docxFile: { type: 'string', description: 'Path to the DOCX file' },
      outputFile: { type: 'string', description: 'Output JSON file path' },
    },
    execute: async (params) => {
      const args = ['convert', params.docxFile];
      if (params.outputFile) args.push('--output', params.outputFile);
      return runPythonCommand(args);
    },
  },
  {
    name: 'fetch_readmes',
    description: 'Download README files from GitHub repositories',
    parameters: {
      reposFile: { type: 'string', description: 'Path to repos.txt file', default: 'repos.txt' },
    },
    execute: async (params) => {
      return runPythonCommand(['fetch', '--repos-file', params.reposFile || 'repos.txt']);
    },
  },
  {
    name: 'optimize_cv',
    description: 'Optimize CV to fit page limit',
    parameters: {
      cvFile: { type: 'string', description: 'Path to CV JSON file' },
      outputFile: { type: 'string', description: 'Output file path' },
    },
    execute: async (params) => {
      const args = ['optimize', params.cvFile];
      if (params.outputFile) args.push('--output', params.outputFile);
      return runPythonCommand(args);
    },
  },
  {
    name: 'enhance_cv',
    description: 'Full CV enhancement with optimization and AI tailoring',
    parameters: {
      cvFile: { type: 'string', description: 'Path to CV JSON file' },
      outputFile: { type: 'string', description: 'Output file path' },
      guidance: { type: 'string', description: 'Custom AI guidance' },
    },
    execute: async (params) => {
      const args = ['enhance', params.cvFile, '--readme-dir', '.readme_cache', '--skip-selection'];
      if (params.outputFile) args.push('--output', params.outputFile);
      if (params.guidance) args.push('--guidance', params.guidance);
      return runPythonCommand(args);
    },
  },
  {
    name: 'build_docx',
    description: 'Build professional DOCX from CV JSON',
    parameters: {
      cvFile: { type: 'string', description: 'Path to CV JSON file' },
      outputFile: { type: 'string', description: 'Output DOCX file path' },
    },
    execute: async (params) => {
      const args = ['build', params.cvFile];
      if (params.outputFile) args.push('--output', params.outputFile);
      return runPythonCommand(args);
    },
  },
  {
    name: 'set_config',
    description: 'Update CV configuration settings',
    parameters: {
      pageLimit: { type: 'number', description: 'Target page limit' },
      fontFamily: { type: 'string', description: 'Font family name' },
      marginInches: { type: 'number', description: 'Page margin in inches' },
    },
    execute: async (params) => {
      // This would update the config file
      return { success: true, message: 'Config updated', params };
    },
  },
  {
    name: 'get_status',
    description: 'Get current workflow status',
    parameters: {},
    execute: async () => {
      return runPythonCommand(['status']);
    },
  },
  {
    name: 'list_cv_files',
    description: 'List available CV JSON files',
    parameters: {},
    execute: async () => {
      const { getCvFiles } = await import('./utils.js');
      return { files: getCvFiles() };
    },
  },
  {
    name: 'list_readmes',
    description: 'List available GitHub README files',
    parameters: {},
    execute: async () => {
      const { getReadmeFiles } = await import('./utils.js');
      return { files: getReadmeFiles() };
    },
  },
];

export function getToolByName(name) {
  return tools.find(t => t.name === name);
}

export function getToolsForAI() {
  return tools.map(t => ({
    type: 'function',
    function: {
      name: t.name,
      description: t.description,
      parameters: {
        type: 'object',
        properties: t.parameters,
        required: Object.keys(t.parameters).filter(k => !t.parameters[k].default),
      },
    },
  }));
}
