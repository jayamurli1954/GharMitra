/**
 * Settings Service for Web
 */
import api from './api';

class SettingsService {
  /**
   * Get society settings
   */
  async getSocietySettings() {
    const response = await api.get('/settings/society');
    return response.data;
  }

  /**
   * Create or update society settings
   */
  async saveSocietySettings(settingsData) {
    const response = await api.patch('/settings/society', settingsData);
    return response.data;
  }
}

export const settingsService = new SettingsService();
export default settingsService;

