/**
 * Re-export the authoritative API client for backward compatibility.
 */
import { apiClient } from './api/client';

export * from './api/client';
export default apiClient;
