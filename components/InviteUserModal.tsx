'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useInvitationStore } from '@/store/invitationStore';
import { useUserStore } from '@/store/userStore';
import { UserRole } from '@/types';
import Modal from './Modal';
import LoadingSpinner from './LoadingSpinner';
import toast from 'react-hot-toast';

interface InviteUserModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function InviteUserModal({ isOpen, onClose }: InviteUserModalProps) {
  const { user } = useAuthStore();
  const { createInvitation, loading } = useInvitationStore();
  const { managers, fetchManagers } = useUserStore();

  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState<UserRole>('employee');
  const [managerId, setManagerId] = useState('');
  const [ptoBalance, setPtoBalance] = useState(15);
  const [sickBalance, setSickBalance] = useState(10);
  const [personalBalance, setPersonalBalance] = useState(5);

  useEffect(() => {
    if (isOpen && user?.role === 'admin') {
      fetchManagers();
    }
  }, [isOpen, user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!user) {
      toast.error('User not authenticated');
      return;
    }

    if (role === 'employee' && !managerId) {
      toast.error('Please select a manager for the employee');
      return;
    }

    try {
      const selectedManager = managers.find((m) => m.id === managerId);

      await createInvitation(
        email,
        name,
        role,
        role === 'employee' ? managerId : undefined,
        role === 'employee' ? selectedManager?.name : undefined,
        ptoBalance,
        sickBalance,
        personalBalance,
        user.id,
        user.name
      );

      toast.success(`Invitation sent to ${email}`);

      // Reset form
      setEmail('');
      setName('');
      setRole('employee');
      setManagerId('');
      setPtoBalance(15);
      setSickBalance(10);
      setPersonalBalance(5);

      onClose();
    } catch (error: any) {
      toast.error(error.message || 'Failed to send invitation');
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Invite New User" maxWidth="lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input-field"
              required
              disabled={loading}
              placeholder="John Doe"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field"
              required
              disabled={loading}
              placeholder="john@company.com"
            />
          </div>
        </div>

        {/* Role */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Role
          </label>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as UserRole)}
            className="input-field"
            disabled={loading}
          >
            <option value="employee">Employee</option>
            <option value="manager">Manager</option>
            {user?.role === 'admin' && <option value="admin">Admin</option>}
          </select>
        </div>

        {/* Manager Selection (for employees only) */}
        {role === 'employee' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assign Manager
            </label>
            <select
              value={managerId}
              onChange={(e) => setManagerId(e.target.value)}
              className="input-field"
              required
              disabled={loading}
            >
              <option value="">Select a manager...</option>
              {managers.map((manager) => (
                <option key={manager.id} value={manager.id}>
                  {manager.name} ({manager.email})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Initial Balances */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-3">
            Initial Time Off Balances
          </p>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">
                Vacation (PTO)
              </label>
              <input
                type="number"
                value={ptoBalance}
                onChange={(e) => setPtoBalance(Number(e.target.value))}
                className="input-field"
                min="0"
                required
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">
                Sick Leave
              </label>
              <input
                type="number"
                value={sickBalance}
                onChange={(e) => setSickBalance(Number(e.target.value))}
                className="input-field"
                min="0"
                required
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">
                Personal Leave
              </label>
              <input
                type="number"
                value={personalBalance}
                onChange={(e) => setPersonalBalance(Number(e.target.value))}
                className="input-field"
                min="0"
                required
                disabled={loading}
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex space-x-3">
          <button type="submit" disabled={loading} className="btn-primary flex-1">
            {loading ? <LoadingSpinner size="sm" /> : 'Send Invitation'}
          </button>
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="btn-secondary flex-1"
          >
            Cancel
          </button>
        </div>
      </form>
    </Modal>
  );
}
