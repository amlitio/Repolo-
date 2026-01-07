import { create } from 'zustand';
import {
  collection,
  doc,
  addDoc,
  getDocs,
  getDoc,
  query,
  where,
  Timestamp,
  deleteDoc,
} from 'firebase/firestore';
import { db } from '@/lib/firebase';
import { Invitation, UserRole } from '@/types';

interface InvitationState {
  invitations: Invitation[];
  loading: boolean;
  createInvitation: (
    email: string,
    name: string,
    role: UserRole,
    managerId: string | undefined,
    managerName: string | undefined,
    initialPtoBalance: number,
    initialSickBalance: number,
    initialPersonalBalance: number,
    invitedBy: string,
    invitedByName: string
  ) => Promise<string>;
  fetchInvitations: () => Promise<void>;
  fetchPendingInvitations: () => Promise<void>;
  getInvitationById: (invitationId: string) => Promise<Invitation | null>;
  deleteInvitation: (invitationId: string) => Promise<void>;
}

export const useInvitationStore = create<InvitationState>((set, get) => ({
  invitations: [],
  loading: false,

  createInvitation: async (
    email,
    name,
    role,
    managerId,
    managerName,
    initialPtoBalance,
    initialSickBalance,
    initialPersonalBalance,
    invitedBy,
    invitedByName
  ) => {
    try {
      set({ loading: true });

      // Check if email already exists
      const usersQuery = query(collection(db, 'users'), where('email', '==', email));
      const usersSnapshot = await getDocs(usersQuery);

      if (!usersSnapshot.empty) {
        throw new Error('User with this email already exists');
      }

      // Check if invitation already exists
      const invitationsQuery = query(
        collection(db, 'invitations'),
        where('email', '==', email),
        where('status', '==', 'pending')
      );
      const invitationsSnapshot = await getDocs(invitationsQuery);

      if (!invitationsSnapshot.empty) {
        throw new Error('Invitation already sent to this email');
      }

      const invitationData = {
        email,
        name,
        role,
        managerId: managerId || null,
        managerName: managerName || null,
        initialPtoBalance,
        initialSickBalance,
        initialPersonalBalance,
        invitedBy,
        invitedByName,
        status: 'pending',
        createdAt: Timestamp.fromDate(new Date()),
        expiresAt: Timestamp.fromDate(
          new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
        ), // 7 days
      };

      const docRef = await addDoc(collection(db, 'invitations'), invitationData);

      set({ loading: false });
      return docRef.id;
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to create invitation');
    }
  },

  fetchInvitations: async () => {
    try {
      set({ loading: true });

      const querySnapshot = await getDocs(collection(db, 'invitations'));
      const invitations: Invitation[] = [];

      querySnapshot.forEach((doc) => {
        const data = doc.data();
        invitations.push({
          id: doc.id,
          ...data,
          createdAt: data.createdAt?.toDate(),
          expiresAt: data.expiresAt?.toDate(),
        } as Invitation);
      });

      set({ invitations, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to fetch invitations');
    }
  },

  fetchPendingInvitations: async () => {
    try {
      set({ loading: true });

      const q = query(
        collection(db, 'invitations'),
        where('status', '==', 'pending')
      );
      const querySnapshot = await getDocs(q);
      const invitations: Invitation[] = [];

      querySnapshot.forEach((doc) => {
        const data = doc.data();
        invitations.push({
          id: doc.id,
          ...data,
          createdAt: data.createdAt?.toDate(),
          expiresAt: data.expiresAt?.toDate(),
        } as Invitation);
      });

      set({ invitations, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to fetch invitations');
    }
  },

  getInvitationById: async (invitationId) => {
    try {
      const invitationDoc = await getDoc(doc(db, 'invitations', invitationId));

      if (!invitationDoc.exists()) {
        return null;
      }

      const data = invitationDoc.data();
      return {
        id: invitationDoc.id,
        ...data,
        createdAt: data.createdAt?.toDate(),
        expiresAt: data.expiresAt?.toDate(),
      } as Invitation;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch invitation');
    }
  },

  deleteInvitation: async (invitationId) => {
    try {
      set({ loading: true });

      await deleteDoc(doc(db, 'invitations', invitationId));

      const invitations = get().invitations.filter((inv) => inv.id !== invitationId);
      set({ invitations, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to delete invitation');
    }
  },
}));
