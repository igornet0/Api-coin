import { useState, useEffect } from 'react';
import apiService from '../services/api';
import InputField from './InputField';
import Button from './Button';

const ApiKeysManager = () => {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingKey, setEditingKey] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    api_key: '',
    api_secret: '',
    api_passphrase: '',
    limit_requests: 1000,
    timedelta_refresh: 60
  });
  const [submitting, setSubmitting] = useState(false);
  const [showUsageDetails, setShowUsageDetails] = useState({});

  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    try {
      setLoading(true);
      const keys = await apiService.getApiKeys();
      setApiKeys(keys);
    } catch (err) {
      setError('Ошибка загрузки API ключей: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFormChange = (e) => {
    const { name, value, type } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'number' ? parseInt(value) || 0 : value
    });
  };

  const loadUsageInfo = async (keyId) => {
    try {
      const usage = await apiService.getApiKeyUsage(keyId);
      setShowUsageDetails(prev => ({
        ...prev,
        [keyId]: usage
      }));
    } catch (err) {
      console.error('Ошибка загрузки статистики:', err);
    }
  };

  const toggleUsageDetails = (keyId) => {
    setShowUsageDetails(prev => {
      if (prev[keyId]) {
        const { [keyId]: removed, ...rest } = prev;
        return rest;
      } else {
        loadUsageInfo(keyId);
        return prev;
      }
    });
  };

  const resetForm = () => {
    setFormData({
      name: '',
      api_key: '',
      api_secret: '',
      api_passphrase: '',
      limit_requests: 1000,
      timedelta_refresh: 60
    });
    setEditingKey(null);
    setShowAddForm(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      if (editingKey) {
        await apiService.updateApiKey(editingKey.id, formData);
      } else {
        await apiService.createApiKey(formData);
      }
      resetForm();
      await loadApiKeys();
    } catch (err) {
      setError(`Ошибка ${editingKey ? 'обновления' : 'создания'} API ключа: ` + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (key) => {
    setFormData({
      name: key.name,
      api_key: key.api_key,
      api_secret: '', // Не показываем секрет для безопасности
      api_passphrase: '', // Не показываем пароль для безопасности
      limit_requests: key.limit_requests,
      timedelta_refresh: key.timedelta_refresh
    });
    setEditingKey(key);
    setShowAddForm(true);
  };

  const handleDelete = async (keyId) => {
    if (!confirm('Вы уверены, что хотите удалить этот API ключ?')) {
      return;
    }

    try {
      await apiService.deleteApiKey(keyId);
      await loadApiKeys();
    } catch (err) {
      setError('Ошибка удаления API ключа: ' + err.message);
    }
  };

  const handleToggleStatus = async (keyId) => {
    try {
      await apiService.toggleApiKeyStatus(keyId);
      await loadApiKeys();
    } catch (err) {
      setError('Ошибка изменения статуса API ключа: ' + err.message);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="relative">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
          <div className="absolute inset-0 animate-ping rounded-full h-16 w-16 border-2 border-blue-400 opacity-20"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header Section */}
      <div className="mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Управление API ключами
            </h2>
            <p className="text-gray-600 max-w-2xl">
              Добавьте и управляйте вашими API ключами для криптовалютных бирж. 
              Все ключи хранятся в зашифрованном виде.
            </p>
          </div>
        <Button
          onClick={() => setShowAddForm(!showAddForm)}
          variant={showAddForm ? "secondary" : "primary"}
          icon={({ className }) => (
            showAddForm ? (
              <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            )
          )}
        >
          {showAddForm ? 'Отмена' : 'Добавить ключ'}
        </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex">
            <svg className="h-5 w-5 text-red-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="text-sm text-red-700">{error}</div>
          </div>
        </div>
      )}

      {/* Add Form */}
      {showAddForm && (
        <div className="mb-8 bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 p-8">
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              {editingKey ? 'Редактировать API ключ' : 'Добавить новый API ключ'}
            </h3>
            <p className="text-gray-600">
              {editingKey 
                ? 'Обновите параметры API ключа. Секретные данные будут сохранены только при их изменении.' 
                : 'Введите данные вашего API ключа от криптовалютной биржи'
              }
            </p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-6">
              <InputField
                label="Название ключа"
                name="name"
                type="text"
                value={formData.name}
                onChange={handleFormChange}
                placeholder="Например: Мой KuCoin API"
                required
                icon={({ className }) => (
                  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                )}
              />
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <InputField
                  label="API Key"
                  name="api_key"
                  type="text"
                  value={formData.api_key}
                  onChange={handleFormChange}
                  placeholder="Ваш API ключ"
                  required
                  icon={({ className }) => (
                    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m0 0a2 2 0 012 2 2 2 0 00-2-2m-2-2v2m0 6V9.5m0 0a2 2 0 012-2 2 2 0 00-2 2z" />
                    </svg>
                  )}
                />
                
                <InputField
                  label="API Secret"
                  name="api_secret"
                  type="password"
                  value={formData.api_secret}
                  onChange={handleFormChange}
                  placeholder={editingKey ? "Оставьте пустым, чтобы не изменять" : "Ваш API secret"}
                  required={!editingKey}
                  icon={({ className }) => (
                    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  )}
                />
              </div>
              
              <InputField
                label="API Passphrase"
                name="api_passphrase"
                type="password"
                value={formData.api_passphrase}
                onChange={handleFormChange}
                placeholder={editingKey ? "Оставьте пустым, чтобы не изменять" : "Ваша API passphrase"}
                required={!editingKey}
                icon={({ className }) => (
                  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                )}
              />

              {/* Rate Limiting Settings */}
              <div className="border-t pt-6">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Настройки лимитирования</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <InputField
                    label="Лимит запросов"
                    name="limit_requests"
                    type="number"
                    value={formData.limit_requests}
                    onChange={handleFormChange}
                    placeholder="1000"
                    min="1"
                    max="10000"
                    required
                    icon={({ className }) => (
                      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    )}
                    helpText="Максимальное количество запросов в периоде"
                  />
                  
                  <InputField
                    label="Период обновления (минуты)"
                    name="timedelta_refresh"
                    type="number"
                    value={formData.timedelta_refresh}
                    onChange={handleFormChange}
                    placeholder="60"
                    min="1"
                    max="1440"
                    required
                    icon={({ className }) => (
                      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    )}
                    helpText="Через сколько минут счетчик запросов обнуляется"
                  />
                </div>
              </div>
            </div>
            
            <div className="flex gap-4 pt-4">
              <Button
                type="submit"
                disabled={submitting}
                loading={submitting}
                variant="primary"
                icon={({ className }) => (
                  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={editingKey ? "M5 13l4 4L19 7" : "M12 6v6m0 0v6m0-6h6m-6 0H6"} />
                  </svg>
                )}
              >
                {submitting 
                  ? (editingKey ? 'Обновление...' : 'Сохранение...')
                  : (editingKey ? 'Обновить ключ' : 'Сохранить ключ')
                }
              </Button>
              
              <Button
                type="button"
                onClick={resetForm}
                variant="secondary"
              >
                Отмена
              </Button>
            </div>
          </form>
        </div>
      )}

      {/* API Keys List */}
      <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 overflow-hidden">
        {apiKeys.length === 0 ? (
          <div className="p-12 text-center">
            <div className="mx-auto h-24 w-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <svg className="h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m0 0a2 2 0 012 2 2 2 0 00-2-2m-2-2v2m0 6V9.5m0 0a2 2 0 012-2 2 2 0 00-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Нет API ключей</h3>
            <p className="text-gray-500 mb-6">У вас пока нет добавленных API ключей. Добавьте первый ключ для начала работы.</p>
            <Button
              onClick={() => setShowAddForm(true)}
              variant="primary"
              icon={({ className }) => (
                <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              )}
            >
              Добавить первый ключ
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50/80">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Название
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    API Key
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Лимиты
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Статус
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {apiKeys.map((key) => (
                  <>
                    <tr key={key.id} className="hover:bg-gray-50/50 transition-colors duration-200">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <button
                            onClick={() => toggleUsageDetails(key.id)}
                            className="h-10 w-10 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mr-3 hover:from-blue-600 hover:to-indigo-700 transition-all duration-200"
                          >
                            <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m0 0a2 2 0 012 2 2 2 0 00-2-2m-2-2v2m0 6V9.5m0 0a2 2 0 012-2 2 2 0 00-2 2z" />
                            </svg>
                          </button>
                          <div>
                            <div className="text-sm font-medium text-gray-900">{key.name}</div>
                            <div className="text-sm text-gray-500">API ключ #{key.id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <code className="px-3 py-1 text-sm bg-gray-100 rounded-lg font-mono text-gray-700">
                          {key.api_key.substring(0, 8)}...{key.api_key.substring(key.api_key.length - 4)}
                        </code>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="space-y-1">
                          <div className="flex items-center text-sm text-gray-600">
                            <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                            {key.requests_count || 0} / {key.limit_requests || 1000}
                          </div>
                          <div className="flex items-center text-sm text-gray-600">
                            <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {key.timedelta_refresh || 60} мин
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                            key.is_active
                              ? 'bg-green-100 text-green-800 border border-green-200'
                              : 'bg-red-100 text-red-800 border border-red-200'
                          }`}
                        >
                          <div className={`h-2 w-2 rounded-full mr-2 ${
                            key.is_active ? 'bg-green-500' : 'bg-red-500'
                          }`}></div>
                          {key.is_active ? 'Активен' : 'Неактивен'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleEdit(key)}
                            className="text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-3 py-1 rounded-lg text-sm font-medium transition-all duration-200"
                          >
                            Изменить
                          </button>
                          <button
                            onClick={() => handleToggleStatus(key.id)}
                            className={`px-3 py-1 rounded-lg text-sm font-medium transition-all duration-200 ${
                              key.is_active
                                ? 'text-orange-600 hover:text-orange-800 hover:bg-orange-50'
                                : 'text-green-600 hover:text-green-800 hover:bg-green-50'
                            }`}
                          >
                            {key.is_active ? 'Деактивировать' : 'Активировать'}
                          </button>
                          <button
                            onClick={() => handleDelete(key.id)}
                            className="text-red-600 hover:text-red-800 hover:bg-red-50 px-3 py-1 rounded-lg text-sm font-medium transition-all duration-200"
                          >
                            Удалить
                          </button>
                        </div>
                      </td>
                    </tr>
                    {showUsageDetails[key.id] && (
                      <tr key={`${key.id}-details`}>
                        <td colSpan="5" className="px-6 py-4 bg-blue-50/50">
                          <div className="rounded-lg bg-white/80 p-4 border border-blue-200">
                            <h4 className="text-sm font-medium text-gray-900 mb-3">Детальная статистика использования</h4>
                            {showUsageDetails[key.id] ? (
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                <div>
                                  <span className="text-gray-500">Использовано запросов:</span>
                                  <div className="font-semibold text-blue-600">{showUsageDetails[key.id].requests_count}</div>
                                </div>
                                <div>
                                  <span className="text-gray-500">Лимит запросов:</span>
                                  <div className="font-semibold text-blue-600">{showUsageDetails[key.id].limit_requests}</div>
                                </div>
                                <div>
                                  <span className="text-gray-500">Осталось запросов:</span>
                                  <div className="font-semibold text-green-600">{showUsageDetails[key.id].remaining_requests}</div>
                                </div>
                                <div>
                                  <span className="text-gray-500">До обновления:</span>
                                  <div className="font-semibold text-orange-600">{showUsageDetails[key.id].time_until_refresh_minutes} мин</div>
                                </div>
                              </div>
                            ) : (
                              <div className="text-center text-gray-500">Загрузка статистики...</div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ApiKeysManager;