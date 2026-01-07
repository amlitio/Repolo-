'use client';

import { useState } from 'react';
import { TimeOffRequest, RequestStatus } from '@/types';
import { formatDate, capitalize, getLeaveTypeColor } from '@/lib/utils';
import Modal from './Modal';
import LoadingSpinner from './LoadingSpinner';
import { Calendar, Clock, User } from 'lucide-react';

interface ApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  request: TimeOffRequest | null;
  onApprove: (requestId: string, comments: string) => Promise<void>;
  onReject: (requestId: string, comments: string) => Promise<void>;
  isAdmin?: boolean;
}

export default function ApprovalModal({
  isOpen,
  onClose,
  request,
  onApprove,
  onReject,
  isAdmin = false,
}: ApprovalModalProps) {
  const [comments, setComments] = useState('');
  const [loading, setLoading] = useState(false);

  if (!request) return null;

  const handleApprove = async () => {
    try {
      setLoading(true);
      await onApprove(request.id, comments);
      setComments('');
      onClose();
    } catch (error) {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!comments.trim()) {
      alert('Please provide a reason for rejection');
      return;
    }

    try {
      setLoading(true);
      await onReject(request.id, comments);
      setComments('');
      onClose();
    } catch (error) {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isAdmin ? 'Final Approval' : 'Review Request'}
      maxWidth="lg"
    >
      <div className="space-y-6">
        {/* Employee Info */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center space-x-3 mb-3">
            <User className="h-5 w-5 text-gray-400" />
            <div>
              <p className="font-semibold text-gray-900">{request.userName}</p>
              <p className="text-sm text-gray-500">{request.userEmail}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500 mb-1">Leave Type</p>
              <span
                className={`badge ${getLeaveTypeColor(request.leaveType)}`}
              >
                {capitalize(request.leaveType)}
              </span>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">Total Days</p>
              <div className="flex items-center text-sm font-semibold text-gray-900">
                <Clock className="h-4 w-4 mr-1 text-gray-400" />
                {request.totalDays}
              </div>
            </div>
          </div>
        </div>

        {/* Dates */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">Dates</p>
          <div className="flex items-center space-x-2 text-sm text-gray-900">
            <Calendar className="h-4 w-4 text-gray-400" />
            <span>
              {formatDate(request.startDate)} - {formatDate(request.endDate)}
            </span>
          </div>
        </div>

        {/* Reason */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">Reason</p>
          <p className="text-sm text-gray-900 bg-gray-50 rounded-lg p-3">
            {request.reason}
          </p>
        </div>

        {/* Manager Comments (if admin is reviewing) */}
        {isAdmin && request.managerComments && (
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">
              Manager Comments
            </p>
            <p className="text-sm text-gray-900 bg-blue-50 rounded-lg p-3">
              {request.managerComments}
            </p>
          </div>
        )}

        {/* Comments */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {isAdmin ? 'Admin Comments (Optional)' : 'Manager Comments (Optional)'}
          </label>
          <textarea
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            className="input-field"
            rows={3}
            placeholder="Add any comments..."
            disabled={loading}
          />
        </div>

        {/* Actions */}
        <div className="flex space-x-3">
          <button
            onClick={handleApprove}
            disabled={loading}
            className="btn-success flex-1"
          >
            {loading ? <LoadingSpinner size="sm" /> : 'Approve'}
          </button>
          <button
            onClick={handleReject}
            disabled={loading}
            className="btn-danger flex-1"
          >
            {loading ? <LoadingSpinner size="sm" /> : 'Reject'}
          </button>
        </div>
      </div>
    </Modal>
  );
}
