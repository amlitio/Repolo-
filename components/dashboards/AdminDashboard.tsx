'use client';

import { useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useRequestStore } from '@/store/requestStore';
import { useUserStore } from '@/store/userStore';
import { useInvitationStore } from '@/store/invitationStore';
import { TimeOffRequest, User } from '@/types';
import StatsCard from '@/components/StatsCard';
import RequestsTable from '@/components/RequestsTable';
import ApprovalModal from '@/components/ApprovalModal';
import InviteUserModal from '@/components/InviteUserModal';
import { Users, Clock, CheckCircle, Mail, UserPlus, Trash2, Copy, Calendar } from 'lucide-react';
import toast from 'react-hot-toast';

export default function AdminDashboard() {
  const { user } = useAuthStore();
  const { requests, updateRequestStatus, fetchAllRequests } = useRequestStore();
  const { users, updateUserBalance } = useUserStore();
  const { invitations, deleteInvitation, fetchPendingInvitations } = useInvitationStore();

  const [selectedRequest, setSelectedRequest] = useState<TimeOffRequest | null>(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [activeSection, setActiveSection] = useState<'requests' | 'users' | 'invitations'>('requests');
  const [editingBalance, setEditingBalance] = useState<{ userId: string; field: string; value: number } | null>(null);

  const pendingManagerReview = requests.filter((r) => r.status === 'pending').length;
  const pendingAdminApproval = requests.filter((r) => r.status === 'manager_approved');
  const approvedRequests = requests.filter((r) => r.status === 'approved').length;
  const pendingInvitations = invitations.filter((i) => i.status === 'pending').length;

  const handleApprove = async (requestId: string, comments: string) => {
    try {
      await updateRequestStatus(requestId, 'approved', comments, user?.name);
      toast.success('Request approved! PTO balance has been deducted');
      await fetchAllRequests();
    } catch (error: any) {
      toast.error(error.message || 'Failed to approve request');
      throw error;
    }
  };

  const handleReject = async (requestId: string, comments: string) => {
    try {
      await updateRequestStatus(requestId, 'rejected', comments, user?.name);
      toast.success('Request rejected');
      await fetchAllRequests();
    } catch (error: any) {
      toast.error(error.message || 'Failed to reject request');
      throw error;
    }
  };

  const handleRequestClick = (request: TimeOffRequest) => {
    if (request.status === 'manager_approved') {
      setSelectedRequest(request);
      setShowApprovalModal(true);
    }
  };

  const handleDeleteInvitation = async (invitationId: string) => {
    if (confirm('Are you sure you want to delete this invitation?')) {
      try {
        await deleteInvitation(invitationId);
        await fetchPendingInvitations();
        toast.success('Invitation deleted');
      } catch (error: any) {
        toast.error(error.message || 'Failed to delete invitation');
      }
    }
  };

  const handleCopyInvitationLink = (invitationId: string) => {
    const link = `${window.location.origin}/signup?invitation=${invitationId}`;
    navigator.clipboard.writeText(link);
    toast.success('Invitation link copied to clipboard');
  };

  const handleBalanceUpdate = async (userId: string, field: 'ptoBalance' | 'sickBalance' | 'personalBalance', value: number) => {
    try {
      await updateUserBalance(userId, field, value);
      toast.success('Balance updated successfully');
      setEditingBalance(null);
    } catch (error: any) {
      toast.error(error.message || 'Failed to update balance');
    }
  };

  if (!user) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600 mt-1">Manage users, approvals, and invitations</p>
        </div>
        <button
          onClick={() => setShowInviteModal(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <UserPlus className="h-5 w-5" />
          <span>Invite User</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatsCard
          title="Total Users"
          value={users.length}
          icon={Users}
          color="blue"
        />
        <StatsCard
          title="Awaiting Admin Approval"
          value={pendingAdminApproval.length}
          icon={Clock}
          color="yellow"
        />
        <StatsCard
          title="Approved Requests"
          value={approvedRequests}
          icon={CheckCircle}
          color="green"
        />
        <StatsCard
          title="Pending Invitations"
          value={pendingInvitations}
          icon={Mail}
          color="purple"
        />
      </div>

      {/* Section Tabs */}
      <div className="flex space-x-2">
        <button
          onClick={() => setActiveSection('requests')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeSection === 'requests'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
          }`}
        >
          <Calendar className="h-4 w-4 inline mr-2" />
          Requests ({pendingAdminApproval.length} pending)
        </button>
        <button
          onClick={() => setActiveSection('users')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeSection === 'users'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
          }`}
        >
          <Users className="h-4 w-4 inline mr-2" />
          Users ({users.length})
        </button>
        <button
          onClick={() => setActiveSection('invitations')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeSection === 'invitations'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
          }`}
        >
          <Mail className="h-4 w-4 inline mr-2" />
          Invitations ({pendingInvitations})
        </button>
      </div>

      {/* Requests Section */}
      {activeSection === 'requests' && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Time Off Requests
          </h2>

          {/* Pending Admin Approval */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Awaiting Final Approval ({pendingAdminApproval.length})
            </h3>
            <div
              className="cursor-pointer"
              onClick={(e) => {
                const target = e.target as HTMLElement;
                const row = target.closest('tr');
                if (row) {
                  const requestId = row.getAttribute('data-request-id');
                  const request = pendingAdminApproval.find((r) => r.id === requestId);
                  if (request) {
                    handleRequestClick(request);
                  }
                }
              }}
            >
              <RequestsTable
                requests={pendingAdminApproval}
                showUser={true}
                showActions={false}
              />
            </div>
            {pendingAdminApproval.length > 0 && (
              <p className="text-sm text-gray-500 mt-4 text-center">
                Click on a request to review and approve/reject
              </p>
            )}
          </div>

          {/* All Requests */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              All Requests ({requests.length})
            </h3>
            <RequestsTable
              requests={requests}
              showUser={true}
              showActions={false}
            />
          </div>
        </div>
      )}

      {/* Users Section */}
      {activeSection === 'users' && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            All Users
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Manager
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Vacation
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sick
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Personal
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{u.name}</div>
                        <div className="text-sm text-gray-500">{u.email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="badge badge-pending capitalize">{u.role}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {u.managerName || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {editingBalance?.userId === u.id && editingBalance.field === 'ptoBalance' ? (
                        <input
                          type="number"
                          defaultValue={u.ptoBalance}
                          onBlur={(e) => handleBalanceUpdate(u.id, 'ptoBalance', Number(e.target.value))}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleBalanceUpdate(u.id, 'ptoBalance', Number((e.target as HTMLInputElement).value));
                            }
                          }}
                          className="w-20 px-2 py-1 border rounded"
                          autoFocus
                        />
                      ) : (
                        <button
                          onClick={() => setEditingBalance({ userId: u.id, field: 'ptoBalance', value: u.ptoBalance })}
                          className="text-sm text-gray-900 hover:text-primary-600"
                        >
                          {u.ptoBalance} days
                        </button>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {editingBalance?.userId === u.id && editingBalance.field === 'sickBalance' ? (
                        <input
                          type="number"
                          defaultValue={u.sickBalance}
                          onBlur={(e) => handleBalanceUpdate(u.id, 'sickBalance', Number(e.target.value))}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleBalanceUpdate(u.id, 'sickBalance', Number((e.target as HTMLInputElement).value));
                            }
                          }}
                          className="w-20 px-2 py-1 border rounded"
                          autoFocus
                        />
                      ) : (
                        <button
                          onClick={() => setEditingBalance({ userId: u.id, field: 'sickBalance', value: u.sickBalance })}
                          className="text-sm text-gray-900 hover:text-primary-600"
                        >
                          {u.sickBalance} days
                        </button>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {editingBalance?.userId === u.id && editingBalance.field === 'personalBalance' ? (
                        <input
                          type="number"
                          defaultValue={u.personalBalance}
                          onBlur={(e) => handleBalanceUpdate(u.id, 'personalBalance', Number(e.target.value))}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleBalanceUpdate(u.id, 'personalBalance', Number((e.target as HTMLInputElement).value));
                            }
                          }}
                          className="w-20 px-2 py-1 border rounded"
                          autoFocus
                        />
                      ) : (
                        <button
                          onClick={() => setEditingBalance({ userId: u.id, field: 'personalBalance', value: u.personalBalance })}
                          className="text-sm text-gray-900 hover:text-primary-600"
                        >
                          {u.personalBalance} days
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-sm text-gray-500 mt-4 text-center">
            Click on any balance to edit
          </p>
        </div>
      )}

      {/* Invitations Section */}
      {activeSection === 'invitations' && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Pending Invitations
          </h2>
          <div className="space-y-3">
            {invitations.map((invitation) => (
              <div
                key={invitation.id}
                className="bg-gray-50 rounded-lg p-4 flex items-center justify-between"
              >
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">{invitation.name}</h3>
                      <p className="text-sm text-gray-600">{invitation.email}</p>
                    </div>
                    <span className="badge badge-pending capitalize">{invitation.role}</span>
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    {invitation.managerName && (
                      <span>Manager: {invitation.managerName} • </span>
                    )}
                    Invited by {invitation.invitedByName} •{' '}
                    Expires: {new Date(invitation.expiresAt).toLocaleDateString()}
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleCopyInvitationLink(invitation.id)}
                    className="p-2 text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                    title="Copy invitation link"
                  >
                    <Copy className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleDeleteInvitation(invitation.id)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Delete invitation"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              </div>
            ))}
            {invitations.length === 0 && (
              <p className="text-gray-500 text-center py-8">No pending invitations</p>
            )}
          </div>
        </div>
      )}

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
        isAdmin={true}
      />

      {/* Invite User Modal */}
      <InviteUserModal
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
      />
    </div>
  );
}
