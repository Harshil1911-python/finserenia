/**
 * SERENIA ACCOUNTING — components/layout/Topbar.tsx
 * ====================================================
 * Top navigation bar: sidebar toggle, company switcher,
 * dark mode toggle, notifications, user profile menu.
 */

import React, { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import {
  Bars3Icon, SunIcon, MoonIcon, BellIcon,
  ChevronDownIcon, UserCircleIcon, ArrowRightOnRectangleIcon,
  BuildingOffice2Icon, CheckIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';

export const Topbar: React.FC<{ onToggleSidebar: () => void }> = ({ onToggleSidebar }) => {
  const { user, activeCompany, companies, switchCompany, logout } = useAuth();
  const { mode, toggleMode } = useTheme();

  return (
    <header className="h-topbar sticky top-0 z-20 flex items-center justify-between px-4 lg:px-6 bg-white/80 dark:bg-surface-dark-elevated/80 backdrop-blur-md border-b border-surface-200 dark:border-surface-dark-border">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-md text-surface-300 hover:text-surface-dark dark:hover:text-white hover:bg-surface-50 dark:hover:bg-surface-dark transition-colors"
          aria-label="Toggle sidebar"
        >
          <Bars3Icon className="w-5 h-5" />
        </button>

        {/* Company Switcher */}
        {companies.length > 0 && (
          <Menu as="div" className="relative">
            <Menu.Button className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium text-surface-dark dark:text-white hover:bg-surface-50 dark:hover:bg-surface-dark transition-colors border border-surface-200 dark:border-surface-dark-border">
              <BuildingOffice2Icon className="w-4 h-4 text-primary-500" />
              <span className="max-w-[180px] truncate">{activeCompany?.name || 'Select company'}</span>
              <ChevronDownIcon className="w-4 h-4 text-surface-300" />
            </Menu.Button>
            <Transition as={Fragment} enter="transition ease-out duration-100" enterFrom="opacity-0 scale-95" enterTo="opacity-100 scale-100" leave="transition ease-in duration-75" leaveFrom="opacity-100 scale-100" leaveTo="opacity-0 scale-95">
              <Menu.Items className="absolute left-0 mt-2 w-64 origin-top-left rounded-lg bg-white dark:bg-surface-dark-elevated shadow-modal border border-surface-200 dark:border-surface-dark-border focus:outline-none py-1 max-h-80 overflow-y-auto">
                {companies.map((company) => (
                  <Menu.Item key={company.id}>
                    {({ active }) => (
                      <button
                        onClick={() => switchCompany(company.id)}
                        className={`w-full flex items-center justify-between px-3 py-2 text-sm text-left ${active ? 'bg-surface-50 dark:bg-surface-dark' : ''}`}
                      >
                        <span className="truncate">
                          <span className="block font-medium text-surface-dark dark:text-white">{company.name}</span>
                          {company.gstin && <span className="block text-2xs text-surface-300">{company.gstin}</span>}
                        </span>
                        {activeCompany?.id === company.id && <CheckIcon className="w-4 h-4 text-primary-500 shrink-0" />}
                      </button>
                    )}
                  </Menu.Item>
                ))}
              </Menu.Items>
            </Transition>
          </Menu>
        )}
      </div>

      <div className="flex items-center gap-2">
        {/* Dark mode toggle */}
        <button
          onClick={toggleMode}
          className="p-2 rounded-md text-surface-300 hover:text-surface-dark dark:hover:text-white hover:bg-surface-50 dark:hover:bg-surface-dark transition-colors"
          aria-label="Toggle dark mode"
        >
          {mode === 'dark' ? <SunIcon className="w-5 h-5" /> : <MoonIcon className="w-5 h-5" />}
        </button>

        {/* Notifications */}
        <button className="relative p-2 rounded-md text-surface-300 hover:text-surface-dark dark:hover:text-white hover:bg-surface-50 dark:hover:bg-surface-dark transition-colors">
          <BellIcon className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-danger" />
        </button>

        {/* User menu */}
        <Menu as="div" className="relative">
          <Menu.Button className="flex items-center gap-2 pl-2 pr-1 py-1 rounded-md hover:bg-surface-50 dark:hover:bg-surface-dark transition-colors">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-teal-400 flex items-center justify-center text-white text-sm font-semibold">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </div>
            <div className="hidden md:block text-left">
              <p className="text-sm font-medium text-surface-dark dark:text-white leading-tight">{user?.full_name}</p>
              <p className="text-2xs text-surface-300 leading-tight capitalize">{user?.role.replace('_', ' ')}</p>
            </div>
            <ChevronDownIcon className="w-4 h-4 text-surface-300 hidden md:block" />
          </Menu.Button>
          <Transition as={Fragment} enter="transition ease-out duration-100" enterFrom="opacity-0 scale-95" enterTo="opacity-100 scale-100" leave="transition ease-in duration-75" leaveFrom="opacity-100 scale-100" leaveTo="opacity-0 scale-95">
            <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right rounded-lg bg-white dark:bg-surface-dark-elevated shadow-modal border border-surface-200 dark:border-surface-dark-border focus:outline-none py-1">
              <Menu.Item>
                {({ active }) => (
                  <a href="/profile" className={`flex items-center gap-2.5 px-3 py-2 text-sm text-surface-dark dark:text-white ${active ? 'bg-surface-50 dark:bg-surface-dark' : ''}`}>
                    <UserCircleIcon className="w-4 h-4 text-surface-300" /> My Profile
                  </a>
                )}
              </Menu.Item>
              <div className="my-1 border-t border-surface-200 dark:border-surface-dark-border" />
              <Menu.Item>
                {({ active }) => (
                  <button onClick={logout} className={`w-full flex items-center gap-2.5 px-3 py-2 text-sm text-danger ${active ? 'bg-surface-50 dark:bg-surface-dark' : ''}`}>
                    <ArrowRightOnRectangleIcon className="w-4 h-4" /> Sign Out
                  </button>
                )}
              </Menu.Item>
            </Menu.Items>
          </Transition>
        </Menu>
      </div>
    </header>
  );
};
