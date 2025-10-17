process.env.TES_DB_FILE = ':memory:';

import test from 'node:test';
import assert from 'node:assert/strict';
import { createAppServer } from '../src/app.js';
import { initStorage, resetState, invalidateStorage } from '../src/storage.js';
import { loadConfigFromEnv } from '../src/config.js';

let server;
let baseUrl;

async function startServer () {
  await loadConfigFromEnv();
  invalidateStorage();
  await initStorage();
  server = createAppServer();
  await new Promise(resolve => server.listen(0, resolve));
  const address = server.address();
  baseUrl = `http://127.0.0.1:${address.port}`;
}

test.before(async () => {
  await startServer();
});

test.after(async () => {
  if (server) {
    await new Promise(resolve => server.close(resolve));
  }
});

test.beforeEach(async () => {
  await resetState();
});

test('creates and retrieves a task', async () => {
  const createResponse = await fetch(`${baseUrl}/api/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: 'Prepare release notes',
      priority: 4,
      dueDate: '2030-01-01T09:00:00.000Z',
      tags: ['release']
    })
  });
  assert.equal(createResponse.status, 201);
  const created = await createResponse.json();
  assert.equal(created.title, 'Prepare release notes');
  assert.equal(created.priority, 4);
  assert.ok(created.id);

  const getResponse = await fetch(`${baseUrl}/api/tasks/${created.id}`);
  assert.equal(getResponse.status, 200);
  const fetched = await getResponse.json();
  assert.equal(fetched.id, created.id);
  assert.equal(fetched.dueDate, '2030-01-01T09:00:00.000Z');
});

test('validates invalid task payloads', async () => {
  const response = await fetch(`${baseUrl}/api/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: '', priority: 10 })
  });
  assert.equal(response.status, 400);
  const body = await response.json();
  assert.ok(body.error.includes('title'));
});

test('lists tasks and marks completion', async () => {
  const creation = await fetch(`${baseUrl}/api/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: 'Complete analytics', status: 'in_progress', tags: ['analytics'] })
  });
  const created = await creation.json();

  const complete = await fetch(`${baseUrl}/api/tasks/${created.id}/complete`, { method: 'POST' });
  assert.equal(complete.status, 200);

  const list = await fetch(`${baseUrl}/api/tasks?status=completed`);
  const payload = await list.json();
  assert.equal(payload.items.length, 1);
  assert.equal(payload.items[0].status, 'completed');
});

test('rejects invalid event chronology', async () => {
  const response = await fetch(`${baseUrl}/api/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'Broken meeting',
      startTime: '2030-01-02T10:00:00.000Z',
      endTime: '2030-01-02T09:00:00.000Z'
    })
  });
  assert.equal(response.status, 400);
});

test('creates events and filters by tag', async () => {
  const create = await fetch(`${baseUrl}/api/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'Quarterly planning',
      startTime: '2030-01-05T12:00:00.000Z',
      endTime: '2030-01-05T13:30:00.000Z',
      tags: ['planning']
    })
  });
  assert.equal(create.status, 201);

  const list = await fetch(`${baseUrl}/api/events?tag=planning`);
  assert.equal(list.status, 200);
  const body = await list.json();
  assert.equal(body.items[0].name, 'Quarterly planning');
});

test('statistics endpoints provide overview and focus', async () => {
  await fetch(`${baseUrl}/api/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: 'Focus work', dueDate: '2030-01-01T09:00:00.000Z' })
  });

  await fetch(`${baseUrl}/api/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'Sync', startTime: '2030-01-01T10:00:00.000Z' })
  });

  const overviewResponse = await fetch(`${baseUrl}/api/statistics/overview`);
  assert.equal(overviewResponse.status, 200);
  const overview = await overviewResponse.json();
  assert.ok('tasks' in overview);
  assert.ok(Array.isArray(overview.upcomingTasks));

  const focusResponse = await fetch(`${baseUrl}/api/statistics/focus`);
  assert.equal(focusResponse.status, 200);
  const focus = await focusResponse.json();
  assert.ok(focus.nextTask);
});
