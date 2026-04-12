const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

export async function fetchFromAPI<T>(endpoint: string, options?: RequestInit): Promise<T | null> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      console.warn(`API warning: ${response.status} ${response.statusText} for ${endpoint}`);
      return null;
    }

    return response.json();
  } catch (error) {
    console.warn(`API request failed for ${endpoint}:`, error);
    return null;
  }
}

export interface Notification {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

export async function getNotifications(): Promise<{
  notifications: Notification[];
  unread_count: number;
  total_count: number;
} | null> {
  return fetchFromAPI('/api/notifications');
}

export async function markNotificationAsRead(id: string): Promise<{ success: boolean; message: string } | null> {
  return fetchFromAPI(`/api/notifications/${id}/read`, {
    method: 'POST',
  });
}

export async function markAllNotificationsAsRead(): Promise<{ success: boolean; message: string } | null> {
  return fetchFromAPI('/api/notifications/mark-all-read', {
    method: 'POST',
  });
}

export async function deleteNotification(id: string): Promise<{ success: boolean; message: string } | null> {
  return fetchFromAPI(`/api/notifications/${id}`, {
    method: 'DELETE',
  });
}

export async function clearReadNotifications(): Promise<{
  success: boolean;
  message: string;
  cleared_count: number;
} | null> {
  return fetchFromAPI('/api/notifications/clear-read', {
    method: 'POST',
  });
}
