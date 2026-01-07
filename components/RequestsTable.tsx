'use client';

import { TimeOffRequest } from '@/types';
import {
  formatDate,
  capitalize,
  getLeaveTypeColor,
  getStatusColor,
  getStatusDisplay,
} from '@/lib/utils';
import { Calendar, Clock, X } from 'lucide-react';
import toast from 'react-hot-toast';

interface RequestsTableProps {
  requests: TimeOffRequest[];
  onCancel?: (requestId: string) => void;
  showActions?: boolean;
  showUser?: boolean;
}

export default function RequestsTable({
  requests,
  onCancel,
  showActions = false,
  showUser = false,
}: RequestsTableProps) {
  const handleCancel = async (requestId: string) => {
    if (confirm('Are you sure you want to cancel this request?')) {
      try {
        if (onCancel) {
          await onCancel(requestId);
          toast.success('Request cancelled successfully');
        }
      } catch (error: any) {
        toast.error(error.message || 'Failed to cancel request');
      }
    }
  };

  if (requests.length === 0) {
    return (
      <div className="text-center py-12">
        <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-500">No time off requests found</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {showUser && (
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Employee
              </th>
            )}
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Leave Type
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Dates
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Days
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Reason
            </th>
            {showActions && (
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            )}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {requests.map((request) => (
            <tr key={request.id} data-request-id={request.id} className="hover:bg-gray-50">
              {showUser && (
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {request.userName}
                    </div>
                    <div className="text-sm text-gray-500">{request.userEmail}</div>
                  </div>
                </td>
              )}
              <td className="px-6 py-4 whitespace-nowrap">
                <span
                  className={`badge ${getLeaveTypeColor(request.leaveType)}`}
                >
                  {capitalize(request.leaveType)}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center text-sm text-gray-900">
                  <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                  <div>
                    <div>{formatDate(request.startDate)}</div>
                    <div className="text-gray-500">
                      to {formatDate(request.endDate)}
                    </div>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center text-sm text-gray-900">
                  <Clock className="h-4 w-4 mr-2 text-gray-400" />
                  {request.totalDays}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`badge ${getStatusColor(request.status)}`}>
                  {getStatusDisplay(request.status)}
                </span>
              </td>
              <td className="px-6 py-4">
                <div className="text-sm text-gray-900 max-w-xs truncate">
                  {request.reason}
                </div>
                {request.managerComments && (
                  <div className="text-xs text-blue-600 mt-1">
                    Manager: {request.managerComments}
                  </div>
                )}
                {request.adminComments && (
                  <div className="text-xs text-green-600 mt-1">
                    Admin: {request.adminComments}
                  </div>
                )}
              </td>
              {showActions && (
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  {request.status === 'pending' && onCancel && (
                    <button
                      onClick={() => handleCancel(request.id)}
                      className="text-red-600 hover:text-red-900"
                      title="Cancel request"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
