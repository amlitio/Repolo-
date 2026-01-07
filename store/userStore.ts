import { create } from 'zustand';
import {
  collection,
  doc,
  getDocs,
  getDoc,
  updateDoc,
  query,
  where,
  Timestamp,
} from 'firebase/firestore';
import { db } from '@/lib/firebase';
import { User } from '@/types';

interface UserState {
  users: User[];
  managers: User[];
  loading: boolean;
  fetchAllUsers: () => Promise<void>;
  fetchManagers: () => Promise<void>;
  fetchTeamMembers: (managerId: string) => Promise<void>;
  updateUserBalance: (
    userId: string,
    field: 'ptoBalance' | 'sickBalance' | 'personalBalance',
    value: number
  ) => Promise<void>;
  updateUserManager: (userId: string, managerId: string, managerName: string) => Promise<void>;
}

export const useUserStore = create<UserState>((set, get) => ({
  users: [],
  managers: [],
  loading: false,

  fetchAllUsers: async () => {
    try {
      set({ loading: true });

      const querySnapshot = await getDocs(collection(db, 'users'));
      const users: User[] = [];

      querySnapshot.forEach((doc) => {
        const data = doc.data();
        users.push({
          id: doc.id,
          ...data,
          createdAt: data.createdAt?.toDate(),
          updatedAt: data.updatedAt?.toDate(),
        } as User);
      });

      set({ users, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to fetch users');
    }
  },

  fetchManagers: async () => {
    try {
      set({ loading: true });

      const q = query(collection(db, 'users'), where('role', '==', 'manager'));
      const querySnapshot = await getDocs(q);
      const managers: User[] = [];

      querySnapshot.forEach((doc) => {
        const data = doc.data();
        managers.push({
          id: doc.id,
          ...data,
          createdAt: data.createdAt?.toDate(),
          updatedAt: data.updatedAt?.toDate(),
        } as User);
      });

      set({ managers, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to fetch managers');
    }
  },

  fetchTeamMembers: async (managerId) => {
    try {
      set({ loading: true });

      const q = query(collection(db, 'users'), where('managerId', '==', managerId));
      const querySnapshot = await getDocs(q);
      const users: User[] = [];

      querySnapshot.forEach((doc) => {
        const data = doc.data();
        users.push({
          id: doc.id,
          ...data,
          createdAt: data.createdAt?.toDate(),
          updatedAt: data.updatedAt?.toDate(),
        } as User);
      });

      set({ users, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to fetch team members');
    }
  },

  updateUserBalance: async (userId, field, value) => {
    try {
      set({ loading: true });

      await updateDoc(doc(db, 'users', userId), {
        [field]: value,
        updatedAt: Timestamp.fromDate(new Date()),
      });

      // Update local state
      const users = get().users.map((user) =>
        user.id === userId ? { ...user, [field]: value, updatedAt: new Date() } : user
      );

      set({ users, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to update balance');
    }
  },

  updateUserManager: async (userId, managerId, managerName) => {
    try {
      set({ loading: true });

      await updateDoc(doc(db, 'users', userId), {
        managerId,
        managerName,
        updatedAt: Timestamp.fromDate(new Date()),
      });

      // Update local state
      const users = get().users.map((user) =>
        user.id === userId
          ? { ...user, managerId, managerName, updatedAt: new Date() }
          : user
      );

      set({ users, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to update manager');
    }
  },
}));
