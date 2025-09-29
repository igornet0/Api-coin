// API service for API Coin application

class ApiService {
  constructor() {
    this.baseURL = __API_URL__;
    this.token = localStorage.getItem('access_token');
  }

  // Utility method to make HTTP requests
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Add authorization header if token exists
    if (this.token) {
      config.headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, config);
      
      if (response.status === 401) {
        // Token expired, clear it and redirect to login
        this.clearToken();
        throw new Error('Unauthorized');
      }
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Request failed');
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Auth methods
  async register(userData) {
    const response = await this.request('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    
    if (response.access_token) {
      this.setToken(response.access_token);
    }
    
    return response;
  }

  async login(credentials) {
    const response = await this.request('/auth/login_user/', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    
    if (response.access_token) {
      this.setToken(response.access_token);
    }
    
    return response;
  }

  async getCurrentUser() {
    return await this.request('/auth/user/me/');
  }

  // API Keys methods
  async getApiKeys() {
    return await this.request('/api-keys/');
  }

  async createApiKey(apiKeyData) {
    return await this.request('/api-keys/', {
      method: 'POST',
      body: JSON.stringify(apiKeyData),
    });
  }

  async deleteApiKey(keyId) {
    return await this.request(`/api-keys/${keyId}`, {
      method: 'DELETE',
    });
  }

  async updateApiKey(keyId, apiKeyData) {
    return await this.request(`/api-keys/${keyId}`, {
      method: 'PUT',
      body: JSON.stringify(apiKeyData),
    });
  }

  async toggleApiKeyStatus(keyId) {
    return await this.request(`/api-keys/${keyId}/toggle`, {
      method: 'PUT',
    });
  }

  async getApiKeyUsage(keyId) {
    return await this.request(`/api-keys/${keyId}/usage`);
  }

  // Coin data methods
  async getCoins(params = {}) {
    const searchParams = new URLSearchParams(params);
    return await this.request(`/coin_api/?${searchParams}`);
  }

  async getCoin(coinId) {
    return await this.request(`/coin_api/${coinId}`);
  }

  // Token management
  setToken(token) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('access_token');
  }

  isAuthenticated() {
    return !!this.token;
  }
}

export default new ApiService();
