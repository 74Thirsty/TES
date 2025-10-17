import { randomUUID } from 'node:crypto';
import { getState, saveState } from '../storage.js';
import { TASK_STATUS_VALUES } from '../validators.js';

function cloneTask (task) {
  return structuredClone(task);
}

function ensureDefaults (payload) {
  return {
    description: '',
    status: 'pending',
    priority: 3,
    dueDate: null,
    estimatedMinutes: null,
    tags: [],
    ...payload
  };
}

export async function createTask (input) {
  const now = new Date().toISOString();
  const task = ensureDefaults({
    ...input,
    id: randomUUID(),
    createdAt: now,
    updatedAt: now,
    completedAt: input.status === 'completed' ? now : null
  });

  const state = getState();
  state.tasks.push(task);
  await saveState();
  return cloneTask(task);
}

export function getTask (id) {
  const state = getState();
  const task = state.tasks.find(item => item.id === id);
  if (!task) {
    const error = new Error('Task not found');
    error.statusCode = 404;
    throw error;
  }
  return cloneTask(task);
}

export function listTasks (filters = {}) {
  const state = getState();
  let results = state.tasks.slice();

  if (filters.status) {
    results = results.filter(task => task.status === filters.status);
  }

  if (filters.priority) {
    results = results.filter(task => task.priority === filters.priority);
  }

  if (filters.tag) {
    const tag = filters.tag.toLowerCase();
    results = results.filter(task => task.tags.some(t => t.toLowerCase() === tag));
  }

  if (filters.overdue) {
    results = results.filter(task => isTaskOverdue(task));
  }

  if (filters.search) {
    const term = filters.search.toLowerCase();
    results = results.filter(task =>
      task.title.toLowerCase().includes(term) ||
      task.description.toLowerCase().includes(term)
    );
  }

  const sortField = filters.sortBy ?? 'createdAt';
  const sortOrder = filters.sortOrder === 'asc' ? 1 : -1;

  results.sort((a, b) => {
    if (sortField === 'priority') {
      return (a.priority - b.priority) * sortOrder;
    }
    const aValue = a[sortField] ?? '';
    const bValue = b[sortField] ?? '';
    if (aValue === bValue) return 0;
    return aValue > bValue ? sortOrder : -sortOrder;
  });

  const pageSize = filters.pageSize ?? 20;
  const page = filters.page ?? 1;
  const offset = (page - 1) * pageSize;
  const paged = results.slice(offset, offset + pageSize).map(cloneTask);

  return {
    items: paged,
    pagination: {
      total: results.length,
      page,
      pageSize,
      totalPages: Math.max(1, Math.ceil(results.length / pageSize))
    }
  };
}

export async function updateTask (id, updates) {
  const state = getState();
  const task = state.tasks.find(item => item.id === id);
  if (!task) {
    const error = new Error('Task not found');
    error.statusCode = 404;
    throw error;
  }

  const next = { ...task, ...updates };
  next.updatedAt = new Date().toISOString();

  if (updates.status) {
    if (updates.status === 'completed') {
      next.completedAt = task.completedAt ?? next.updatedAt;
    } else {
      next.completedAt = null;
    }
  }

  Object.assign(task, next);
  await saveState();
  return cloneTask(task);
}

export async function deleteTask (id) {
  const state = getState();
  const index = state.tasks.findIndex(item => item.id === id);
  if (index === -1) {
    const error = new Error('Task not found');
    error.statusCode = 404;
    throw error;
  }
  state.tasks.splice(index, 1);
  await saveState();
}

export async function completeTask (id) {
  const state = getState();
  const task = state.tasks.find(item => item.id === id);
  if (!task) {
    const error = new Error('Task not found');
    error.statusCode = 404;
    throw error;
  }

  task.status = 'completed';
  task.completedAt = new Date().toISOString();
  task.updatedAt = task.completedAt;
  await saveState();
  return cloneTask(task);
}

export function getUpcomingTasks (limit = 5) {
  const now = Date.now();
  const state = getState();
  return state.tasks
    .filter(task => task.dueDate && !['completed', 'cancelled'].includes(task.status))
    .filter(task => new Date(task.dueDate).getTime() >= now)
    .sort((a, b) => new Date(a.dueDate) - new Date(b.dueDate))
    .slice(0, limit)
    .map(cloneTask);
}

export function getOverdueTasks () {
  const now = Date.now();
  const state = getState();
  return state.tasks
    .filter(task => task.dueDate && !['completed', 'cancelled'].includes(task.status))
    .filter(task => new Date(task.dueDate).getTime() < now)
    .sort((a, b) => new Date(a.dueDate) - new Date(b.dueDate))
    .map(cloneTask);
}

export function isTaskOverdue (task) {
  if (!task.dueDate) return false;
  if (['completed', 'cancelled'].includes(task.status)) return false;
  return new Date(task.dueDate).getTime() < Date.now();
}

export function summariseStatuses () {
  const state = getState();
  const summary = Object.fromEntries(TASK_STATUS_VALUES.map(status => [status, 0]));
  for (const task of state.tasks) {
    if (summary[task.status] !== undefined) {
      summary[task.status] += 1;
    }
  }
  return summary;
}
