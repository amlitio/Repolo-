import { create } from 'zustand';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User as FirebaseUser,
} from 'firebase/auth';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { auth, db } from '@/lib/firebase';
import { User } from '@/types';

interface AuthState {
  user: User | null;
  firebaseUser: FirebaseUser | null;
  loading: boolean;
  initialized: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, invitationId: string) => Promise<void>;
  signOut: () => Promise<void>;
  initializeAuth: () => void;
  updateUser: (userData: Partial<User>) => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  firebaseUser: null,
  loading: true,
  initialized: false,

  initializeAuth: () => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        try {
          const userDoc = await getDoc(doc(db, 'users', firebaseUser.uid));
          if (userDoc.exists()) {
            const userData = userDoc.data();
            set({
              user: {
                id: firebaseUser.uid,
                ...userData,
                createdAt: userData.createdAt?.toDate(),
                updatedAt: userData.updatedAt?.toDate(),
              } as User,
              firebaseUser,
              loading: false,
              initialized: true,
            });
          } else {
            set({ user: null, firebaseUser: null, loading: false, initialized: true });
          }
        } catch (error) {
          console.error('Error fetching user data:', error);
          set({ user: null, firebaseUser: null, loading: false, initialized: true });
        }
      } else {
        set({ user: null, firebaseUser: null, loading: false, initialized: true });
      }
    });

    return unsubscribe;
  },

  signIn: async (email: string, password: string) => {
    try {
      set({ loading: true });
      await signInWithEmailAndPassword(auth, email, password);
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to sign in');
    }
  },

  signUp: async (email: string, password: string, invitationId: string) => {
    try {
      set({ loading: true });

      // Get invitation details
      const invitationDoc = await getDoc(doc(db, 'invitations', invitationId));
      if (!invitationDoc.exists()) {
        throw new Error('Invalid invitation');
      }

      const invitation = invitationDoc.data();
      if (invitation.status !== 'pending') {
        throw new Error('Invitation already used or expired');
      }

      if (invitation.email !== email) {
        throw new Error('Email does not match invitation');
      }

      // Create user account
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const userId = userCredential.user.uid;

      // Create user document
      const userData: Omit<User, 'id'> = {
        email: invitation.email,
        name: invitation.name,
        role: invitation.role,
        managerId: invitation.managerId,
        managerName: invitation.managerName,
        ptoBalance: invitation.initialPtoBalance,
        sickBalance: invitation.initialSickBalance,
        personalBalance: invitation.initialPersonalBalance,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      await setDoc(doc(db, 'users', userId), {
        ...userData,
        createdAt: new Date(),
        updatedAt: new Date(),
      });

      // Update invitation status
      await setDoc(
        doc(db, 'invitations', invitationId),
        { status: 'accepted', acceptedAt: new Date() },
        { merge: true }
      );

      set({ loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.message || 'Failed to sign up');
    }
  },

  signOut: async () => {
    try {
      await firebaseSignOut(auth);
      set({ user: null, firebaseUser: null });
    } catch (error: any) {
      throw new Error(error.message || 'Failed to sign out');
    }
  },

  updateUser: async (userData: Partial<User>) => {
    const { user } = get();
    if (!user) return;

    try {
      const updatedData = {
        ...userData,
        updatedAt: new Date(),
      };

      await setDoc(doc(db, 'users', user.id), updatedData, { merge: true });

      set({
        user: {
          ...user,
          ...userData,
          updatedAt: new Date(),
        },
      });
    } catch (error: any) {
      throw new Error(error.message || 'Failed to update user');
    }
  },
}));
