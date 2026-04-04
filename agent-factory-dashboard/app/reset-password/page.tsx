'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Sparkles, Lock, AlertCircle, CheckCircle, Mail } from 'lucide-react';

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isValidToken, setIsValidToken] = useState<boolean | null>(null);

  const token = searchParams.get('token');
  const email = searchParams.get('email');

  // Verify token on mount
  useEffect(() => {
    if (!token || !email) {
      console.log('Reset password: No token or email in URL');
      setIsValidToken(false);
      return;
    }

    // Decode email in case it's URL-encoded
    const decodedEmail = decodeURIComponent(email);
    console.log('Reset password: Checking token for email:', decodedEmail);

    // Check if token exists in localStorage
    const resetTokens = JSON.parse(localStorage.getItem('resetTokens') || '{}');
    console.log('Reset password: All stored reset tokens:', resetTokens);
    
    const storedToken = resetTokens[decodedEmail];
    console.log('Reset password: Stored token for this email:', storedToken);

    if (storedToken && storedToken.token === token) {
      // Check if token is expired (1 hour expiry)
      const now = Date.now();
      const expiresAt = storedToken.expiresAt;
      console.log('Reset password: Token matches, checking expiry. Now:', now, 'Expires:', expiresAt);

      if (now < expiresAt) {
        console.log('Reset password: Token is valid!');
        setIsValidToken(true);
      } else {
        // Token expired
        console.log('Reset password: Token has expired');
        delete resetTokens[decodedEmail];
        localStorage.setItem('resetTokens', JSON.stringify(resetTokens));
        setIsValidToken(false);
      }
    } else {
      console.log('Reset password: Token does not match or not found');
      setIsValidToken(false);
    }
  }, [token, email]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Store the new password (in real app, this would be an API call)
    const users = JSON.parse(localStorage.getItem('users') || '{}');
    users[email as string] = { password, name: email?.split('@')[0] || 'User' };
    localStorage.setItem('users', JSON.stringify(users));

    // Remove used reset token
    const resetTokens = JSON.parse(localStorage.getItem('resetTokens') || '{}');
    delete resetTokens[email as string];
    localStorage.setItem('resetTokens', JSON.stringify(resetTokens));

    setSuccess(true);

    // Redirect to login after 2 seconds
    setTimeout(() => {
      router.push('/login');
    }, 2000);
  };

  if (!token || !email) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center max-w-md p-8">
          <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4 mx-auto">
            <AlertCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
            Invalid Reset Link
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mb-6">
            This password reset link is invalid or incomplete.
          </p>
          <button
            onClick={() => router.push('/login')}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-all"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  if (isValidToken === false) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center max-w-md p-8">
          <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4 mx-auto">
            <AlertCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
            Link Expired or Invalid
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mb-6">
            This password reset link has expired or is invalid. Please request a new one.
          </p>
          
          {/* Demo Mode Bypass */}
          <div className="mb-6 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
            <p className="text-sm font-medium text-amber-900 dark:text-amber-100 mb-2">
              🛠 Demo Mode
            </p>
            <p className="text-xs text-amber-700 dark:text-amber-300 mb-3">
              The token doesn't match localStorage. This happens if you cleared storage or the link is from a previous request.
            </p>
            <button
              onClick={() => {
                // Create a valid token for demo purposes
                const demoEmail = email ? decodeURIComponent(email) : 'demo@example.com';
                const demoToken = token || 'demo-token';
                const resetTokens = JSON.parse(localStorage.getItem('resetTokens') || '{}');
                resetTokens[demoEmail] = {
                  token: demoToken,
                  expiresAt: Date.now() + (60 * 60 * 1000) // 1 hour
                };
                localStorage.setItem('resetTokens', JSON.stringify(resetTokens));
                window.location.reload();
              }}
              className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded-lg transition-all"
            >
              Create Demo Token & Continue
            </button>
          </div>
          
          <button
            onClick={() => router.push('/login')}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-all"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  if (isValidToken === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-slate-600 dark:text-slate-400">Verifying link...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-indigo-600 to-indigo-700 items-center justify-center p-12">
        <div className="max-w-md text-white">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
              <Sparkles className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Agent Factory</h1>
              <p className="text-indigo-200">Digital FTE Management</p>
            </div>
          </div>
          <h2 className="text-4xl font-bold mb-6">
            Reset your password
          </h2>
          <p className="text-lg text-indigo-100">
            Create a new secure password for your account
          </p>
        </div>
      </div>

      {/* Right Side - Reset Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-slate-50 dark:bg-slate-900">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-700 flex items-center justify-center shadow-md mb-4">
              <Lock className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
              Create new password
            </h2>
            <p className="text-slate-500 dark:text-slate-400">
              Enter a new password for <span className="font-medium text-indigo-600 dark:text-indigo-400">{email}</span>
            </p>
          </div>

          {success && (
            <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-green-800 dark:text-green-200 font-medium">Password reset successful!</p>
                <p className="text-xs text-green-700 dark:text-green-300 mt-1">Redirecting to login...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* New Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                New password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:border-transparent dark:text-white transition-all"
                  placeholder="••••••••"
                  required
                  disabled={success}
                />
              </div>
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                Must be at least 6 characters
              </p>
            </div>

            {/* Confirm Password Field */}
            <div>
              <label htmlFor="confirm-password" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Confirm password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  id="confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:border-transparent dark:text-white transition-all"
                  placeholder="••••••••"
                  required
                  disabled={success}
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || success}
              className="w-full py-3 px-4 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white font-medium rounded-lg shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Resetting password...
                </>
              ) : (
                'Reset Password'
              )}
            </button>
          </form>

          <div className="mt-8 text-center">
            <button
              onClick={() => router.push('/login')}
              className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
            >
              ← Back to login
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
