import { URL } from 'node:url';
import { handleCors, readJsonBody, sendError, sendJson, sendNoContent } from './http.js';
import { initStorage } from './storage.js';
import {
  validateTaskPayload,
  validateEventPayload,
  parseTaskFilters,
  parseEventFilters,
  ensureEventChronology,
  ensureEventChronologyWithExisting
} from './validators.js';
import {
  createTask,
  getTask,
  listTasks,
  updateTask,
  deleteTask,
  completeTask
} from './services/tasks.js';
import {
  createEvent,
  getEvent,
  listEvents,
  updateEvent,
  deleteEvent
} from './services/events.js';
import { getOverview, getFocus } from './services/statistics.js';

export async function handleRequest (req, res) {
  try {
    await initStorage();
  } catch (error) {
    sendError(res, error);
    return;
  }

  if (handleCors(req, res)) {
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host}`);
  const path = url.pathname;
  const method = req.method ?? 'GET';

  try {
    if (path === '/' && method === 'GET') {
      sendJson(res, 200, {
        name: 'Task & Event Scheduler API',
        version: '1.0.0',
        endpoints: {
          tasks: '/api/tasks',
          events: '/api/events',
          statistics: '/api/statistics/overview',
          focus: '/api/statistics/focus',
          health: '/api/health'
        }
      });
      return;
    }

    if (path === '/api/health' && method === 'GET') {
      sendJson(res, 200, { status: 'ok' });
      return;
    }

    if (path.startsWith('/api/tasks')) {
      await handleTaskRoutes(method, path, url, req, res);
      return;
    }

    if (path.startsWith('/api/events')) {
      await handleEventRoutes(method, path, url, req, res);
      return;
    }

    if (path === '/api/statistics/overview' && method === 'GET') {
      const overview = getOverview();
      sendJson(res, 200, overview);
      return;
    }

    if (path === '/api/statistics/focus' && method === 'GET') {
      const focus = getFocus();
      sendJson(res, 200, focus);
      return;
    }

    sendError(res, { statusCode: 404, message: 'Not Found' });
  } catch (error) {
    sendError(res, error);
  }
}

async function handleTaskRoutes (method, path, url, req, res) {
  if (path === '/api/tasks' && method === 'GET') {
    const filters = parseTaskFilters(url.searchParams);
    const data = listTasks(filters);
    sendJson(res, 200, data);
    return;
  }

  if (path === '/api/tasks' && method === 'POST') {
    const payload = await readJsonBody(req);
    const validated = validateTaskPayload(payload);
    const task = await createTask(validated);
    sendJson(res, 201, task);
    return;
  }

  const match = path.match(/^\/api\/tasks\/([^/]+)(?:\/(complete))?$/);
  if (!match) {
    sendError(res, { statusCode: 404, message: 'Not Found' });
    return;
  }

  const [, taskId, action] = match;

  if (!action) {
    if (method === 'GET') {
      const task = getTask(taskId);
      sendJson(res, 200, task);
      return;
    }

    if (method === 'PATCH') {
      const payload = await readJsonBody(req);
      const validated = validateTaskPayload(payload, { partial: true });
      const task = await updateTask(taskId, validated);
      sendJson(res, 200, task);
      return;
    }

    if (method === 'DELETE') {
      await deleteTask(taskId);
      sendNoContent(res);
      return;
    }
  }

  if (action === 'complete' && method === 'POST') {
    const task = await completeTask(taskId);
    sendJson(res, 200, task);
    return;
  }

  sendError(res, { statusCode: 405, message: 'Method Not Allowed' });
}

async function handleEventRoutes (method, path, url, req, res) {
  if (path === '/api/events' && method === 'GET') {
    const filters = parseEventFilters(url.searchParams);
    const data = listEvents(filters);
    sendJson(res, 200, data);
    return;
  }

  if (path === '/api/events' && method === 'POST') {
    const payload = await readJsonBody(req);
    const validated = validateEventPayload(payload);
    ensureEventChronology(validated);
    const event = await createEvent(validated);
    sendJson(res, 201, event);
    return;
  }

  const match = path.match(/^\/api\/events\/([^/]+)$/);
  if (!match) {
    sendError(res, { statusCode: 404, message: 'Not Found' });
    return;
  }

  const [, eventId] = match;

  if (method === 'GET') {
    const event = getEvent(eventId);
    sendJson(res, 200, event);
    return;
  }

  if (method === 'PATCH') {
    const payload = await readJsonBody(req);
    const validated = validateEventPayload(payload, { partial: true });
    const existing = getEvent(eventId);
    ensureEventChronologyWithExisting(validated.startTime ?? existing.startTime, validated.endTime ?? existing.endTime);
    const event = await updateEvent(eventId, validated);
    sendJson(res, 200, event);
    return;
  }

  if (method === 'DELETE') {
    await deleteEvent(eventId);
    sendNoContent(res);
    return;
  }

  sendError(res, { statusCode: 405, message: 'Method Not Allowed' });
}
