#!/usr/bin/env node
// Find clicker binary from platform package and run `clicker mcp`

const { execFileSync } = require('child_process');
const path = require('path');
const os = require('os');

function getClickerPath() {
  const platform = os.platform();
  const arch = os.arch() === 'x64' ? 'x64' : 'arm64';
  const packageName = `@vibium/${platform}-${arch}`;
  const binaryName = platform === 'win32' ? 'clicker.exe' : 'clicker';

  try {
    const packagePath = require.resolve(`${packageName}/package.json`);
    return path.join(path.dirname(packagePath), 'bin', binaryName);
  } catch {
    console.error(`Could not find clicker binary for ${platform}-${arch}`);
    process.exit(1);
  }
}

const clickerPath = getClickerPath();
execFileSync(clickerPath, ['mcp'], { stdio: 'inherit' });
