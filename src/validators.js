const TASK_STATUSES = ['pending', 'in_progress', 'completed', 'cancelled'];
const TASK_SORT_FIELDS = ['createdAt', 'updatedAt', 'dueDate', 'priority'];

function ensureString (value, field) {
  if (typeof value !== 'string') {
    throw createValidationError(`${field} must be a string`);
  }
  return value;
}

function ensureArray (value, field) {
  if (!Array.isArray(value)) {
    throw createValidationError(`${field} must be an array`);
  }
  return value;
}

function normaliseTags (tags) {
  if (tags === undefined) return [];
  const values = ensureArray(tags, 'tags')
    .map(tag => ensureString(tag, 'tag').trim())
    .filter(Boolean);
  const seen = new Set();
  const unique = [];
  for (const value of values) {
    const key = value.toLowerCase();
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(value);
    }
  }
  return unique;
}

function parseDate (value, field) {
  if (value === undefined || value === null) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    throw createValidationError(`${field} must be a valid date`);
  }
  return date.toISOString();
}

function parseBoolean (value) {
  if (value === undefined) return undefined;
  if (typeof value === 'boolean') return value;
  if (typeof value === 'string') {
    const lower = value.toLowerCase();
    if (['true', '1', 'yes'].includes(lower)) return true;
    if (['false', '0', 'no'].includes(lower)) return false;
  }
  return undefined;
}

function createValidationError (message, details) {
  const error = new Error(message);
  error.statusCode = 400;
  if (details) {
    error.details = details;
  }
  return error;
}

export function validateTaskPayload (payload, { partial = false } = {}) {
  if (typeof payload !== 'object' || payload === null) {
    throw createValidationError('Payload must be an object');
  }

  const result = {};

  if (!partial || payload.title !== undefined) {
    const title = ensureString(payload.title, 'title').trim();
    if (title.length === 0) {
      throw createValidationError('title is required');
    }
    result.title = title;
  }

  if (payload.description !== undefined) {
    const description = ensureString(payload.description, 'description');
    result.description = description.trim();
  }

  if (payload.status !== undefined) {
    const status = ensureString(payload.status, 'status');
    if (!TASK_STATUSES.includes(status)) {
      throw createValidationError(`status must be one of ${TASK_STATUSES.join(', ')}`);
    }
    result.status = status;
  }

  if (payload.priority !== undefined) {
    const priority = Number(payload.priority);
    if (!Number.isInteger(priority) || priority < 1 || priority > 5) {
      throw createValidationError('priority must be an integer between 1 and 5');
    }
    result.priority = priority;
  }

  if (payload.dueDate !== undefined) {
    result.dueDate = parseDate(payload.dueDate, 'dueDate');
  }

  if (payload.estimatedMinutes !== undefined) {
    const minutes = Number(payload.estimatedMinutes);
    if (!Number.isInteger(minutes) || minutes <= 0 || minutes > 24 * 60) {
      throw createValidationError('estimatedMinutes must be a positive integer up to 1440');
    }
    result.estimatedMinutes = minutes;
  }

  if (payload.tags !== undefined) {
    result.tags = normaliseTags(payload.tags);
  }

  if (Object.keys(result).length === 0) {
    throw createValidationError('At least one field must be provided');
  }

  return result;
}

export function validateEventPayload (payload, { partial = false } = {}) {
  if (typeof payload !== 'object' || payload === null) {
    throw createValidationError('Payload must be an object');
  }

  const result = {};

  if (!partial || payload.name !== undefined) {
    const name = ensureString(payload.name, 'name').trim();
    if (name.length === 0) {
      throw createValidationError('name is required');
    }
    result.name = name;
  }

  if (payload.description !== undefined) {
    result.description = ensureString(payload.description, 'description').trim();
  }

  if (payload.location !== undefined) {
    result.location = ensureString(payload.location, 'location').trim();
  }

  if (!partial || payload.startTime !== undefined) {
    result.startTime = parseDate(payload.startTime, 'startTime');
  }

  if (payload.endTime !== undefined) {
    result.endTime = parseDate(payload.endTime, 'endTime');
  }

  if (payload.allDay !== undefined) {
    const boolean = parseBoolean(payload.allDay);
    if (boolean === undefined) {
      throw createValidationError('allDay must be a boolean');
    }
    result.allDay = boolean;
  }

  if (payload.tags !== undefined) {
    result.tags = normaliseTags(payload.tags);
  }

  if (Object.keys(result).length === 0) {
    throw createValidationError('At least one field must be provided');
  }

  return result;
}

export function parseTaskFilters (searchParams) {
  const filters = {};

  const status = searchParams.get('status');
  if (status && TASK_STATUSES.includes(status)) {
    filters.status = status;
  }

  const priority = searchParams.get('priority');
  if (priority !== null) {
    const value = Number(priority);
    if (Number.isInteger(value) && value >= 1 && value <= 5) {
      filters.priority = value;
    }
  }

  const tag = searchParams.get('tag');
  if (tag) {
    filters.tag = tag.toLowerCase();
  }

  const overdue = parseBoolean(searchParams.get('overdue'));
  if (overdue !== undefined) {
    filters.overdue = overdue;
  }

  const search = searchParams.get('search');
  if (search) {
    filters.search = search.toLowerCase();
  }

  const sortBy = searchParams.get('sortBy');
  if (sortBy && TASK_SORT_FIELDS.includes(sortBy)) {
    filters.sortBy = sortBy;
  }

  const sortOrder = searchParams.get('sortOrder');
  if (sortOrder && ['asc', 'desc'].includes(sortOrder.toLowerCase())) {
    filters.sortOrder = sortOrder.toLowerCase();
  }

  const page = Number(searchParams.get('page'));
  if (Number.isInteger(page) && page > 0) {
    filters.page = page;
  }

  const pageSize = Number(searchParams.get('pageSize'));
  if (Number.isInteger(pageSize) && pageSize > 0 && pageSize <= 100) {
    filters.pageSize = pageSize;
  }

  return filters;
}

export function parseEventFilters (searchParams) {
  const filters = {};

  const tag = searchParams.get('tag');
  if (tag) {
    filters.tag = tag.toLowerCase();
  }

  const from = searchParams.get('from');
  if (from) {
    filters.from = parseDate(from, 'from');
  }

  const to = searchParams.get('to');
  if (to) {
    filters.to = parseDate(to, 'to');
  }

  const search = searchParams.get('search');
  if (search) {
    filters.search = search.toLowerCase();
  }

  const page = Number(searchParams.get('page'));
  if (Number.isInteger(page) && page > 0) {
    filters.page = page;
  }

  const pageSize = Number(searchParams.get('pageSize'));
  if (Number.isInteger(pageSize) && pageSize > 0 && pageSize <= 100) {
    filters.pageSize = pageSize;
  }

  return filters;
}

export function ensureEventChronology (event) {
  if (event.endTime && event.startTime && new Date(event.endTime) < new Date(event.startTime)) {
    throw createValidationError('endTime must be after startTime');
  }
}

export function ensureEventChronologyWithExisting (startTime, endTime) {
  if (endTime && startTime && new Date(endTime) < new Date(startTime)) {
    throw createValidationError('endTime must be after startTime');
  }
}

export const TASK_STATUS_VALUES = TASK_STATUSES;
