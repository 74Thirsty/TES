import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { config } from './config.js';

const initialState = () => ({ tasks: [], events: [] });

let state = initialState();
let initialised = false;

function useMemory () {
  return config.dataFile === ':memory:';
}

async function ensureDirectory () {
  if (useMemory() || !config.dataDirectory) return;
  await mkdir(config.dataDirectory, { recursive: true });
}

async function persist () {
  if (useMemory()) return;
  await ensureDirectory();
  await writeFile(config.dataFile, JSON.stringify(state, null, 2), 'utf8');
}

export async function initStorage () {
  if (initialised) return;
  initialised = true;

  if (useMemory()) {
    state = initialState();
    return;
  }

  try {
    const contents = await readFile(config.dataFile, 'utf8');
    const parsed = JSON.parse(contents);
    state = {
      tasks: Array.isArray(parsed.tasks) ? parsed.tasks : [],
      events: Array.isArray(parsed.events) ? parsed.events : []
    };
  } catch (error) {
    if (error.code === 'ENOENT') {
      state = initialState();
      await persist();
    } else {
      throw error;
    }
  }
}

export function getState () {
  return state;
}

export async function saveState () {
  await persist();
}

export async function resetState () {
  state = initialState();
  await persist();
}

export function invalidateStorage () {
  initialised = false;
  state = initialState();
}
