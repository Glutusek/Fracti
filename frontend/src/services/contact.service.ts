import apiClient from './api';

export interface ContactPayload {
  name: string;
  email: string;
  subject?: string;
  message: string;
}

class ContactService {
  async sendContact(data: ContactPayload) {
    const response = await apiClient.post('/contact/', data);
    return response.data;
  }
}

export default new ContactService();
