'use client';

import { useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useRequestStore } from '@/store/requestStore';
import { useUserStore } from '@/store/userStore';
import { TimeOffRequest } from '@/types';
import StatsCard from '@/components/StatsCard';
import RequestsTable from '@/components/RequestsTable';
import ApprovalModal from '@/components/ApprovalModal';
import { Users, Clock, CheckCircle, XCircle, Calendar } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ManagerDashboard() {
  const { user } = useAuthStore();
  const { requests, updateRequestStatus, fetchManagerRequests } = useRequestStore();
  const { users } = useUserStore();

  const [selectedRequest, setSelectedRequest] = useState<TimeOffRequest | null>(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'pending' | 'reviewed'>('pending');

  const pendingRequests = requests.filter((r) => r.status === 'pending');
  const reviewedRequests = requests.filter((r) => r.status !== 'pending');
  const totalTeamMembers = users.length;

  const handleApprove = async (requestId: string, comments: string) => {
    try {
      await updateRequestStatus(requestId, 'manager_approved', comments, user?.name);
      toast.success('Request approved and sent to admin for final approval');
      if (user) {
        await fetchManagerRequests(user.id);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to approve request');
      throw error;
    }
  };

  const handleReject = async (requestId: string, comments: string) => {
    try {
      await updateRequestStatus(requestId, 'rejected', comments, user?.name);
      toast.success('Request rejected');
      if (user) {
        await fetchManagerRequests(user.id);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to reject request');
      throw error;
    }
  };

  const handleRequestClick = (request: TimeOffRequest) => {
    if (request.status === 'pending') {
      setSelectedRequest(request);
      setShowApprovalModal(true);
    }
  };

  if (!user) return null;

  const displayedRequests = activeTab === 'pending' ? pendingRequests : reviewedRequests;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Manager Dashboard</h1>
        <p className="text-gray-600 mt-1">Review and approve your team's time off requests</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatsCard
          title="Team Members"
          value={totalTeamMembers}
          icon={Users}
          color="blue"
        />
        <StatsCard
          title="Pending Reviews"
          value={pendingRequests.length}
          icon={Clock}
          color="yellow"
        />
        <StatsCard
          title="Approved (This Month)"
          value={reviewedRequests.filter((r) => r.status === 'manager_approved' || r.status === 'approved').length}
          icon={CheckCircle}
          color="green"
        />
        <StatsCard
          title="Rejected (This Month)"
          value={reviewedRequests.filter((r) => r.status === 'rejected').length}
          icon={XCircle}
          color="red"
        />
      </div>

      {/* Team Members Section */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          My Team
        </h2>
        {users.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {users.map((member) => (
              <div key={member.id} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{member.name}</h3>
                    <p className="text-sm text-gray-600">{member.email}</p>
                  </div>
                </div>
                <div className="mt-3 space-y-1">
                  <p className="text-xs text-gray-600">
                    <span className="font-medium">Vacation:</span> {member.ptoBalance} days
                  </p>
                  <p className="text-xs text-gray-600">
                    <span className="font-medium">Sick:</span> {member.sickBalance} days
                  </p>
                  <p className="text-xs text-gray-600">
                    <span className="font-medium">Personal:</span> {member.personalBalance} days
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No team members yet</p>
        )}
      </div>

      {/* Requests Section */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            Time Off Requests
          </h2>

          {/* Tabs */}
          <div className="flex space-x-2">
            <button
              onClick={() => setActiveTab('pending')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'pending'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Pending ({pendingRequests.length})
            </button>
            <button
              onClick={() => setActiveTab('reviewed')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'reviewed'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Reviewed ({reviewedRequests.length})
            </button>
          </div>
        </div>

        <div
          className={activeTab === 'pending' ? 'cursor-pointer' : ''}
          onClick={(e) => {
            if (activeTab === 'pending') {
              const target = e.target as HTMLElement;
              const row = target.closest('tr');
              if (row) {
                const requestId = row.getAttribute('data-request-id');
                const request = pendingRequests.find((r) => r.id === requestId);
                if (request) {
                  handleRequestClick(request);
                }
              }
            }
          }}
        >
          <RequestsTable
            requests={displayedRequests.map((r) => ({
              ...r,
              id: r.id,
            }))}
            showUser={true}
            showActions={false}
          />
        </div>

        {activeTab === 'pending' && pendingRequests.length > 0 && (
          <p className="text-sm text-gray-500 mt-4 text-center">
            Click on a request to review and approve/reject
          </p>
        )}
      </div>

      {/* Approval Modal */}
      <ApprovalModal
        isOpen={showApprovalModal}
        onClose={() => {
          setShowApprovalModal(false);
          setSelectedRequest(null);
        }}
        request={selectedRequest}
        onApprove={handleApprove}
        onReject={handleReject}
        isAdmin={false}
      />
    </div>
  );
}
