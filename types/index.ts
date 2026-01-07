export type UserRole = 'admin' | 'manager' | 'employee';

export type LeaveType = 'vacation' | 'sick' | 'personal';

export type RequestStatus = 'pending' | 'manager_approved' | 'approved' | 'rejected';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  managerId?: string;
  managerName?: string;
  ptoBalance: number;
  sickBalance: number;
  personalBalance: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface TimeOffRequest {
  id: string;
  userId: string;
  userName: string;
  userEmail: string;
  managerId?: string;
  managerName?: string;
  leaveType: LeaveType;
  startDate: Date;
  endDate: Date;
  totalDays: number;
  reason: string;
  status: RequestStatus;
  managerComments?: string;
  adminComments?: string;
  approvedByManagerAt?: Date;
  approvedByAdminAt?: Date;
  rejectedBy?: string;
  rejectedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface Invitation {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  managerId?: string;
  managerName?: string;
  initialPtoBalance: number;
  initialSickBalance: number;
  initialPersonalBalance: number;
  invitedBy: string;
  invitedByName: string;
  status: 'pending' | 'accepted' | 'expired';
  createdAt: Date;
  expiresAt: Date;
}

export interface NotificationPayload {
  to: string;
  subject: string;
  body: string;
  requestId?: string;
  userId?: string;
}

export interface DashboardStats {
  totalRequests: number;
  pendingRequests: number;
  approvedRequests: number;
  rejectedRequests: number;
  totalPtoBalance: number;
  totalSickBalance: number;
  totalPersonalBalance: number;
}
