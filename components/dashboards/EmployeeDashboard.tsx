'use client';

import { useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useRequestStore } from '@/store/requestStore';
import StatsCard from '@/components/StatsCard';
import RequestsTable from '@/components/RequestsTable';
import RequestForm from '@/components/RequestForm';
import Modal from '@/components/Modal';
import { Calendar, Clock, Plus, Briefcase, Heart } from 'lucide-react';
import toast from 'react-hot-toast';

export default function EmployeeDashboard() {
  const { user } = useAuthStore();
  const { requests, cancelRequest, fetchUserRequests } = useRequestStore();

  const [showRequestModal, setShowRequestModal] = useState(false);

  const handleCancelRequest = async (requestId: string) => {
    try {
      await cancelRequest(requestId);
      if (user) {
        await fetchUserRequests(user.id);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to cancel request');
    }
  };

  const handleRequestSuccess = async () => {
    setShowRequestModal(false);
    if (user) {
      await fetchUserRequests(user.id);
    }
  };

  if (!user) return null;

  const pendingRequests = requests.filter((r) => r.status === 'pending').length;
  const approvedRequests = requests.filter((r) => r.status === 'approved').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Time Off</h1>
          <p className="text-gray-600 mt-1">Manage your time off requests and balances</p>
        </div>
        <button
          onClick={() => setShowRequestModal(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="h-5 w-5" />
          <span>Request Time Off</span>
        </button>
      </div>

      {/* Manager Info */}
      {user.managerName && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-900">
            <span className="font-semibold">Your Manager:</span> {user.managerName}
          </p>
        </div>
      )}

      {/* Balance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatsCard
          title="Vacation Days"
          value={user.ptoBalance}
          icon={Briefcase}
          color="blue"
        />
        <StatsCard
          title="Sick Days"
          value={user.sickBalance}
          icon={Heart}
          color="red"
        />
        <StatsCard
          title="Personal Days"
          value={user.personalBalance}
          icon={Calendar}
          color="purple"
        />
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <StatsCard
          title="Pending Requests"
          value={pendingRequests}
          icon={Clock}
          color="yellow"
        />
        <StatsCard
          title="Approved Requests"
          value={approvedRequests}
          icon={Calendar}
          color="green"
        />
      </div>

      {/* Requests Table */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          My Requests
        </h2>
        <RequestsTable
          requests={requests}
          onCancel={handleCancelRequest}
          showActions={true}
          showUser={false}
        />
      </div>

      {/* Request Modal */}
      <Modal
        isOpen={showRequestModal}
        onClose={() => setShowRequestModal(false)}
        title="Request Time Off"
        maxWidth="lg"
      >
        <RequestForm
          onSuccess={handleRequestSuccess}
          onCancel={() => setShowRequestModal(false)}
        />
      </Modal>
    </div>
  );
}
