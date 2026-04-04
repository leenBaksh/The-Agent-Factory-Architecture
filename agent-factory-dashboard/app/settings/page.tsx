'use client';

import React, { useState } from 'react';
import { Header } from '@/components/Header';
import { useAuth } from '@/contexts/AuthContext';
import {
  Settings,
  User,
  Bell,
  Shield,
  Palette,
  Globe,
  Database,
  Key,
  Webhook,
  Mail,
  MessageSquare,
  Save,
  RotateCcw,
  Moon,
  Sun,
  Monitor,
  Check,
  ChevronRight,
  Lock,
  Eye,
  EyeOff,
  Copy,
  RefreshCw,
  Trash2,
  Plus,
  ExternalLink,
  AlertCircle,
  Info,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';

type TabType = 'general' | 'profile' | 'notifications' | 'appearance' | 'integrations' | 'api' | 'security';

export default function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('general');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showSaveNotification, setShowSaveNotification] = useState(false);
  const [showModal, setShowModal] = useState<'none' | 'avatar' | 'apiKey' | '2fa' | 'password' | 'connectIntegration' | 'configureIntegration' | 'requestIntegration'>('none');
  const [selectedIntegration, setSelectedIntegration] = useState<any>(null);

  // Sync profile with authenticated user
  React.useEffect(() => {
    if (user) {
      setProfile(prev => ({
        ...prev,
        name: user.name || prev.name,
        email: user.email || prev.email,
        role: user.role || prev.role,
      }));
    }
  }, [user]);

  // Load saved avatar from localStorage on mount
  React.useEffect(() => {
    const savedAvatar = localStorage.getItem('userAvatar');
    if (savedAvatar) {
      setProfile(prev => ({ ...prev, avatar: savedAvatar }));
    }
  }, []);

  // General Settings
  const [generalSettings, setGeneralSettings] = useState({
    organizationName: 'Acme Corporation',
    timezone: 'America/New_York',
    language: 'en',
    dateFormat: 'MM/DD/YYYY',
    weekStart: 'sunday',
  });

  // Profile Settings - will be updated from AuthContext
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    role: '',
    avatar: '',
  });

  // Notification Settings
  const [notifications, setNotifications] = useState({
    emailNotifications: true,
    pushNotifications: true,
    ticketAssigned: true,
    ticketResolved: true,
    slaBreaches: true,
    newMessages: true,
    dailyDigest: false,
    weeklyReport: true,
  });

  // Appearance Settings
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
  const [compactMode, setCompactMode] = useState(false);
  const [showAvatars, setShowAvatars] = useState(true);

  // Integrations
  const [integrations, setIntegrations] = useState([
    { id: '1', name: 'Slack', enabled: true, icon: MessageSquare, status: 'connected' },
    { id: '2', name: 'Gmail', enabled: true, icon: Mail, status: 'connected' },
    { id: '3', name: 'WhatsApp', enabled: false, icon: MessageSquare, status: 'disconnected' },
    { id: '4', name: 'Webhooks', enabled: true, icon: Webhook, status: 'configured' },
  ]);

  // API Keys
  const [apiKeys, setApiKeys] = useState([
    { id: '1', name: 'Production Key', key: 'sk_live_••••••••••••1234', created: '2025-06-15', lastUsed: '2026-04-02' },
    { id: '2', name: 'Development Key', key: 'sk_test_••••••••••••5678', created: '2025-08-20', lastUsed: '2026-04-01' },
  ]);

  const tabs: { id: TabType; label: string; icon: React.ElementType }[] = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'integrations', label: 'Integrations', icon: Webhook },
    { id: 'api', label: 'API Keys', icon: Key },
    { id: 'security', label: 'Security', icon: Shield },
  ];

  const handleSave = () => {
    // Save profile to localStorage and update AuthContext
    localStorage.setItem('user', JSON.stringify({
      id: '1',
      email: profile.email,
      name: profile.name,
      role: profile.role,
    }));
    
    setHasUnsavedChanges(false);
    setShowSaveNotification(true);
    setTimeout(() => setShowSaveNotification(false), 3000);
  };

  const handleReset = () => {
    // In real app, would reset to defaults
    setHasUnsavedChanges(false);
  };

  return (
    <>
      <Header title="Settings" />
      <main className="flex-1 overflow-y-auto bg-zinc-50 p-6 dark:bg-zinc-950">
        <div className="mx-auto max-w-5xl">
          {/* Header with Save/Reset */}
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                Configuration & Preferences
              </h2>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Manage your account settings and preferences
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleReset}
                className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
              >
                <RotateCcw className="h-4 w-4" />
                Reset
              </button>
              <button
                onClick={handleSave}
                disabled={!hasUnsavedChanges}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Save className="h-4 w-4" />
                Save Changes
              </button>
            </div>
          </div>

          {/* Save Notification */}
          {showSaveNotification && (
            <div className="mb-6 flex items-center gap-3 rounded-lg bg-green-50 p-4 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
              <Check className="h-5 w-5 text-green-600 dark:text-green-400" />
              <p className="text-sm font-medium text-green-800 dark:text-green-200">
                Settings saved successfully!
              </p>
            </div>
          )}

          <div className="flex gap-6">
            {/* Sidebar Navigation */}
            <nav className="hidden w-56 shrink-0 space-y-1 md:block">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={cn(
                      'flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                      activeTab === tab.id
                        ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-900/20 dark:text-indigo-400'
                        : 'text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800'
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="h-4 w-4" />
                      {tab.label}
                    </div>
                    {activeTab === tab.id && (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </button>
                );
              })}
            </nav>

            {/* Mobile Tab Selector */}
            <div className="md:hidden">
              <select
                value={activeTab}
                onChange={(e) => setActiveTab(e.target.value as TabType)}
                className="w-full rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm outline-none focus:border-indigo-500 dark:border-zinc-700 dark:bg-zinc-900"
              >
                {tabs.map((tab) => (
                  <option key={tab.id} value={tab.id}>
                    {tab.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Content Area */}
            <div className="flex-1 space-y-6">
              {activeTab === 'general' && (
                <SettingsSection title="General Settings">
                  <SettingGroup title="Organization">
                    <TextField
                      label="Organization Name"
                      value={generalSettings.organizationName}
                      onChange={(v) => {
                        setGeneralSettings({ ...generalSettings, organizationName: v });
                        setHasUnsavedChanges(true);
                      }}
                      placeholder="Your organization name"
                    />
                  </SettingGroup>

                  <SettingGroup title="Regional Settings">
                    <div className="grid gap-4 md:grid-cols-2">
                      <SelectField
                        label="Timezone"
                        value={generalSettings.timezone}
                        onChange={(v) => {
                          setGeneralSettings({ ...generalSettings, timezone: v });
                          setHasUnsavedChanges(true);
                        }}
                        options={[
                          { value: 'America/New_York', label: 'Eastern Time (ET)' },
                          { value: 'America/Chicago', label: 'Central Time (CT)' },
                          { value: 'America/Denver', label: 'Mountain Time (MT)' },
                          { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
                          { value: 'Europe/London', label: 'London (GMT)' },
                          { value: 'Europe/Paris', label: 'Paris (CET)' },
                          { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
                        ]}
                      />
                      <SelectField
                        label="Language"
                        value={generalSettings.language}
                        onChange={(v) => {
                          setGeneralSettings({ ...generalSettings, language: v });
                          setHasUnsavedChanges(true);
                        }}
                        options={[
                          { value: 'en', label: 'English' },
                          { value: 'es', label: 'Spanish' },
                          { value: 'fr', label: 'French' },
                          { value: 'de', label: 'German' },
                          { value: 'ja', label: 'Japanese' },
                        ]}
                      />
                    </div>
                    <div className="grid gap-4 md:grid-cols-2">
                      <SelectField
                        label="Date Format"
                        value={generalSettings.dateFormat}
                        onChange={(v) => {
                          setGeneralSettings({ ...generalSettings, dateFormat: v });
                          setHasUnsavedChanges(true);
                        }}
                        options={[
                          { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
                          { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
                          { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
                        ]}
                      />
                      <SelectField
                        label="Week Starts On"
                        value={generalSettings.weekStart}
                        onChange={(v) => {
                          setGeneralSettings({ ...generalSettings, weekStart: v });
                          setHasUnsavedChanges(true);
                        }}
                        options={[
                          { value: 'sunday', label: 'Sunday' },
                          { value: 'monday', label: 'Monday' },
                        ]}
                      />
                    </div>
                  </SettingGroup>
                </SettingsSection>
              )}

              {activeTab === 'profile' && (
                <SettingsSection title="Profile Settings">
                  <div className="flex items-center gap-6">
                    {profile.avatar ? (
                      <img
                        src={profile.avatar}
                        alt={profile.name}
                        className="h-20 w-20 rounded-full object-cover"
                      />
                    ) : (
                      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-2xl font-bold text-white">
                        {profile.name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                      </div>
                    )}
                    <div>
                      <button
                        onClick={() => setShowModal('avatar')}
                        className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                      >
                        Change Avatar
                      </button>
                      <p className="mt-2 text-xs text-zinc-500">
                        JPG, GIF or PNG. Max size 2MB.
                      </p>
                    </div>
                  </div>

                  <SettingGroup title="Personal Information">
                    <TextField
                      label="Full Name"
                      value={profile.name}
                      onChange={(v) => {
                        setProfile({ ...profile, name: v });
                        setHasUnsavedChanges(true);
                      }}
                      placeholder="Your name"
                    />
                    <TextField
                      label="Email Address"
                      type="email"
                      value={profile.email}
                      onChange={(v) => {
                        setProfile({ ...profile, email: v });
                        setHasUnsavedChanges(true);
                      }}
                      placeholder="your@email.com"
                    />
                    <div className="rounded-lg bg-zinc-50 p-4 dark:bg-zinc-800">
                      <div className="flex items-start gap-3">
                        <Lock className="h-5 w-5 text-zinc-400 shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                            Role: {profile.role}
                          </p>
                          <p className="text-xs text-zinc-500 dark:text-zinc-400">
                            Contact your administrator to change your role.
                          </p>
                        </div>
                      </div>
                    </div>
                  </SettingGroup>
                </SettingsSection>
              )}

              {activeTab === 'notifications' && (
                <SettingsSection title="Notification Preferences">
                  <SettingGroup title="Channels">
                    <ToggleField
                      label="Email Notifications"
                      description="Receive notifications via email"
                      icon={Mail}
                      checked={notifications.emailNotifications}
                      onChange={(v) => {
                        setNotifications({ ...notifications, emailNotifications: v });
                        setHasUnsavedChanges(true);
                      }}
                    />
                    <ToggleField
                      label="Push Notifications"
                      description="Receive browser push notifications"
                      icon={Bell}
                      checked={notifications.pushNotifications}
                      onChange={(v) => {
                        setNotifications({ ...notifications, pushNotifications: v });
                        setHasUnsavedChanges(true);
                      }}
                    />
                  </SettingGroup>

                  <SettingGroup title="Alerts">
                    <ToggleField
                      label="Ticket Assigned"
                      description="When a ticket is assigned to you"
                      checked={notifications.ticketAssigned}
                      onChange={(v) => {
                        setNotifications({ ...notifications, ticketAssigned: v });
                        setHasUnsavedChanges(true);
                      }}
                    />
                    <ToggleField
                      label="Ticket Resolved"
                      description="When a ticket you're following is resolved"
                      checked={notifications.ticketResolved}
                      onChange={(v) => {
                        setNotifications({ ...notifications, ticketResolved: v });
                        setHasUnsavedChanges(true);
                      }}
                    />
                    <ToggleField
                      label="SLA Breaches"
                      description="When a ticket is at risk of breaching SLA"
                      icon={AlertCircle}
                      checked={notifications.slaBreaches}
                      onChange={(v) => {
                        setNotifications({ ...notifications, slaBreaches: v });
                        setHasUnsavedChanges(true);
                      }}
                    />
                    <ToggleField
                      label="New Messages"
                      description="When you receive new messages"
                      icon={MessageSquare}
                      checked={notifications.newMessages}
                      onChange={(v) => {
                        setNotifications({ ...notifications, newMessages: v });
                        setHasUnsavedChanges(true);
                      }}
                    />
                  </SettingGroup>

                  <SettingGroup title="Digest & Reports">
                    <ToggleField
                      label="Daily Digest"
                      description="Summary of daily activity"
                      checked={notifications.dailyDigest}
                      onChange={(v) => {
                        setNotifications({ ...notifications, dailyDigest: v });
                        setHasUnsavedChanges(true);
                      }}
                    />
                    <ToggleField
                      label="Weekly Report"
                      description="Weekly performance summary"
                      checked={notifications.weeklyReport}
                      onChange={(v) => {
                        setNotifications({ ...notifications, weeklyReport: v });
                        setHasUnsavedChanges(true);
                      }}
                    />
                  </SettingGroup>
                </SettingsSection>
              )}

              {activeTab === 'appearance' && (
                <SettingsSection title="Appearance Settings">
                  <SettingGroup title="Theme">
                    <div className="grid gap-3 md:grid-cols-3">
                      <ThemeOption
                        value="light"
                        label="Light"
                        icon={Sun}
                        current={theme}
                        onChange={(v) => {
                          setTheme(v);
                          setHasUnsavedChanges(true);
                        }}
                      />
                      <ThemeOption
                        value="dark"
                        label="Dark"
                        icon={Moon}
                        current={theme}
                        onChange={(v) => {
                          setTheme(v);
                          setHasUnsavedChanges(true);
                        }}
                      />
                      <ThemeOption
                        value="system"
                        label="System"
                        icon={Monitor}
                        current={theme}
                        onChange={(v) => {
                          setTheme(v);
                          setHasUnsavedChanges(true);
                        }}
                      />
                    </div>
                  </SettingGroup>

                  <SettingGroup title="Display Options">
                    <ToggleField
                      label="Compact Mode"
                      description="Show more content with reduced spacing"
                      checked={compactMode}
                      onChange={(v) => {
                        setCompactMode(v);
                        setHasUnsavedChanges(true);
                      }}
                    />
                    <ToggleField
                      label="Show Avatars"
                      description="Display user avatars in conversations"
                      checked={showAvatars}
                      onChange={(v) => {
                        setShowAvatars(v);
                        setHasUnsavedChanges(true);
                      }}
                    />
                  </SettingGroup>
                </SettingsSection>
              )}

              {activeTab === 'integrations' && (
                <SettingsSection title="Integrations">
                  <div className="space-y-3">
                    {integrations.map((integration) => {
                      const Icon = integration.icon;
                      return (
                        <div
                          key={integration.id}
                          className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-800"
                        >
                          <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-700">
                              <Icon className="h-5 w-5 text-zinc-600 dark:text-zinc-400" />
                            </div>
                            <div>
                              <p className="font-medium text-zinc-900 dark:text-zinc-100">
                                {integration.name}
                              </p>
                              <p className="text-xs text-zinc-500 capitalize">
                                {integration.status}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {integration.status === 'disconnected' ? (
                              <button
                                onClick={() => {
                                  setSelectedIntegration(integration);
                                  setShowModal('connectIntegration');
                                }}
                                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
                              >
                                <Plus className="h-3.5 w-3.5" />
                                Connect
                              </button>
                            ) : (
                              <>
                                <button
                                  onClick={() => {
                                    setSelectedIntegration(integration);
                                    setShowModal('configureIntegration');
                                  }}
                                  className="rounded-lg border border-zinc-200 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300"
                                >
                                  Configure
                                </button>
                                <button
                                  onClick={() => {
                                    setIntegrations(
                                      integrations.map((i) =>
                                        i.id === integration.id
                                          ? { ...i, enabled: !i.enabled }
                                          : i
                                      )
                                    );
                                    setHasUnsavedChanges(true);
                                  }}
                                  className={cn(
                                    'rounded-lg px-3 py-1.5 text-sm font-medium',
                                    integration.enabled
                                      ? 'bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-900/20'
                                      : 'bg-green-50 text-green-600 hover:bg-green-100 dark:bg-green-900/20'
                                  )}
                                >
                                  {integration.enabled ? 'Disable' : 'Enable'}
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <div className="mt-6 rounded-lg border border-dashed border-zinc-300 p-6 text-center dark:border-zinc-700">
                    <Webhook className="mx-auto h-8 w-8 text-zinc-400" />
                    <p className="mt-2 text-sm font-medium text-zinc-900 dark:text-zinc-100">
                      More integrations coming soon
                    </p>
                    <p className="text-xs text-zinc-500">
                      Zapier, Microsoft Teams, Salesforce, and more
                    </p>
                    <button
                      onClick={() => setShowModal('requestIntegration')}
                      className="mt-4 text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                    >
                      Request an integration →
                    </button>
                  </div>
                </SettingsSection>
              )}

              {activeTab === 'api' && (
                <SettingsSection title="API Keys">
                  <div className="mb-4 flex items-start gap-3 rounded-lg bg-amber-50 p-4 dark:bg-amber-900/20">
                    <Info className="h-5 w-5 text-amber-600 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                        Keep your API keys secure
                      </p>
                      <p className="text-xs text-amber-700 dark:text-amber-300">
                        API keys have full access to your account. Never share them publicly or commit them to version control.
                      </p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {apiKeys.map((apiKey) => (
                      <div
                        key={apiKey.id}
                        className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-800"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-zinc-900 dark:text-zinc-100">
                              {apiKey.name}
                            </p>
                            <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900 dark:text-green-300">
                              Active
                            </span>
                          </div>
                          <div className="mt-1 flex items-center gap-3 text-xs text-zinc-500">
                            <code className="rounded bg-zinc-100 px-2 py-0.5 dark:bg-zinc-700">
                              {apiKey.key}
                            </code>
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(apiKey.key);
                                alert('API key copied to clipboard!');
                              }}
                              className="flex items-center gap-1 text-zinc-400 hover:text-zinc-600"
                            >
                              <Copy className="h-3 w-3" />
                              Copy
                            </button>
                          </div>
                          <div className="mt-2 flex items-center gap-4 text-xs text-zinc-400">
                            <span>Created: {apiKey.created}</span>
                            <span>Last used: {apiKey.lastUsed}</span>
                          </div>
                        </div>
                        <button
                          onClick={() => {
                            if (confirm('Are you sure you want to delete this API key?')) {
                              setApiKeys(apiKeys.filter((k) => k.id !== apiKey.id));
                              setHasUnsavedChanges(true);
                            }
                          }}
                          className="rounded-lg p-2 text-red-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>

                  <button
                    onClick={() => setShowModal('apiKey')}
                    className="mt-4 flex items-center gap-2 rounded-lg border border-dashed border-zinc-300 px-4 py-3 text-sm font-medium text-zinc-600 hover:border-indigo-500 hover:text-indigo-600 dark:border-zinc-700 dark:text-zinc-400"
                  >
                    <Plus className="h-4 w-4" />
                    Create New API Key
                  </button>
                </SettingsSection>
              )}

              {activeTab === 'security' && (
                <SettingsSection title="Security Settings">
                  <SettingGroup title="Authentication">
                    <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-800">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Shield className="h-5 w-5 text-green-600" />
                          <div>
                            <p className="font-medium text-zinc-900 dark:text-zinc-100">
                              Two-Factor Authentication
                            </p>
                            <p className="text-xs text-zinc-500">
                              Add an extra layer of security to your account
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => setShowModal('2fa')}
                          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                        >
                          Enable 2FA
                        </button>
                      </div>
                    </div>
                  </SettingGroup>

                  <SettingGroup title="Password">
                    <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-800">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-zinc-900 dark:text-zinc-100">
                            Change Password
                          </p>
                          <p className="text-xs text-zinc-500">
                            Last changed 30 days ago
                          </p>
                        </div>
                        <button
                          onClick={() => setShowModal('password')}
                          className="rounded-lg border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300"
                        >
                          Update
                        </button>
                      </div>
                    </div>
                  </SettingGroup>

                  <SettingGroup title="Sessions">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-800">
                        <div className="flex items-center gap-3">
                          <Monitor className="h-5 w-5 text-zinc-400" />
                          <div>
                            <p className="font-medium text-zinc-900 dark:text-zinc-100">
                              Current Session
                            </p>
                            <p className="text-xs text-zinc-500">
                              Chrome on Windows • Active now
                            </p>
                          </div>
                        </div>
                        <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900 dark:text-green-300">
                          Active
                        </span>
                      </div>
                      <div className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-800">
                        <div className="flex items-center gap-3">
                          <Monitor className="h-5 w-5 text-zinc-400" />
                          <div>
                            <p className="font-medium text-zinc-900 dark:text-zinc-100">
                              Previous Session
                            </p>
                            <p className="text-xs text-zinc-500">
                              Safari on macOS • 2 days ago
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => {
                            if (confirm('Are you sure you want to revoke this session?')) {
                              alert('Session revoked! (Demo)');
                            }
                          }}
                          className="text-sm font-medium text-red-600 hover:text-red-700"
                        >
                          Revoke
                        </button>
                      </div>
                    </div>
                  </SettingGroup>
                </SettingsSection>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Avatar Change Modal */}
      {showModal === 'avatar' && (
        <Modal
          title="Change Avatar"
          onClose={() => setShowModal('none')}
        >
          <div className="space-y-4">
            <div className="flex justify-center">
              {profile.avatar ? (
                <img
                  src={profile.avatar}
                  alt={profile.name}
                  className="h-32 w-32 rounded-full object-cover"
                />
              ) : (
                <div className="flex h-32 w-32 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-5xl font-bold text-white">
                  {profile.name.split(' ').map((n: string) => n[0]).join('').slice(0, 2)}
                </div>
              )}
            </div>
            <div className="rounded-lg border border-dashed border-zinc-300 p-6 text-center dark:border-zinc-700">
              <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100 mb-2">
                Upload a new avatar
              </p>
              <p className="text-xs text-zinc-500 mb-4">
                JPG, GIF or PNG. Max size 2MB.
              </p>
              <div className="flex justify-center gap-3">
                <input
                  type="file"
                  id="avatar-upload"
                  accept="image/jpeg,image/gif,image/png"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      // Validate file type
                      const validTypes = ['image/jpeg', 'image/gif', 'image/png'];
                      if (!validTypes.includes(file.type)) {
                        alert('Please select a valid image file (JPG, GIF, or PNG)');
                        return;
                      }
                      // Validate file size (2MB max)
                      if (file.size > 2 * 1024 * 1024) {
                        alert('File size must be less than 2MB');
                        return;
                      }
                      // Convert file to base64 and store in localStorage
                      const reader = new FileReader();
                      reader.onload = (event) => {
                        const base64Image = event.target?.result as string;
                        // Store avatar in localStorage
                        localStorage.setItem('userAvatar', base64Image);
                        // Update profile state
                        setProfile({ ...profile, avatar: base64Image });
                        setHasUnsavedChanges(true);
                        setShowModal('none');
                        alert('Avatar updated successfully!');
                      };
                      reader.onerror = () => {
                        alert('Error reading file. Please try again.');
                      };
                      reader.readAsDataURL(file);
                    }
                  }}
                />
                <label
                  htmlFor="avatar-upload"
                  className="inline-block cursor-pointer rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                >
                  Choose File
                </label>
                {profile.avatar && (
                  <button
                    onClick={() => {
                      localStorage.removeItem('userAvatar');
                      setProfile({ ...profile, avatar: '' });
                      setHasUnsavedChanges(true);
                      setShowModal('none');
                      alert('Avatar removed successfully!');
                    }}
                    className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-100 dark:border-red-800 dark:bg-red-900/20"
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Create API Key Modal */}
      {showModal === 'apiKey' && (
        <Modal
          title="Create New API Key"
          onClose={() => setShowModal('none')}
        >
          <div className="space-y-4">
            <div className="rounded-lg bg-amber-50 p-4 dark:bg-amber-900/20">
              <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                ⚠️ Keep your API key secure
              </p>
              <p className="text-xs text-amber-700 dark:text-amber-300">
                Once created, you won't be able to see the full key again. Store it in a safe place.
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                Key Name
              </label>
              <input
                type="text"
                placeholder="e.g., Production API Key"
                className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800"
              />
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <button
                onClick={() => setShowModal('none')}
                className="rounded-lg border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setApiKeys([...apiKeys, {
                    id: String(Date.now()),
                    name: 'New API Key',
                    key: 'sk_live_••••••••••••' + Math.random().toString().slice(2, 6),
                    created: new Date().toISOString().split('T')[0],
                    lastUsed: 'Never',
                  }]);
                  setShowModal('none');
                  setHasUnsavedChanges(true);
                }}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
              >
                Create Key
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* 2FA Modal */}
      {showModal === '2fa' && (
        <Modal
          title="Enable Two-Factor Authentication"
          onClose={() => setShowModal('none')}
        >
          <div className="space-y-4">
            <div className="text-center">
              <Shield className="h-16 w-16 text-indigo-600 mx-auto mb-4" />
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                Scan this QR code with your authenticator app
              </p>
            </div>
            <div className="flex justify-center">
              <div className="h-48 w-48 bg-white p-4 rounded-lg">
                {/* QR Code placeholder */}
                <div className="h-full w-full bg-gradient-to-br from-indigo-500 to-purple-600 rounded flex items-center justify-center text-white text-xs text-center">
                  QR Code<br/>Placeholder
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                Enter 6-digit code
              </label>
              <input
                type="text"
                placeholder="000000"
                maxLength={6}
                className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-center text-lg outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800"
              />
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <button
                onClick={() => setShowModal('none')}
                className="rounded-lg border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowModal('none');
                  alert('2FA enabled successfully! (Demo)');
                }}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
              >
                Enable 2FA
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Change Password Modal */}
      {showModal === 'password' && (
        <Modal
          title="Change Password"
          onClose={() => setShowModal('none')}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                Current Password
              </label>
              <input
                type="password"
                placeholder="••••••••"
                className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                New Password
              </label>
              <input
                type="password"
                placeholder="••••••••"
                className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                Confirm New Password
              </label>
              <input
                type="password"
                placeholder="••••••••"
                className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800"
              />
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <button
                onClick={() => setShowModal('none')}
                className="rounded-lg border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowModal('none');
                  alert('Password changed successfully! (Demo)');
                }}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
              >
                Update Password
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Connect Integration Modal */}
      {showModal === 'connectIntegration' && selectedIntegration && (
        <Modal
          title={`Connect ${selectedIntegration.name}`}
          onClose={() => setShowModal('none')}
        >
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 bg-zinc-50 dark:bg-zinc-800 rounded-lg">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-zinc-200 dark:bg-zinc-700">
                <selectedIntegration.icon className="h-6 w-6 text-zinc-600 dark:text-zinc-400" />
              </div>
              <div>
                <p className="font-medium text-zinc-900 dark:text-zinc-100">{selectedIntegration.name}</p>
                <p className="text-xs text-zinc-500">Connect your account to enable notifications</p>
              </div>
            </div>
            <div className="rounded-lg bg-amber-50 dark:bg-amber-900/20 p-4">
              <p className="text-sm font-medium text-amber-800 dark:text-amber-200 mb-2">
                🔐 Authentication Required
              </p>
              <p className="text-xs text-amber-700 dark:text-amber-300">
                You will be redirected to {selectedIntegration.name} to authorize the connection.
              </p>
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <button
                onClick={() => setShowModal('none')}
                className="rounded-lg border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  // Simulate OAuth flow
                  setIntegrations(
                    integrations.map((i) =>
                      i.id === selectedIntegration.id
                        ? { ...i, enabled: true, status: 'connected' as const }
                        : i
                    )
                  );
                  setShowModal('none');
                  setHasUnsavedChanges(true);
                  alert(`Successfully connected to ${selectedIntegration.name}! (Demo)`);
                }}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
              >
                Connect
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Configure Integration Modal */}
      {showModal === 'configureIntegration' && selectedIntegration && (
        <Modal
          title={`Configure ${selectedIntegration.name}`}
          onClose={() => setShowModal('none')}
        >
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 bg-zinc-50 dark:bg-zinc-800 rounded-lg">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-zinc-200 dark:bg-zinc-700">
                <selectedIntegration.icon className="h-6 w-6 text-zinc-600 dark:text-zinc-400" />
              </div>
              <div>
                <p className="font-medium text-zinc-900 dark:text-zinc-100">{selectedIntegration.name}</p>
                <p className="text-xs text-green-600 dark:text-green-400 capitalize">{selectedIntegration.status}</p>
              </div>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                  Notification Settings
                </label>
                <select className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800">
                  <option>All notifications</option>
                  <option>Important only</option>
                  <option>Mentions only</option>
                  <option>None</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                  Webhook URL (optional)
                </label>
                <input
                  type="text"
                  placeholder="https://your-domain.com/webhook"
                  className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800"
                />
              </div>
            </div>

            <div className="rounded-lg bg-blue-50 dark:bg-blue-900/20 p-4">
              <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                ℹ️ Demo Mode
              </p>
              <p className="text-xs text-blue-700 dark:text-blue-300">
                Configuration changes are not persisted in demo mode.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <button
                onClick={() => setShowModal('none')}
                className="rounded-lg border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowModal('none');
                  alert(`${selectedIntegration.name} settings saved! (Demo)`);
                }}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
              >
                Save Changes
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Request Integration Modal */}
      {showModal === 'requestIntegration' && (
        <Modal
          title="Request an Integration"
          onClose={() => setShowModal('none')}
        >
          <form onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.currentTarget);
            const request = {
              id: Date.now().toString(),
              integrationName: formData.get('integrationName') as string,
              useCase: formData.get('useCase') as string,
              email: formData.get('email') as string,
              submittedAt: new Date().toISOString(),
            };
            
            // Store in localStorage
            const existingRequests = JSON.parse(localStorage.getItem('integrationRequests') || '[]');
            existingRequests.push(request);
            localStorage.setItem('integrationRequests', JSON.stringify(existingRequests));
            
            setShowModal('none');
            alert(`Thanks for requesting "${request.integrationName}"!\n\nWe've saved your request. (Demo: Check browser localStorage)`);
          }}>
            <div className="space-y-4">
              <div className="rounded-lg bg-indigo-50 dark:bg-indigo-900/20 p-4">
                <p className="text-sm font-medium text-indigo-800 dark:text-indigo-200 mb-1">
                  🚀 Help us prioritize!
                </p>
                <p className="text-xs text-indigo-700 dark:text-indigo-300">
                  Tell us which integrations you need most. We read every request!
                </p>
              </div>
              
              <div className="space-y-3">
                <div>
                  <label htmlFor="integrationName" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    Integration Name *
                  </label>
                  <input
                    id="integrationName"
                    name="integrationName"
                    type="text"
                    required
                    placeholder="e.g., Slack, Notion, HubSpot"
                    className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800"
                  />
                </div>
                <div>
                  <label htmlFor="useCase" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    Use Case
                  </label>
                  <textarea
                    id="useCase"
                    name="useCase"
                    placeholder="How would you use this integration?"
                    rows={3}
                    className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800 resize-none"
                  />
                </div>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    Your Email (optional)
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="you@company.com"
                    className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal('none')}
                  className="rounded-lg border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                >
                  Submit Request
                </button>
              </div>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}

function SettingsSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-6">
      <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
        {title}
      </h3>
      {children}
    </div>
  );
}

function SettingGroup({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-4">
      {title && (
        <h4 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          {title}
        </h4>
      )}
      {children}
    </div>
  );
}

function TextField({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800"
      />
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function ToggleField({
  label,
  description,
  icon: Icon,
  checked,
  onChange,
}: {
  label: string;
  description?: string;
  icon?: React.ElementType;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-3">
        {Icon && <Icon className="h-5 w-5 text-zinc-400" />}
        <div>
          <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
            {label}
          </p>
          {description && (
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              {description}
            </p>
          )}
        </div>
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={cn(
          'relative h-6 w-11 rounded-full transition-colors',
          checked ? 'bg-indigo-600' : 'bg-zinc-200 dark:bg-zinc-700'
        )}
      >
        <span
          className={cn(
            'absolute top-1 h-4 w-4 rounded-full bg-white transition-transform',
            checked ? 'left-6' : 'left-1'
          )}
        />
      </button>
    </div>
  );
}

function ThemeOption({
  value,
  label,
  icon: Icon,
  current,
  onChange,
}: {
  value: 'light' | 'dark' | 'system';
  label: string;
  icon: React.ElementType;
  current: 'light' | 'dark' | 'system';
  onChange: (value: 'light' | 'dark' | 'system') => void;
}) {
  return (
    <button
      onClick={() => onChange(value)}
      className={cn(
        'flex flex-col items-center gap-3 rounded-xl border p-4 transition-all',
        current === value
          ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/20'
          : 'border-zinc-200 bg-white hover:border-zinc-300 dark:border-zinc-700 dark:bg-zinc-800'
      )}
    >
      <Icon
        className={cn(
          'h-6 w-6',
          current === value ? 'text-indigo-600' : 'text-zinc-400'
        )}
      />
      <span
        className={cn(
          'text-sm font-medium',
          current === value ? 'text-indigo-600' : 'text-zinc-600 dark:text-zinc-400'
        )}
      >
        {label}
      </span>
      {current === value && (
        <Check className="h-4 w-4 text-indigo-600" />
      )}
    </button>
  );
}

function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl max-w-md w-full p-6 relative animate-in fade-in zoom-in duration-200">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
        >
          <X className="w-5 h-5" />
        </button>
        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
          {title}
        </h3>
        {children}
      </div>
    </div>
  );
}
