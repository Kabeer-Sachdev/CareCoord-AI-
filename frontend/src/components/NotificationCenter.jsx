import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';
import { wsClient } from '../services/websocket';

const PRIORITY_STYLES = {
  CRITICAL: {
    badge: 'bg-red-900 text-red-300 border border-red-700',
    dot: 'bg-red-500',
    border: 'border-l-red-500',
  },
  HIGH: {
    badge: 'bg-orange-900 text-orange-300 border border-orange-700',
    dot: 'bg-orange-500',
    border: 'border-l-orange-500',
  },
  NORMAL: {
    badge: 'bg-blue-900 text-blue-300 border border-blue-700',
    dot: 'bg-blue-500',
    border: 'border-l-blue-500',
  },
  LOW: {
    badge: 'bg-gray-800 text-gray-400 border border-gray-600',
    dot: 'bg-gray-500',
    border: 'border-l-gray-500',
  },
};

function timeAgo(dateStr) {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export function NotificationCenter() {
  const { isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef(null);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const fetchNotifications = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const data = await apiService.getNotifications();
      const list = Array.isArray(data) ? data : data.notifications || [];
      setNotifications(list.slice(0, 20));
    } catch {
      // silently ignore fetch errors for notification centre
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  // Initial load & poll every 30s
  useEffect(() => {
    if (!isAuthenticated) return;
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [isAuthenticated, fetchNotifications]);

  // Real-time updates via WebSocket
  useEffect(() => {
    const unsub = wsClient.on('NOTIFICATION_CREATED', (payload) => {
      setNotifications((prev) => {
        const newNotif = payload.notification || payload;
        return [newNotif, ...prev].slice(0, 20);
      });
    });
    return unsub;
  }, []);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    function handleClick(e) {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  async function handleMarkRead(id) {
    try {
      await apiService.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch {}
  }

  async function handleMarkAllRead() {
    try {
      await apiService.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {}
  }

  if (!isAuthenticated) return null;

  return (
    <div className="relative" ref={panelRef}>
      {/* Bell button */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-label="Notifications"
      >
        {/* Bell SVG */}
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>

        {/* Unread badge */}
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 text-xs font-bold leading-none text-white bg-red-600 rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown panel */}
      {open && (
        <div className="absolute right-0 mt-2 w-96 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-50 flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
            <h3 className="text-sm font-semibold text-white">Notifications</h3>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                Mark all read
              </button>
            )}
          </div>

          {/* Notification list */}
          <div className="max-h-96 overflow-y-auto divide-y divide-gray-800">
            {loading && notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500 text-sm">
                Loading…
              </div>
            ) : notifications.length === 0 ? (
              <div className="px-4 py-10 text-center">
                <svg
                  className="mx-auto w-10 h-10 text-gray-700 mb-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                <p className="text-sm text-gray-500">No notifications yet</p>
              </div>
            ) : (
              notifications.map((notif) => {
                const priority = notif.priority || 'NORMAL';
                const styles = PRIORITY_STYLES[priority] || PRIORITY_STYLES.NORMAL;
                return (
                  <button
                    key={notif.id}
                    onClick={() => !notif.is_read && handleMarkRead(notif.id)}
                    className={`w-full text-left px-4 py-3 border-l-4 ${styles.border} transition-colors ${
                      notif.is_read
                        ? 'bg-gray-900 hover:bg-gray-800'
                        : 'bg-gray-800 hover:bg-gray-750'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      {/* Unread dot */}
                      <span
                        className={`mt-1.5 flex-shrink-0 w-2 h-2 rounded-full ${
                          notif.is_read ? 'bg-transparent' : styles.dot
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-0.5">
                          <p className="text-sm font-medium text-white truncate">
                            {notif.title}
                          </p>
                          <span
                            className={`flex-shrink-0 text-xs px-1.5 py-0.5 rounded font-medium ${styles.badge}`}
                          >
                            {priority}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400 line-clamp-2">
                          {notif.message}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">
                          {timeAgo(notif.created_at)}
                        </p>
                      </div>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
