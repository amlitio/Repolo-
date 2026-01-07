import { create } from 'zustand';
import {
  collection,
  doc,
  addDoc,
  updateDoc,
  deleteDoc,
  getDocs,
  getDoc,
  query,
  where,
  orderBy,
  Timestamp,
} from 'firebase/firestore';
import { db } from '@/lib/firebase';
import { TimeOffRequest, LeaveType, RequestStatus } from '@/types';
import { calculateBusinessDays } from '@/lib/utils';

interface RequestState {
  requests: TimeOffRequest[];
  loading: boolean;
  createRequest: (
    userId: string,
    userName: string,
    userEmail: string,
    managerId: string | undefined,
    managerName: string | undefined,
    leaveType: LeaveType,
    startDate: Date,
    endDate: Date,
    reason: string
  ) => Promise<void>;
  fetchUserRequests: (userId: string) => Promise<void>;
  fetchManagerRequests: (managerId: string) => Promise<void>;
  fetchAllRequests: () => Promise<void>;
  updateRequestStatus: (
    requestId: string,
    status: RequestStatus,
    comments?: string,
    approverName?: string
  ) => Promise<void>;
  cancelRequest: (requestId: string) => Promise<void>;
  deductBalance: (
    userId: string,
    leaveType: LeaveType,
    days: number
  ) => Promise<void>;
}

export const useRequestStore = create<RequestState>((set, get) => ({
  requests: [],
  loading: false,

  createRequest: async (
    userId,
    userName,
    userEmail,
    managerId,
    managerName,
    leaveType,
    startDate,
    endDate,
    reason
  ) => {
    try {
      set({ loading: true });

      const totalDays = calculateBusinessDays(startDate, endDate);

      const requestData = {
        userId,
        userName,
        userEmail,
        managerId,
        managerName,
        leaveType,
        startDate: Timestamp.fromDate(startDate),
        endDate: Timestamp.fromDate(endDate),
        totalDays,
        reason,
        status: 'pending' as RequestStatus,
        createdAt: Timestamp.fromDate(new Date()),
        updatedAt: Timestamp.fromDate(new Date()),
      };

      await addDoc(collection(db, 'requests'), requestData);

      set({ loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to create request');
    }
  },

  fetchUserRequests: async (userId) => {
    try {
      set({ loading: true });

      const q = query(
        collection(db, 'requests'),
        where('userId', '==', userId),
        orderBy('createdAt', 'desc')
      );

      const querySnapshot = await getDocs(q);
      const requests: TimeOffRequest[] = [];

      querySnapshot.forEach((doc) => {
        const data = doc.data();
        requests.push({
          id: doc.id,
          ...data,
          startDate: data.startDate?.toDate(),
          endDate: data.endDate?.toDate(),
          createdAt: data.createdAt?.toDate(),
          updatedAt: data.updatedAt?.toDate(),
          approvedByManagerAt: data.approvedByManagerAt?.toDate(),
          approvedByAdminAt: data.approvedByAdminAt?.toDate(),
          rejectedAt: data.rejectedAt?.toDate(),
        } as TimeOffRequest);
      });

      set({ requests, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to fetch requests');
    }
  },

  fetchManagerRequests: async (managerId) => {
    try {
      set({ loading: true });

      const q = query(
        collection(db, 'requests'),
        where('managerId', '==', managerId),
        orderBy('createdAt', 'desc')
      );

      const querySnapshot = await getDocs(q);
      const requests: TimeOffRequest[] = [];

      querySnapshot.forEach((doc) => {
        const data = doc.data();
        requests.push({
          id: doc.id,
          ...data,
          startDate: data.startDate?.toDate(),
          endDate: data.endDate?.toDate(),
          createdAt: data.createdAt?.toDate(),
          updatedAt: data.updatedAt?.toDate(),
          approvedByManagerAt: data.approvedByManagerAt?.toDate(),
          approvedByAdminAt: data.approvedByAdminAt?.toDate(),
          rejectedAt: data.rejectedAt?.toDate(),
        } as TimeOffRequest);
      });

      set({ requests, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to fetch requests');
    }
  },

  fetchAllRequests: async () => {
    try {
      set({ loading: true });

      const q = query(collection(db, 'requests'), orderBy('createdAt', 'desc'));

      const querySnapshot = await getDocs(q);
      const requests: TimeOffRequest[] = [];

      querySnapshot.forEach((doc) => {
        const data = doc.data();
        requests.push({
          id: doc.id,
          ...data,
          startDate: data.startDate?.toDate(),
          endDate: data.endDate?.toDate(),
          createdAt: data.createdAt?.toDate(),
          updatedAt: data.updatedAt?.toDate(),
          approvedByManagerAt: data.approvedByManagerAt?.toDate(),
          approvedByAdminAt: data.approvedByAdminAt?.toDate(),
          rejectedAt: data.rejectedAt?.toDate(),
        } as TimeOffRequest);
      });

      set({ requests, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to fetch requests');
    }
  },

  updateRequestStatus: async (requestId, status, comments, approverName) => {
    try {
      set({ loading: true });

      const updateData: any = {
        status,
        updatedAt: Timestamp.fromDate(new Date()),
      };

      if (status === 'manager_approved') {
        updateData.managerComments = comments;
        updateData.approvedByManagerAt = Timestamp.fromDate(new Date());
      } else if (status === 'approved') {
        updateData.adminComments = comments;
        updateData.approvedByAdminAt = Timestamp.fromDate(new Date());

        // Deduct balance
        const requestDoc = await getDoc(doc(db, 'requests', requestId));
        if (requestDoc.exists()) {
          const request = requestDoc.data();
          await get().deductBalance(
            request.userId,
            request.leaveType,
            request.totalDays
          );
        }
      } else if (status === 'rejected') {
        updateData.rejectedBy = approverName;
        updateData.rejectedAt = Timestamp.fromDate(new Date());
        updateData.adminComments = comments;
      }

      await updateDoc(doc(db, 'requests', requestId), updateData);

      // Update local state
      const requests = get().requests.map((req) =>
        req.id === requestId ? { ...req, ...updateData, updatedAt: new Date() } : req
      );

      set({ requests, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to update request');
    }
  },

  cancelRequest: async (requestId) => {
    try {
      set({ loading: true });

      await deleteDoc(doc(db, 'requests', requestId));

      const requests = get().requests.filter((req) => req.id !== requestId);
      set({ requests, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to cancel request');
    }
  },

  deductBalance: async (userId, leaveType, days) => {
    try {
      const userDoc = await getDoc(doc(db, 'users', userId));
      if (!userDoc.exists()) {
        throw new Error('User not found');
      }

      const userData = userDoc.data();
      const balanceField =
        leaveType === 'vacation'
          ? 'ptoBalance'
          : leaveType === 'sick'
          ? 'sickBalance'
          : 'personalBalance';

      const currentBalance = userData[balanceField] || 0;
      const newBalance = Math.max(0, currentBalance - days);

      await updateDoc(doc(db, 'users', userId), {
        [balanceField]: newBalance,
        updatedAt: Timestamp.fromDate(new Date()),
      });
    } catch (error: any) {
      throw new Error(error.message || 'Failed to deduct balance');
    }
  },
}));
