import { randomUUID } from 'node:crypto';
import { getState, saveState } from '../storage.js';

function cloneEvent (event) {
  return structuredClone(event);
}

function ensureDefaults (payload) {
  return {
    description: '',
    location: '',
    endTime: null,
    allDay: false,
    tags: [],
    ...payload
  };
}

export async function createEvent (input) {
  const now = new Date().toISOString();
  const event = ensureDefaults({
    ...input,
    id: randomUUID(),
    createdAt: now,
    updatedAt: now
  });

  const state = getState();
  state.events.push(event);
  await saveState();
  return cloneEvent(event);
}

export function getEvent (id) {
  const state = getState();
  const event = state.events.find(item => item.id === id);
  if (!event) {
    const error = new Error('Event not found');
    error.statusCode = 404;
    throw error;
  }
  return cloneEvent(event);
}

export async function updateEvent (id, updates) {
  const state = getState();
  const event = state.events.find(item => item.id === id);
  if (!event) {
    const error = new Error('Event not found');
    error.statusCode = 404;
    throw error;
  }

  const next = { ...event, ...updates };
  next.updatedAt = new Date().toISOString();

  Object.assign(event, next);
  await saveState();
  return cloneEvent(event);
}

export async function deleteEvent (id) {
  const state = getState();
  const index = state.events.findIndex(item => item.id === id);
  if (index === -1) {
    const error = new Error('Event not found');
    error.statusCode = 404;
    throw error;
  }
  state.events.splice(index, 1);
  await saveState();
}

export function listEvents (filters = {}) {
  const state = getState();
  let results = state.events.slice();

  if (filters.tag) {
    const tag = filters.tag.toLowerCase();
    results = results.filter(event => event.tags.some(t => t.toLowerCase() === tag));
  }

  if (filters.from) {
    const fromTime = new Date(filters.from).getTime();
    results = results.filter(event => {
      const end = event.endTime ? new Date(event.endTime).getTime() : null;
      return end === null || end >= fromTime;
    });
  }

  if (filters.to) {
    const toTime = new Date(filters.to).getTime();
    results = results.filter(event => new Date(event.startTime).getTime() <= toTime);
  }

  if (filters.search) {
    const term = filters.search.toLowerCase();
    results = results.filter(event =>
      event.name.toLowerCase().includes(term) ||
      event.description.toLowerCase().includes(term) ||
      event.location.toLowerCase().includes(term)
    );
  }

  results.sort((a, b) => new Date(a.startTime) - new Date(b.startTime));

  const pageSize = filters.pageSize ?? 20;
  const page = filters.page ?? 1;
  const offset = (page - 1) * pageSize;
  const paged = results.slice(offset, offset + pageSize).map(cloneEvent);

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

export function getUpcomingEvents (limit = 5) {
  const now = Date.now();
  const state = getState();
  return state.events
    .filter(event => new Date(event.startTime).getTime() >= now)
    .sort((a, b) => new Date(a.startTime) - new Date(b.startTime))
    .slice(0, limit)
    .map(cloneEvent);
}

export function getActiveEvents (referenceDate = new Date()) {
  const timestamp = referenceDate.getTime();
  const state = getState();
  return state.events
    .filter(event => {
      const start = new Date(event.startTime).getTime();
      const end = event.endTime ? new Date(event.endTime).getTime() : null;
      if (event.allDay) {
        const startDate = new Date(event.startTime);
        return startDate.toDateString() === referenceDate.toDateString();
      }
      return start <= timestamp && (end === null || end >= timestamp);
    })
    .map(cloneEvent);
}
