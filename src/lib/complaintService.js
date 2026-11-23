// src/lib/complaintService.js
import { supabase } from './supabase';
import { canTransition } from './statusService';

/**
 * Fetch a single complaint with its fields.
 * @param {string} id - complaint UUID
 */
export async function fetchComplaint(id) {
  const { data, error } = await supabase
    .from('complaints')
    .select('*')
    .eq('id', id)
    .single();
  if (error) throw error;
  return data;
}

/**
 * Update a complaint's status if the transition is valid.
 * Also creates a history record.
 * @param {string} complaintId
 * @param {string} newStatus - target status value
 * @param {string} userId - auth user id performing the change
 * @param {string} [message] - optional custom history message (e.g., rejection reason)
 */
export async function updateComplaintStatus(complaintId, newStatus, userId, message) {
  // 1. Get current complaint
  const { data: current, error: fetchErr } = await supabase
    .from('complaints')
    .select('status')
    .eq('id', complaintId)
    .single();
  if (fetchErr) throw fetchErr;

  const currentStatus = current.status;

  // 2. Validate transition
  if (!canTransition(currentStatus, newStatus)) {
    throw new Error(`Invalid status transition from ${currentStatus} to ${newStatus}`);
  }

  // 3. Perform update
  const { error: updateErr } = await supabase
    .from('complaints')
    .update({ status: newStatus, updated_at: new Date().toISOString() })
    .eq('id', complaintId);
  if (updateErr) throw updateErr;

  // 4. Insert history entry
  const historyMessage = message || `Status changed to ${newStatus}`;
  const { error: historyErr } = await supabase
    .from('complaint_history')
    .insert([
      {
        complaint_id: complaintId,
        status: newStatus,
        message: historyMessage,
        changed_by: userId,
      },
    ]);
  if (historyErr) throw historyErr;

  return true;
}
