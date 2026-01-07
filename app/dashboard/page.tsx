'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useRequestStore } from '@/store/requestStore';
import { useUserStore } from '@/store/userStore';
import { useInvitationStore } from '@/store/invitationStore';
import Navbar from '@/components/Navbar';
import LoadingSpinner from '@/components/LoadingSpinner';
import EmployeeDashboard from '@/components/dashboards/EmployeeDashboard';
import ManagerDashboard from '@/components/dashboards/ManagerDashboard';
import AdminDashboard from '@/components/dashboards/AdminDashboard';

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading, initialized } = useAuthStore();
  const { fetchUserRequests, fetchManagerRequests, fetchAllRequests } = useRequestStore();
  const { fetchAllUsers, fetchTeamMembers } = useUserStore();
  const { fetchPendingInvitations } = useInvitationStore();

  const [isLoadingData, setIsLoadingData] = useState(true);

  useEffect(() => {
    if (!initialized) return;

    if (!user) {
      router.push('/login');
      return;
    }

    const loadData = async () => {
      try {
        setIsLoadingData(true);

        if (user.role === 'employee') {
          await fetchUserRequests(user.id);
        } else if (user.role === 'manager') {
          await Promise.all([
            fetchManagerRequests(user.id),
            fetchTeamMembers(user.id),
          ]);
        } else if (user.role === 'admin') {
          await Promise.all([
            fetchAllRequests(),
            fetchAllUsers(),
            fetchPendingInvitations(),
          ]);
        }

        setIsLoadingData(false);
      } catch (error) {
        console.error('Error loading dashboard data:', error);
        setIsLoadingData(false);
      }
    };

    loadData();
  }, [user, initialized, router]);

  if (!initialized || loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoadingData ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <>
            {user.role === 'employee' && <EmployeeDashboard />}
            {user.role === 'manager' && <ManagerDashboard />}
            {user.role === 'admin' && <AdminDashboard />}
          </>
        )}
      </main>
    </div>
  );
}
