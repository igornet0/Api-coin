import { useState, useEffect } from 'react';
import apiService from '../services/api';

const ApiRequests = () => {
  const [apiKeys, setApiKeys] = useState([]);
  const [selectedKey, setSelectedKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [requestType, setRequestType] = useState('coins');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [coinId, setCoinId] = useState('');

  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    try {
      const keys = await apiService.getApiKeys();
      const activeKeys = keys.filter(key => key.is_active);
      setApiKeys(activeKeys);
      if (activeKeys.length > 0) {
        setSelectedKey(activeKeys[0].id);
      }
    } catch (err) {
      setError('Ошибка загрузки API ключей: ' + err.message);
    }
  };

  const executeRequest = async () => {
    if (!selectedKey) {
      setError('Выберите API ключ');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      let response;
      
      switch (requestType) {
        case 'coins':
          response = await apiService.getCoins();
          break;
        case 'coin':
          if (!coinId) {
            setError('Введите ID монеты');
            return;
          }
          response = await apiService.getCoin(coinId);
          break;
        default:
          setError('Неизвестный тип запроса');
          return;
      }
      
      setResult(response);
    } catch (err) {
      setError('Ошибка выполнения запроса: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatJson = (obj) => {
    return JSON.stringify(obj, null, 2);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header Section */}
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          Выполнение API запросов
        </h2>
        <p className="text-gray-600 max-w-3xl">
          Используйте ваши сохраненные API ключи для выполнения запросов к криптовалютным биржам 
          и получения актуальной информации о монетах.
        </p>
      </div>
      
      {apiKeys.length === 0 ? (
        <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 p-12 text-center">
          <div className="mx-auto h-24 w-24 bg-yellow-100 rounded-full flex items-center justify-center mb-6">
            <svg className="h-12 w-12 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-3">Нет активных API ключей</h3>
          <p className="text-gray-600 mb-6">
            У вас нет активных API ключей. Сначала добавьте и активируйте API ключ в разделе управления ключами.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-6 py-3 rounded-xl font-medium transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            Обновить страницу
          </button>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Request Configuration */}
          <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 p-8">
            <div className="mb-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Настройки запроса</h3>
              <p className="text-gray-600">Выберите API ключ и тип запроса для выполнения</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API ключ
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m0 0a2 2 0 012 2 2 2 0 00-2-2m-2-2v2m0 6V9.5m0 0a2 2 0 012-2 2 2 0 00-2 2z" />
                    </svg>
                  </div>
                  <select
                    value={selectedKey}
                    onChange={(e) => setSelectedKey(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white appearance-none"
                  >
                    {apiKeys.map((key) => (
                      <option key={key.id} value={key.id}>
                        {key.name} (...{key.api_key.substring(key.api_key.length - 4)})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Тип запроса
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <select
                    value={requestType}
                    onChange={(e) => setRequestType(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white appearance-none"
                  >
                    <option value="coins">Получить список монет</option>
                    <option value="coin">Получить информацию о монете</option>
                  </select>
                </div>
              </div>

              {requestType === 'coin' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ID монеты
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                      </svg>
                    </div>
                    <input
                      type="number"
                      value={coinId}
                      onChange={(e) => setCoinId(e.target.value)}
                      className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white"
                      placeholder="Введите ID монеты"
                    />
                  </div>
                </div>
              )}
            </div>
            
            <button
              onClick={executeRequest}
              disabled={loading}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-3 rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              {loading ? (
                <div className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Выполняется...
                </div>
              ) : (
                <div className="flex items-center">
                  <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Выполнить запрос
                </div>
              )}
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <div className="flex">
                <svg className="h-5 w-5 text-red-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="text-sm text-red-700">{error}</div>
              </div>
            </div>
          )}

          {/* Results Display */}
          {result && (
            <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 overflow-hidden">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">Результат запроса</h3>
                    <div className="flex items-center">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 border border-green-200">
                        <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                        Успешно
                      </span>
                      <span className="ml-4 text-sm text-gray-500">
                        {new Date().toLocaleString('ru-RU')}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Statistics Cards */}
              {result.coins && (
                <div className="p-6 border-b border-gray-200">
                  <h4 className="text-lg font-medium text-gray-900 mb-4">Статистика</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-100">
                      <div className="flex items-center">
                        <div className="h-10 w-10 bg-blue-500 rounded-lg flex items-center justify-center mr-3">
                          <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Всего монет</p>
                          <p className="text-2xl font-bold text-blue-600">{result.count || result.coins.length}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-gradient-to-r from-emerald-50 to-teal-50 p-4 rounded-xl border border-emerald-100">
                      <div className="flex items-center">
                        <div className="h-10 w-10 bg-emerald-500 rounded-lg flex items-center justify-center mr-3">
                          <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Пропущено</p>
                          <p className="text-2xl font-bold text-emerald-600">{result.skip || 0}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-4 rounded-xl border border-purple-100">
                      <div className="flex items-center">
                        <div className="h-10 w-10 bg-purple-500 rounded-lg flex items-center justify-center mr-3">
                          <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Лимит</p>
                          <p className="text-2xl font-bold text-purple-600">{result.limit || 'Нет'}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Single Coin Info */}
              {result.coin && (
                <div className="p-6 border-b border-gray-200">
                  <h4 className="text-lg font-medium text-gray-900 mb-4">Информация о монете</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-100">
                      <p className="text-sm text-gray-600 mb-1">Название</p>
                      <p className="text-xl font-bold text-blue-600">{result.coin.name}</p>
                    </div>
                    
                    <div className="bg-gradient-to-r from-emerald-50 to-teal-50 p-4 rounded-xl border border-emerald-100">
                      <p className="text-sm text-gray-600 mb-1">Текущая цена</p>
                      <p className="text-xl font-bold text-emerald-600">${result.coin.price_now || 'N/A'}</p>
                    </div>
                    
                    <div className="bg-gradient-to-r from-red-50 to-pink-50 p-4 rounded-xl border border-red-100">
                      <p className="text-sm text-gray-600 mb-1">Макс. цена</p>
                      <p className="text-xl font-bold text-red-600">${result.coin.max_price_now || 'N/A'}</p>
                    </div>
                    
                    <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-4 rounded-xl border border-yellow-100">
                      <p className="text-sm text-gray-600 mb-1">Объем</p>
                      <p className="text-xl font-bold text-yellow-600">{result.coin.volume_now || 'N/A'}</p>
                    </div>
                  </div>
                </div>
              )}
              
              {/* JSON Data */}
              <div className="p-6">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Полные данные (JSON)</h4>
                <div className="bg-gray-900 rounded-xl p-4 overflow-auto max-h-96">
                  <pre className="text-sm text-green-400 whitespace-pre-wrap font-mono">
                    {formatJson(result)}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ApiRequests;