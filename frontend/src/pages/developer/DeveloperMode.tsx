/**
 * SERENIA ACCOUNTING — pages/developer/DeveloperMode.tsx
 * =========================================================
 * Super Admin-only panel. Tabs: Branding, Theme, Features,
 * SMTP/API/Security settings, Content Management.
 * Changes are persisted to SystemSetting model and cached in Redis.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Tab } from '@headlessui/react';
import toast from 'react-hot-toast';
import {
  SwatchIcon, PaintBrushIcon, ToggleLeftIcon, EnvelopeIcon,
  ShieldCheckIcon, DocumentTextIcon, GlobeAltIcon,
} from '@heroicons/react/24/outline';
import api, { normalizeError } from '../../services/api';
import { Card, CardHeader, CardTitle, CardBody, Input, Select } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import type { SystemSetting, Theme } from '../../types';

const TABS = [
  { key: 'branding', label: 'Branding', icon: SwatchIcon },
  { key: 'theme', label: 'Theme Builder', icon: PaintBrushIcon },
  { key: 'features', label: 'Feature Toggles', icon: ToggleLeftIcon },
  { key: 'smtp', label: 'Email / SMTP', icon: EnvelopeIcon },
  { key: 'security', label: 'Security', icon: ShieldCheckIcon },
  { key: 'content', label: 'Content & Pages', icon: DocumentTextIcon },
  { key: 'navigation', label: 'Navigation', icon: GlobeAltIcon },
];

const SettingField: React.FC<{ setting: SystemSetting; onSave: (key: string, value: string) => void }> = ({ setting, onSave }) => {
  const [value, setValue] = useState(setting.value);
  const dirty = value !== setting.value;

  return (
    <div className="flex items-end gap-2">
      {setting.value_type === 'boolean' ? (
        <Select
          label={setting.label}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          options={[{ value: 'true', label: 'Enabled' }, { value: 'false', label: 'Disabled' }]}
          className="flex-1"
        />
      ) : setting.value_type === 'color' ? (
        <div className="flex-1">
          <label className="block text-sm font-medium text-surface-dark dark:text-surface-100 mb-1.5">{setting.label}</label>
          <div className="flex items-center gap-2">
            <input type="color" value={value} onChange={(e) => setValue(e.target.value)} className="w-10 h-9 rounded border border-surface-200 dark:border-surface-dark-border cursor-pointer" />
            <Input value={value} onChange={(e) => setValue(e.target.value)} className="flex-1" />
          </div>
        </div>
      ) : (
        <Input
          label={setting.label}
          value={value}
          type={setting.value_type === 'email' ? 'email' : setting.value_type === 'url' ? 'url' : 'text'}
          onChange={(e) => setValue(e.target.value)}
          hint={setting.description}
          className="flex-1"
        />
      )}
      {dirty && <Button size="sm" onClick={() => onSave(setting.key, value)}>Save</Button>}
    </div>
  );
};

export const DeveloperMode: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: settings, isLoading } = useQuery<SystemSetting[]>({
    queryKey: ['system-settings'],
    queryFn: async () => {
      const { data } = await api.get<SystemSetting[]>('/developer/settings/');
      return data;
    },
  });

  const { data: theme } = useQuery<Theme>({
    queryKey: ['active-theme'],
    queryFn: async () => {
      const { data } = await api.get<Theme>('/developer/theme/active/');
      return data;
    },
  });

  const saveMutation = useMutation({
    mutationFn: ({ key, value }: { key: string; value: string }) => api.patch(`/developer/settings/${key}/`, { value }),
    onSuccess: () => {
      toast.success('Setting updated');
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
    },
    onError: (err) => toast.error(normalizeError(err).message),
  });

  const themeUpdateMutation = useMutation({
    mutationFn: (updates: Partial<Theme>) => api.patch(`/developer/theme/${theme?.id}/`, updates),
    onSuccess: () => {
      toast.success('Theme updated — changes apply app-wide');
      queryClient.invalidateQueries({ queryKey: ['active-theme'] });
    },
    onError: (err) => toast.error(normalizeError(err).message),
  });

  const groupedSettings = (category: string) => settings?.filter((s) => s.category === category) || [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-dark dark:text-white font-display">Developer Mode</h1>
        <p className="text-sm text-surface-300 mt-0.5">
          Super Admin panel — control branding, theming, features, and platform configuration
        </p>
      </div>

      <Tab.Group>
        <Tab.List className="flex gap-1 border-b border-surface-200 dark:border-surface-dark-border overflow-x-auto">
          {TABS.map((tab) => (
            <Tab
              key={tab.key}
              className={({ selected }) =>
                `flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition-colors focus:outline-none ${
                  selected
                    ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-surface-300 hover:text-surface-dark dark:hover:text-white'
                }`
              }
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </Tab>
          ))}
        </Tab.List>

        <Tab.Panels className="mt-4">
          {/* Branding */}
          <Tab.Panel className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Software Branding</CardTitle></CardHeader>
              <CardBody className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {isLoading ? <p className="text-sm text-surface-300">Loading settings...</p> :
                  groupedSettings('branding').map((s) => (
                    <SettingField key={s.key} setting={s} onSave={(key, value) => saveMutation.mutate({ key, value })} />
                  ))
                }
              </CardBody>
            </Card>
          </Tab.Panel>

          {/* Theme Builder */}
          <Tab.Panel className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Theme Builder</CardTitle></CardHeader>
              <CardBody className="space-y-4">
                <p className="text-sm text-surface-300">
                  Customize colors and typography. Changes apply across the entire application instantly.
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  {theme && (['color_primary', 'color_secondary', 'color_accent', 'color_danger'] as const).map((key) => (
                    <div key={key}>
                      <label className="block text-sm font-medium text-surface-dark dark:text-surface-100 mb-1.5 capitalize">
                        {key.replace('color_', '').replace('_', ' ')}
                      </label>
                      <div className="flex items-center gap-2">
                        <input
                          type="color"
                          value={theme[key]}
                          onChange={(e) => themeUpdateMutation.mutate({ [key]: e.target.value })}
                          className="w-10 h-9 rounded border border-surface-200 dark:border-surface-dark-border cursor-pointer"
                        />
                        <span className="text-sm font-mono text-surface-300">{theme[key]}</span>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  <Input label="Heading Font" value={theme?.font_family_heading || ''} onChange={(e) => themeUpdateMutation.mutate({ font_family_heading: e.target.value })} />
                  <Input label="Body Font" value={theme?.font_family_body || ''} onChange={(e) => themeUpdateMutation.mutate({ font_family_body: e.target.value })} />
                </div>
              </CardBody>
            </Card>
          </Tab.Panel>

          {/* Feature Toggles */}
          <Tab.Panel className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Module Feature Toggles</CardTitle></CardHeader>
              <CardBody className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {groupedSettings('features').map((s) => (
                  <SettingField key={s.key} setting={s} onSave={(key, value) => saveMutation.mutate({ key, value })} />
                ))}
              </CardBody>
            </Card>
          </Tab.Panel>

          {/* SMTP */}
          <Tab.Panel className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Email / SMTP Configuration</CardTitle></CardHeader>
              <CardBody className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {groupedSettings('smtp').map((s) => (
                  <SettingField key={s.key} setting={s} onSave={(key, value) => saveMutation.mutate({ key, value })} />
                ))}
              </CardBody>
            </Card>
          </Tab.Panel>

          {/* Security */}
          <Tab.Panel className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Security Settings</CardTitle></CardHeader>
              <CardBody className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {groupedSettings('security').map((s) => (
                  <SettingField key={s.key} setting={s} onSave={(key, value) => saveMutation.mutate({ key, value })} />
                ))}
              </CardBody>
            </Card>
          </Tab.Panel>

          {/* Content Management */}
          <Tab.Panel className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Landing Page Content</CardTitle></CardHeader>
              <CardBody>
                <p className="text-sm text-surface-300 mb-3">
                  Edit hero text, features, pricing, testimonials, and footer content shown on the public landing page.
                </p>
                <Button variant="outline">Open Content Editor</Button>
              </CardBody>
            </Card>
          </Tab.Panel>

          {/* Navigation */}
          <Tab.Panel className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Navigation Menu</CardTitle></CardHeader>
              <CardBody>
                <p className="text-sm text-surface-300 mb-3">
                  Manage header and footer navigation links for the marketing site.
                </p>
                <Button variant="outline">Manage Menu Items</Button>
              </CardBody>
            </Card>
          </Tab.Panel>
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
};
