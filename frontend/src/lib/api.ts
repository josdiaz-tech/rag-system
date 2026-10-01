// API configuration
export const API_BASE_URL = 'http://localhost:8000';

// Helper function to get auth token
export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token');
  }
  return null;
}

// Helper function to set auth token
export function setToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('token', token);
  }
}

// Helper function to remove auth token
export function removeToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('token');
  }
}

// Helper function to make authenticated requests
export async function fetchAPI(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getToken();
  
  // Build headers properly
  const headers: Record<string, string> = {};
  
  // Copy existing headers if any
  if (options.headers) {
    const existingHeaders = new Headers(options.headers);
    existingHeaders.forEach((value, key) => {
      headers[key] = value;
    });
  }
  
  // Add auth header if token exists
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  // Add Content-Type for JSON if not multipart/form-data
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  
  return fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
}