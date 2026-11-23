// src/lib/statusService.js

/**
 * Centralized status transition definitions and validation.
 * All lifecycle states are defined here.
 */
export const STATUS = {
  SUBMITTED: 'submitted',
  AI_CLASSIFIED: 'ai_classified',
  ASSIGNED: 'assigned',
  ACKNOWLEDGED: 'acknowledged',
  IN_PROGRESS: 'in_progress',
  RESOLUTION_SUBMITTED: 'resolution_submitted',
  VERIFICATION: 'verification',
  RESOLVED: 'resolved',
  REJECTED: 'rejected',
  REASSIGNED: 'reassigned',
};

// Map of valid transitions: from => [allowed next statuses]
export const VALID_TRANSITIONS = {
  [STATUS.SUBMITTED]: [STATUS.AI_CLASSIFIED],
  [STATUS.AI_CLASSIFIED]: [STATUS.ASSIGNED],
  [STATUS.ASSIGNED]: [STATUS.ACKNOWLEDGED, STATUS.REJECTED],
  [STATUS.ACKNOWLEDGED]: [STATUS.IN_PROGRESS],
  [STATUS.IN_PROGRESS]: [STATUS.RESOLUTION_SUBMITTED],
  [STATUS.RESOLUTION_SUBMITTED]: [STATUS.VERIFICATION],
  [STATUS.VERIFICATION]: [STATUS.RESOLVED],
  [STATUS.REJECTED]: [STATUS.REASSIGNED],
  [STATUS.REASSIGNED]: [STATUS.ASSIGNED],
};

/**
 * Check whether a transition from `current` to `next` is allowed.
 * @param {string} current - current status value
 * @param {string} next - desired next status value
 * @returns {boolean}
 */
export function canTransition(current, next) {
  const allowed = VALID_TRANSITIONS[current] ?? [];
  return allowed.includes(next);
}

/**
 * Get a list of possible next statuses for a given current status.
 * @param {string} current
 * @returns {string[]}
 */
export function nextStatusOptions(current) {
  return VALID_TRANSITIONS[current] ?? [];
}
