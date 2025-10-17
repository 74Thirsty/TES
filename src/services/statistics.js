import { getState } from '../storage.js';
import { getUpcomingTasks, getOverdueTasks, summariseStatuses } from './tasks.js';
import { getUpcomingEvents, getActiveEvents } from './events.js';

export function getOverview () {
  const state = getState();
  const taskSummary = summariseStatuses();
  const totalTasks = Object.values(taskSummary).reduce((sum, value) => sum + value, 0);
  const overdueCount = getOverdueTasks().length;

  const now = Date.now();
  const upcomingEvents = state.events.filter(event => new Date(event.startTime).getTime() >= now).length;

  return {
    generatedAt: new Date().toISOString(),
    tasks: {
      total: totalTasks,
      byStatus: taskSummary,
      overdue: overdueCount
    },
    events: {
      upcoming: upcomingEvents,
      active: getActiveEvents(new Date()).length
    },
    upcomingTasks: getUpcomingTasks(5),
    overdueTasks: getOverdueTasks(),
    upcomingEvents: getUpcomingEvents(5),
    activeEvents: getActiveEvents(new Date())
  };
}

export function getFocus () {
  const state = getState();
  const now = new Date();
  const upcomingTask = state.tasks
    .filter(task => ['pending', 'in_progress'].includes(task.status))
    .sort((a, b) => {
      const aDue = a.dueDate ? new Date(a.dueDate).getTime() : Number.POSITIVE_INFINITY;
      const bDue = b.dueDate ? new Date(b.dueDate).getTime() : Number.POSITIVE_INFINITY;
      if (aDue === bDue) {
        return b.priority - a.priority;
      }
      return aDue - bDue;
    })[0] || null;

  const nextEvent = state.events
    .filter(event => new Date(event.startTime).getTime() >= now.getTime())
    .sort((a, b) => new Date(a.startTime) - new Date(b.startTime))[0] || null;

  const focusWindowMinutes = nextEvent
    ? Math.max(0, Math.round((new Date(nextEvent.startTime).getTime() - now.getTime()) / 60000))
    : null;

  return {
    generatedAt: now.toISOString(),
    nextTask: upcomingTask ? {
      id: upcomingTask.id,
      title: upcomingTask.title,
      dueDate: upcomingTask.dueDate,
      priority: upcomingTask.priority
    } : null,
    nextEvent: nextEvent ? {
      id: nextEvent.id,
      name: nextEvent.name,
      startTime: nextEvent.startTime
    } : null,
    focusWindowMinutes
  };
}
