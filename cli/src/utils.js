/**
 * CV Builder - Utility functions
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export function getRootDir() {
  // Go up from cli/src to the main project root
  return path.resolve(__dirname, '..', '..');
}

export function sleep(ms = 1000) {
  return new Promise(r => setTimeout(r, ms));
}

export function findFiles(pattern, dir = getRootDir()) {
  const files = [];
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isFile() && entry.name.match(pattern)) {
        files.push(path.join(dir, entry.name));
      }
    }
  } catch (e) {
    // Directory might not exist
  }
  return files;
}

export function loadJson(filepath) {
  try {
    return JSON.parse(fs.readFileSync(filepath, 'utf8'));
  } catch {
    return null;
  }
}

export function saveJson(filepath, data) {
  fs.writeFileSync(filepath, JSON.stringify(data, null, 2), 'utf8');
}

export function fileExists(filepath) {
  return fs.existsSync(filepath);
}

export function readFile(filepath) {
  try {
    return fs.readFileSync(filepath, 'utf8');
  } catch {
    return null;
  }
}

export function writeFile(filepath, content) {
  fs.writeFileSync(filepath, content, 'utf8');
}

export function getReadmeFiles(dir = '.readme_cache') {
  const readmeDir = path.join(getRootDir(), dir);
  if (!fs.existsSync(readmeDir)) return [];
  
  return fs.readdirSync(readmeDir)
    .filter(f => f.endsWith('.md'))
    .map(f => ({
      name: f.replace('__README.md', '').replace(/_/g, '/'),
      file: f,
      path: path.join(readmeDir, f),
      size: fs.statSync(path.join(readmeDir, f)).size,
    }));
}

export function getCvFiles() {
  const jsonFiles = findFiles(/\.json$/);
  return jsonFiles.filter(f => {
    const content = loadJson(f);
    return content && (content.name || content.experience || content.summary);
  });
}

export function getEnvVar(name) {
  return process.env[name] || null;
}

export function loadEnv() {
  const envPath = path.join(getRootDir(), '.env');
  if (fs.existsSync(envPath)) {
    const content = fs.readFileSync(envPath, 'utf8');
    content.split('\n').forEach(line => {
      const match = line.match(/^([^=]+)=(.*)$/);
      if (match) {
        process.env[match[1].trim()] = match[2].trim();
      }
    });
  }
}
