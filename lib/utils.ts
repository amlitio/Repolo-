import { differenceInBusinessDays, isWeekend, addDays, format } from 'date-fns';

/**
 * Calculate business days between two dates (excluding weekends)
 */
export function calculateBusinessDays(startDate: Date, endDate: Date): number {
  return differenceInBusinessDays(endDate, startDate) + 1;
}

/**
 * Check if a date is a weekend
 */
export function isWeekendDay(date: Date): boolean {
  return isWeekend(date);
}

/**
 * Format date to readable string
 */
export function formatDate(date: Date): string {
  return format(date, 'MMM dd, yyyy');
}

/**
 * Format date to ISO string for input fields
 */
export function formatDateInput(date: Date): string {
  return format(date, 'yyyy-MM-dd');
}

/**
 * Get color for leave type
 */
export function getLeaveTypeColor(leaveType: string): string {
  const colors: Record<string, string> = {
    vacation: 'bg-blue-100 text-blue-800',
    sick: 'bg-red-100 text-red-800',
    personal: 'bg-purple-100 text-purple-800',
  };
  return colors[leaveType] || 'bg-gray-100 text-gray-800';
}

/**
 * Get color for status
 */
export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    manager_approved: 'bg-blue-100 text-blue-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
}

/**
 * Get display name for status
 */
export function getStatusDisplay(status: string): string {
  const displays: Record<string, string> = {
    pending: 'Pending Manager Review',
    manager_approved: 'Pending Admin Approval',
    approved: 'Approved',
    rejected: 'Rejected',
  };
  return displays[status] || status;
}

/**
 * Capitalize first letter
 */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Get balance for leave type
 */
export function getBalanceForLeaveType(
  user: { ptoBalance: number; sickBalance: number; personalBalance: number },
  leaveType: 'vacation' | 'sick' | 'personal'
): number {
  const balances = {
    vacation: user.ptoBalance,
    sick: user.sickBalance,
    personal: user.personalBalance,
  };
  return balances[leaveType] || 0;
}

/**
 * Check if user has sufficient balance
 */
export function hasSufficientBalance(
  user: { ptoBalance: number; sickBalance: number; personalBalance: number },
  leaveType: 'vacation' | 'sick' | 'personal',
  days: number
): boolean {
  const balance = getBalanceForLeaveType(user, leaveType);
  return balance >= days;
}
