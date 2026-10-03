/**
 * SERENIA ACCOUNTING — pages/settings/SettingsPage.tsx
 * =======================================================
 * User profile, password, preferences (theme/timezone/date format).
 */

import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api, { normalizeError } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardBody, Input, Select } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';

export const SettingsPage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [profile, setProfile] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.phone || '',
    qualification: user?.qualification || '',
    membership_number: user?.membership_number || '',
    timezone: user?.timezone || 'Asia/Kolkata',
    date_format: user?.date_format || 'DD/MM/YYYY',
  });

  const [passwords, setPasswords] = useState({ current_password: '', new_password: '', confirm_password: '' });

  const updateProfileMutation = useMutation({
    mutationFn: () => api.patch('/auth/me/', profile),
    onSuccess: () => { toast.success('Profile updated'); refreshUser(); },
    onError: (err) => toast.error(normalizeError(err).message),
  });

  const changePasswordMutation = useMutation({
    mutationFn: () => api.post('/auth/change-password/', passwords),
    onSuccess: () => { toast.success('Password updated'); setPasswords({ current_password: '', new_password: '', confirm_password: '' }); },
    onError: (err) => toast.error(normalizeError(err).message),
  });

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-surface-dark dark:text-white font-display">Settings</h1>
        <p className="text-sm text-surface-300 mt-0.5">Manage your profile and account preferences</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Profile Information</CardTitle></CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="First Name" value={profile.first_name} onChange={(e) => setProfile({ ...profile, first_name: e.target.value })} />
            <Input label="Last Name" value={profile.last_name} onChange={(e) => setProfile({ ...profile, last_name: e.target.value })} />
            <Input label="Email" value={user?.email || ''} disabled />
            <Input label="Phone" value={profile.phone} onChange={(e) => setProfile({ ...profile, phone: e.target.value })} />
            <Input label="Qualification" placeholder="e.g., CA, CPA" value={profile.qualification} onChange={(e) => setProfile({ ...profile, qualification: e.target.value })} />
            <Input label="Membership Number" placeholder="ICAI membership no." value={profile.membership_number} onChange={(e) => setProfile({ ...profile, membership_number: e.target.value })} />
          </div>
          <div className="flex justify-end">
            <Button onClick={() => updateProfileMutation.mutate()} isLoading={updateProfileMutation.isPending}>Save Changes</Button>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader><CardTitle>Preferences</CardTitle></CardHeader>
        <CardBody className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="Timezone"
            value={profile.timezone}
            onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}
            options={[
              { value: 'Asia/Kolkata', label: 'India Standard Time (IST)' },
              { value: 'UTC', label: 'UTC' },
              { value: 'America/New_York', label: 'Eastern Time (US)' },
              { value: 'Europe/London', label: 'London (GMT)' },
            ]}
          />
          <Select
            label="Date Format"
            value={profile.date_format}
            onChange={(e) => setProfile({ ...profile, date_format: e.target.value })}
            options={[
              { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
              { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
              { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
            ]}
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader><CardTitle>Change Password</CardTitle></CardHeader>
        <CardBody className="space-y-4">
          <Input label="Current Password" type="password" value={passwords.current_password} onChange={(e) => setPasswords({ ...passwords, current_password: e.target.value })} />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="New Password" type="password" value={passwords.new_password} onChange={(e) => setPasswords({ ...passwords, new_password: e.target.value })} />
            <Input label="Confirm New Password" type="password" value={passwords.confirm_password} onChange={(e) => setPasswords({ ...passwords, confirm_password: e.target.value })} />
          </div>
          <div className="flex justify-end">
            <Button onClick={() => changePasswordMutation.mutate()} isLoading={changePasswordMutation.isPending}>Update Password</Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};
