'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useInvitationStore } from '@/store/invitationStore';
import { Calendar } from 'lucide-react';
import LoadingSpinner from '@/components/LoadingSpinner';
import toast from 'react-hot-toast';

export default function SignUpPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const invitationId = searchParams.get('invitation');

  const { signUp, user, initialized } = useAuthStore();
  const { getInvitationById } = useInvitationStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [invitationData, setInvitationData] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (initialized && user) {
      router.push('/dashboard');
      return;
    }

    const loadInvitation = async () => {
      if (!invitationId) {
        toast.error('Invalid invitation link');
        router.push('/login');
        return;
      }

      try {
        const invitation = await getInvitationById(invitationId);

        if (!invitation) {
          toast.error('Invitation not found');
          router.push('/login');
          return;
        }

        if (invitation.status !== 'pending') {
          toast.error('This invitation has already been used or expired');
          router.push('/login');
          return;
        }

        if (new Date() > invitation.expiresAt) {
          toast.error('This invitation has expired');
          router.push('/login');
          return;
        }

        setInvitationData(invitation);
        setEmail(invitation.email);
        setIsLoading(false);
      } catch (error: any) {
        toast.error(error.message || 'Failed to load invitation');
        router.push('/login');
      }
    };

    if (initialized && !user) {
      loadInvitation();
    }
  }, [invitationId, user, initialized, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    if (!invitationId) {
      toast.error('Invalid invitation');
      return;
    }

    setIsSubmitting(true);

    try {
      await signUp(email, password, invitationId);
      toast.success('Account created successfully');
      router.push('/dashboard');
    } catch (error: any) {
      toast.error(error.message || 'Failed to create account');
      setIsSubmitting(false);
    }
  };

  if (!initialized || isLoading || (initialized && user)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 px-4">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Calendar className="h-16 w-16 text-primary-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            TimeOff Manager
          </h1>
          <p className="text-gray-600">Create Your Account</p>
        </div>

        {/* Sign Up Card */}
        <div className="bg-white rounded-lg shadow-xl p-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Welcome!
          </h2>
          <p className="text-gray-600 mb-6">
            You've been invited to join as{' '}
            <span className="font-semibold">{invitationData?.name}</span>
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                className="input-field bg-gray-50"
                disabled
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Create Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                required
                disabled={isSubmitting}
                placeholder="Min. 6 characters"
                minLength={6}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input-field"
                required
                disabled={isSubmitting}
                placeholder="Re-enter password"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary w-full"
            >
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <a
                href="/login"
                className="text-primary-600 hover:text-primary-700 font-medium"
              >
                Sign In
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
