'use client';

import { useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useRequestStore } from '@/store/requestStore';
import { LeaveType } from '@/types';
import { calculateBusinessDays, hasSufficientBalance, getBalanceForLeaveType } from '@/lib/utils';
import toast from 'react-hot-toast';
import LoadingSpinner from './LoadingSpinner';

interface RequestFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export default function RequestForm({ onSuccess, onCancel }: RequestFormProps) {
  const { user } = useAuthStore();
  const { createRequest, loading } = useRequestStore();

  const [leaveType, setLeaveType] = useState<LeaveType>('vacation');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('');

  const totalDays =
    startDate && endDate
      ? calculateBusinessDays(new Date(startDate), new Date(endDate))
      : 0;

  const currentBalance = user ? getBalanceForLeaveType(user, leaveType) : 0;
  const hasSufficient = user
    ? hasSufficientBalance(user, leaveType, totalDays)
    : false;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!user) {
      toast.error('User not authenticated');
      return;
    }

    if (!startDate || !endDate) {
      toast.error('Please select start and end dates');
      return;
    }

    if (new Date(startDate) > new Date(endDate)) {
      toast.error('End date must be after start date');
      return;
    }

    if (!hasSufficient) {
      toast.error(`Insufficient ${leaveType} balance`);
      return;
    }

    if (!reason.trim()) {
      toast.error('Please provide a reason');
      return;
    }

    try {
      await createRequest(
        user.id,
        user.name,
        user.email,
        user.managerId,
        user.managerName,
        leaveType,
        new Date(startDate),
        new Date(endDate),
        reason
      );

      toast.success('Request submitted successfully');
      onSuccess();
    } catch (error: any) {
      toast.error(error.message || 'Failed to submit request');
    }
  };

  if (!user) return null;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Leave Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Leave Type
        </label>
        <select
          value={leaveType}
          onChange={(e) => setLeaveType(e.target.value as LeaveType)}
          className="input-field"
          disabled={loading}
        >
          <option value="vacation">Vacation (PTO)</option>
          <option value="sick">Sick Leave</option>
          <option value="personal">Personal Leave</option>
        </select>
        <p className="text-sm text-gray-500 mt-1">
          Available balance: {currentBalance} days
        </p>
      </div>

      {/* Date Range */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Start Date
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="input-field"
            required
            disabled={loading}
            min={new Date().toISOString().split('T')[0]}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            End Date
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="input-field"
            required
            disabled={loading}
            min={startDate || new Date().toISOString().split('T')[0]}
          />
        </div>
      </div>

      {/* Total Days */}
      {startDate && endDate && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-900">
            <span className="font-semibold">Total business days:</span> {totalDays}
          </p>
          <p className="text-sm text-blue-900 mt-1">
            <span className="font-semibold">Remaining balance:</span>{' '}
            {currentBalance - totalDays} days
          </p>
          {!hasSufficient && (
            <p className="text-sm text-red-600 font-semibold mt-2">
              Insufficient balance for this request
            </p>
          )}
        </div>
      )}

      {/* Reason */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Reason
        </label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="input-field"
          rows={4}
          required
          disabled={loading}
          placeholder="Please provide a reason for your time off request..."
        />
      </div>

      {/* Actions */}
      <div className="flex space-x-3">
        <button
          type="submit"
          disabled={loading || !hasSufficient}
          className="btn-primary flex-1"
        >
          {loading ? <LoadingSpinner size="sm" /> : 'Submit Request'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={loading}
          className="btn-secondary flex-1"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
