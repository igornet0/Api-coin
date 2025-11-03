const API_BASE_URL = window.location.origin;

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU');
}

function formatNumber(num) {
    if (!num && num !== 0) return '-';
    return new Intl.NumberFormat('ru-RU', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 8
    }).format(num);
}

// Tab management
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Add active class to button
    event.target.classList.add('active');
    
    // Load data for the tab
    if (tabName === 'coins') {
        loadCoins();
    } else if (tabName === 'news') {
        loadNews();
    } else if (tabName === 'parsing') {
        loadTasks();
        // Загружаем монеты для парсинга при открытии вкладки
        setTimeout(() => {
            loadCoinsForParsing();
        }, 50);
    }
}

// Coins API
async function loadCoins() {
    const tbody = document.getElementById('coins-tbody');
    const filterParsed = document.getElementById('filter-parsed').checked;
    
    tbody.innerHTML = '<tr><td colspan="9" class="loading">Загрузка...</td></tr>';
    
    try {
        const url = filterParsed 
            ? `${API_BASE_URL}/coins?parsed=true`
            : `${API_BASE_URL}/coins`;
            
        const response = await fetch(url);
        if (!response.ok) throw new Error('Ошибка загрузки данных');
        
        const coins = await response.json();
        
        if (coins.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">Нет данных</td></tr>';
            return;
        }
        
        tbody.innerHTML = coins.map(coin => `
            <tr>
                <td>${coin.id}</td>
                <td><strong>${coin.name}</strong></td>
                <td>${formatNumber(coin.price_now)}</td>
                <td>${formatNumber(coin.max_price_now)}</td>
                <td>${formatNumber(coin.min_price_now)}</td>
                <td>${formatNumber(coin.open_price_now)}</td>
                <td>${formatNumber(coin.volume_now)}</td>
                <td>${coin.parsed ? '<span class="badge badge-success">Активна</span>' : '<span class="badge badge-danger">Неактивна</span>'}</td>
                <td>
                    <button class="btn btn-secondary btn-small" onclick="showCoinDetails('${coin.name}')">
                        Детали
                    </button>
                    <button class="btn btn-success btn-small" onclick="exportCoinCSV('${coin.name}')" style="margin-left: 5px;" title="Выгрузить CSV">
                        📥 CSV
                    </button>
                    <button class="btn btn-danger btn-small" onclick="deleteCoin('${coin.name}')" style="margin-left: 5px;" title="Удалить монету">
                        🗑️
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center" style="color: var(--danger-color);">Ошибка: ${error.message}</td></tr>`;
        showNotification('Ошибка загрузки монет', 'error');
    }
}

async function showCoinDetails(coinName) {
    const modal = document.getElementById('coin-details');
    const content = document.getElementById('coin-details-content');
    
    content.innerHTML = '<div class="loading">Загрузка...</div>';
    modal.style.display = 'block';
    
    try {
        // Get coin info
        const coinResponse = await fetch(`${API_BASE_URL}/coins/${coinName}`);
        if (!coinResponse.ok) throw new Error('Ошибка загрузки монеты');
        
        const coin = await coinResponse.json();
        
        // Get timeseries
        const tsResponse = await fetch(`${API_BASE_URL}/coins/${coinName}/timeseries`);
        const timeseries = tsResponse.ok ? await tsResponse.json() : [];
        
        content.innerHTML = `
            <div style="margin-bottom: 20px;">
                <h3 style="display: flex; align-items: center; gap: 10px;">
                    ${coin.name}
                    <button class="btn btn-success btn-small" onclick="exportCoinCSV('${coin.name}')" title="Выгрузить CSV">
                        📥 Выгрузить CSV
                    </button>
                </h3>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 15px;">
                    <div>
                        <strong>Текущая цена:</strong> ${formatNumber(coin.price_now)}
                    </div>
                    <div>
                        <strong>Максимум:</strong> ${formatNumber(coin.max_price_now)}
                    </div>
                    <div>
                        <strong>Минимум:</strong> ${formatNumber(coin.min_price_now)}
                    </div>
                    <div>
                        <strong>Объем:</strong> ${formatNumber(coin.volume_now)}
                    </div>
                </div>
            </div>
        `;
        
        if (timeseries.length > 0) {
            const tsList = document.getElementById('timeseries-list');
            tsList.innerHTML = `
                <h4 style="margin-top: 20px; margin-bottom: 10px;">Временные ряды:</h4>
                <div style="display: grid; gap: 10px;">
                    ${timeseries.map(ts => `
                        <div style="padding: 10px; background: var(--bg-color); border-radius: 6px;">
                            <strong>${ts.timestamp}</strong> - ${ts.path_dataset}
                            <button class="btn btn-secondary btn-small" onclick="loadTimeseriesData(${ts.id})" style="float: right;">
                                Данные
                            </button>
                        </div>
                    `).join('')}
                </div>
            `;
        }
    } catch (error) {
        content.innerHTML = `<div style="color: var(--danger-color);">Ошибка: ${error.message}</div>`;
    }
}

async function loadTimeseriesData(timeseriesId) {
    try {
        const response = await fetch(`${API_BASE_URL}/coins/timeseries/${timeseriesId}/data`);
        if (!response.ok) throw new Error('Ошибка загрузки данных');
        
        const data = await response.json();
        showNotification(`Загружено ${data.length} записей`, 'success');
        
        // Можно открыть модальное окно с данными или экспортировать
        console.log('Timeseries data:', data);
    } catch (error) {
        showNotification('Ошибка загрузки данных временного ряда', 'error');
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// News API
async function loadNews() {
    const container = document.getElementById('news-container');
    const typeFilter = document.getElementById('news-type-filter').value;
    const limit = document.getElementById('news-limit').value || 50;
    
    container.innerHTML = '<div class="loading">Загрузка новостей...</div>';
    
    try {
        let url = `${API_BASE_URL}/news?limit=${limit}`;
        if (typeFilter) {
            url += `&type=${typeFilter}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Ошибка загрузки новостей');
        
        const news = await response.json();
        
        if (news.length === 0) {
            container.innerHTML = '<div class="text-center">Нет новостей</div>';
            return;
        }
        
        container.innerHTML = news.map(item => `
            <div class="news-card">
                <h3>${item.title}</h3>
                <div class="news-meta">
                    <span>📅 ${formatDate(item.date)}</span>
                    <span>📌 ${item.type}</span>
                    <span>🔗 ID: ${item.id_url}</span>
                </div>
                <div class="news-text">${item.text.substring(0, 200)}...</div>
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = `<div class="text-center" style="color: var(--danger-color);">Ошибка: ${error.message}</div>`;
        showNotification('Ошибка загрузки новостей', 'error');
    }
}

// Parsing API
function toggleCountField() {
    const manualStop = document.getElementById('manual-stop').checked;
    const countField = document.getElementById('count');
    if (manualStop) {
        countField.disabled = true;
        countField.style.opacity = '0.5';
    } else {
        countField.disabled = false;
        countField.style.opacity = '1';
    }
}

async function loadCoinsForParsing() {
    const container = document.getElementById('coins-checklist');
    
    if (!container) {
        console.error('Element coins-checklist not found');
        return;
    }
    
    container.innerHTML = '<div class="loading">Загрузка монет...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/coins?parsed=true`);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Ошибка загрузки монет: ${response.status} ${response.statusText} - ${errorText}`);
        }
        
        const coins = await response.json();
        
        if (!Array.isArray(coins)) {
            throw new Error('Ожидался массив монет, получено: ' + typeof coins);
        }
        
        if (coins.length === 0) {
            container.innerHTML = '<div class="text-center">Нет активных монет</div>';
            return;
        }
        
        container.innerHTML = coins.map(coin => {
            const coinName = coin.name || coin;
            return `
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" value="${coinName}" class="coin-checkbox" style="margin-right: 5px;">
                    <span>${coinName}</span>
                </label>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading coins for parsing:', error);
        container.innerHTML = `<div class="text-center" style="color: var(--danger-color);">Ошибка: ${error.message}</div>`;
    }
}

async function startParsing(event) {
    if (event) {
        event.preventDefault();
    }
    
    // Получаем выбранные монеты
    const selectedCoins = Array.from(document.querySelectorAll('.coin-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    const manualStop = document.getElementById('manual-stop').checked;
    
    const formData = {
        parser_type: document.getElementById('parser-type').value,
        count: parseInt(document.getElementById('count').value) || 100,
        time_parser: document.getElementById('time-parser').value,
        pause: parseFloat(document.getElementById('pause').value),
        miss: document.getElementById('miss').checked,
        last_launch: document.getElementById('last-launch').checked,
        clear: document.getElementById('clear').checked,
        save: document.getElementById('save').checked,
        save_type: document.getElementById('save-type').value,
        coins: selectedCoins.length > 0 ? selectedCoins : null,
        manual_stop: manualStop
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/parsing/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка запуска парсинга');
        }
        
        const result = await response.json();
        showNotification(`Задача ${result.task_id} запущена`, 'success');
        
        // Store task ID
        const activeTasks = JSON.parse(localStorage.getItem('activeTasks') || '[]');
        if (!activeTasks.includes(result.task_id)) {
            activeTasks.push(result.task_id);
            localStorage.setItem('activeTasks', JSON.stringify(activeTasks));
        }
        
        // Reset form
        document.getElementById('parsing-form').reset();
        
        // Reload tasks
        setTimeout(() => loadTasks(), 1000);
        
    } catch (error) {
        showNotification(`Ошибка: ${error.message}`, 'error');
    }
}

async function loadTasks() {
    const container = document.getElementById('tasks-container');
    container.innerHTML = '<div class="loading">Загрузка задач...</div>';
    
    try {
        // Получаем список задач из БД
        const response = await fetch(`${API_BASE_URL}/parsing/tasks?limit=50`);
        if (!response.ok) throw new Error('Ошибка получения списка задач');
        
        const tasks = await response.json();
        
        if (!tasks || tasks.length === 0) {
            container.innerHTML = '<div class="loading">Нет задач парсинга</div>';
            return;
        }
        
        // Для каждой задачи получаем детальную информацию
        const tasksHTML = await Promise.all(tasks.map(async (task) => {
            try {
                const statusResponse = await fetch(`${API_BASE_URL}/parsing/status/${task.task_id}`);
                if (!statusResponse.ok) throw new Error('Ошибка получения статуса');
                
                const status = await statusResponse.json();
                
                // Форматируем время
                const timeInfo = [];
                if (status.created_at) {
                    timeInfo.push(`<div><strong>📅 Создана:</strong> ${formatDate(status.created_at)}</div>`);
                }
                if (status.started_at) {
                    timeInfo.push(`<div><strong>▶️ Запущена:</strong> ${formatDate(status.started_at)}</div>`);
                }
                if (status.completed_at) {
                    timeInfo.push(`<div><strong>✅ Завершена:</strong> ${formatDate(status.completed_at)}</div>`);
                }
                
                // Вычисляем длительность, если задача завершена
                let durationDisplay = '';
                if (status.started_at && status.completed_at) {
                    const start = new Date(status.started_at);
                    const end = new Date(status.completed_at);
                    const duration = Math.round((end - start) / 1000); // секунды
                    const minutes = Math.floor(duration / 60);
                    const seconds = duration % 60;
                    durationDisplay = `<div style="margin-top: 5px; color: var(--text-secondary); font-size: 0.9em;">
                        <strong>⏱️ Длительность:</strong> ${minutes}м ${seconds}с
                    </div>`;
                }
                
                const errorDisplay = status.error ? `
                    <div style="margin-top: 10px; padding: 10px; background: rgba(220, 53, 69, 0.1); border-left: 3px solid var(--danger-color); border-radius: 4px;">
                        <div style="color: var(--danger-color); font-weight: bold; margin-bottom: 5px;">⚠️ Ошибка:</div>
                        <div style="color: var(--danger-color); white-space: pre-wrap; word-break: break-word;">${status.error}</div>
                        ${status.traceback ? `
                            <details style="margin-top: 10px;">
                                <summary style="cursor: pointer; color: var(--text-secondary); font-size: 0.9em;">Показать детали ошибки</summary>
                                <pre style="margin-top: 5px; padding: 10px; background: rgba(0, 0, 0, 0.2); border-radius: 4px; overflow-x: auto; font-size: 0.85em; white-space: pre-wrap; word-break: break-word;">${status.traceback}</pre>
                            </details>
                        ` : ''}
                    </div>
                ` : '';
                
                const messageDisplay = status.message ? `
                    <div style="margin-top: 5px; color: var(--text-secondary); font-size: 0.9em;">
                        <strong>💬 Сообщение:</strong> ${status.message}
                    </div>
                ` : '';
                
                const resultDisplay = status.result && status.status === 'completed' ? `
                    <div style="margin-top: 10px; padding: 10px; background: rgba(40, 167, 69, 0.1); border-left: 3px solid #28a745; border-radius: 4px;">
                        <div style="font-weight: bold; margin-bottom: 5px;">✅ Результат:</div>
                        <pre style="margin: 0; white-space: pre-wrap; word-break: break-word; font-size: 0.9em;">${JSON.stringify(status.result, null, 2)}</pre>
                    </div>
                ` : status.result ? `
                    <div style="margin-top: 10px; padding: 10px; background: rgba(0, 123, 255, 0.1); border-left: 3px solid #007bff; border-radius: 4px;">
                        <div style="font-weight: bold; margin-bottom: 5px;">📊 Прогресс:</div>
                        <pre style="margin: 0; white-space: pre-wrap; word-break: break-word; font-size: 0.9em;">${JSON.stringify(status.result, null, 2)}</pre>
                    </div>
                ` : '';
                
                const parserTypeDisplay = task.parser_type ? `
                    <div style="margin-top: 5px; color: var(--text-secondary); font-size: 0.9em;">
                        <strong>🔧 Парсер:</strong> ${task.parser_type}
                    </div>
                ` : '';
                
                const coinsDisplay = task.coins && task.coins.length > 0 ? `
                    <div style="margin-top: 5px; color: var(--text-secondary); font-size: 0.9em;">
                        <strong>🪙 Монеты:</strong> ${task.coins.join(', ')}
                    </div>
                ` : '';
                
                return `
                    <div class="task-card">
                        <h4>
                            Задача ${task.task_id.substring(0, 8)}...
                            <span class="task-status badge ${getStatusBadgeClass(status.status)}">${getStatusText(status.status)}</span>
                            ${task.manual_stop ? '<span class="badge badge-warning" style="margin-left: 5px;">Ручная остановка</span>' : ''}
                        </h4>
                        <div class="task-info">
                            <div><strong>Статус:</strong> ${getStatusText(status.status)}</div>
                            ${parserTypeDisplay}
                            ${coinsDisplay}
                            ${timeInfo.join('')}
                            ${durationDisplay}
                            ${messageDisplay}
                            ${resultDisplay}
                            ${errorDisplay}
                        </div>
                        <div class="task-actions">
                            <button class="btn btn-secondary btn-small" onclick="checkTaskStatus('${task.task_id}')">
                                🔄 Обновить
                            </button>
                            ${status.status === 'in_progress' || status.status === 'pending' ? `
                                <button class="btn btn-danger btn-small" onclick="stopTask('${task.task_id}')">
                                    ⏹️ Остановить
                                </button>
                            ` : ''}
                        </div>
                    </div>
                `;
            } catch (error) {
                return `<div class="task-card" style="color: var(--danger-color);">Ошибка загрузки задачи ${task.task_id}: ${error.message}</div>`;
            }
        }));
        
        container.innerHTML = tasksHTML.join('');
        
        // Обновляем localStorage с активными задачами для обратной совместимости
        const activeTaskIds = tasks
            .filter(t => t.status === 'pending' || t.status === 'in_progress')
            .map(t => t.task_id);
        localStorage.setItem('activeTasks', JSON.stringify(activeTaskIds));
        
    } catch (error) {
        container.innerHTML = `<div class="loading" style="color: var(--danger-color);">Ошибка загрузки задач: ${error.message}</div>`;
        console.error('Error loading tasks:', error);
        showNotification('Ошибка загрузки задач', 'error');
    }
}

function getStatusBadgeClass(status) {
    switch(status) {
        case 'completed': return 'badge-success';
        case 'in_progress': case 'pending': return 'badge-info';
        case 'error': case 'failure': return 'badge-danger';
        default: return 'badge-warning';
    }
}

function getStatusText(status) {
    const statusMap = {
        'pending': 'Ожидает',
        'in_progress': 'Выполняется',
        'completed': 'Завершено',
        'error': 'Ошибка',
        'failure': 'Провалено'
    };
    return statusMap[status] || status;
}

async function checkTaskStatus(taskId) {
    try {
        const response = await fetch(`${API_BASE_URL}/parsing/status/${taskId}`);
        if (!response.ok) throw new Error('Ошибка получения статуса');
        
        const status = await response.json();
        showNotification(`Статус: ${status.status}`, 'info');
        
        // Reload tasks
        loadTasks();
    } catch (error) {
        showNotification(`Ошибка: ${error.message}`, 'error');
    }
}

async function stopTask(taskId) {
    if (!confirm('Вы уверены, что хотите остановить эту задачу?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/parsing/stop/${taskId}`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Ошибка остановки задачи');
        
        const result = await response.json();
        showNotification('Задача остановлена', 'success');
        
        // Remove from active tasks
        const activeTasks = JSON.parse(localStorage.getItem('activeTasks') || '[]');
        const updated = activeTasks.filter(id => id !== taskId);
        localStorage.setItem('activeTasks', JSON.stringify(updated));
        
        // Reload tasks
        loadTasks();
    } catch (error) {
        showNotification(`Ошибка: ${error.message}`, 'error');
    }
}


// Add Coin functions
function showAddCoinModal() {
    document.getElementById('add-coin-modal').style.display = 'block';
    document.getElementById('coin-name').value = '';
    document.getElementById('coin-price').value = '0';
    document.getElementById('coin-parsed').checked = true;
}

async function addCoin(event) {
    event.preventDefault();
    
    const name = document.getElementById('coin-name').value.trim().toUpperCase();
    const price = parseFloat(document.getElementById('coin-price').value) || 0;
    const parsed = document.getElementById('coin-parsed').checked;
    
    if (!name) {
        showNotification('Введите название монеты', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/coins/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                price_now: price,
                parsed: parsed
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка добавления монеты');
        }
        
        const coin = await response.json();
        showNotification(`Монета ${coin.name} успешно добавлена`, 'success');
        closeModal('add-coin-modal');
        loadCoins();
        
    } catch (error) {
        showNotification(`Ошибка: ${error.message}`, 'error');
    }
}

async function uploadCoinsCSV(event) {
    const file = event.target.files[0];
    
    if (!file) {
        return;
    }
    
    if (!file.name.endsWith('.csv')) {
        showNotification('Файл должен быть в формате CSV', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showNotification('Загрузка файла...', 'info');
        
        const response = await fetch(`${API_BASE_URL}/coins/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка загрузки файла');
        }
        
        const result = await response.json();
        
        let message = `Загружено: ${result.added} монет добавлено`;
        if (result.skipped > 0) {
            message += `, ${result.skipped} пропущено (уже существуют)`;
        }
        if (result.errors.length > 0) {
            message += `, ${result.errors.length} ошибок`;
        }
        
        showNotification(message, result.errors.length > 0 ? 'error' : 'success');
        
        if (result.errors.length > 0) {
            console.error('Ошибки при загрузке:', result.errors);
        }
        
        // Сброс input
        event.target.value = '';
        
        // Обновляем список монет
        loadCoins();
        
    } catch (error) {
        showNotification(`Ошибка: ${error.message}`, 'error');
        event.target.value = '';
    }
}

async function exportCoinCSV(coinName) {
    try {
        showNotification(`Выгрузка CSV для ${coinName}...`, 'info');
        
        const response = await fetch(`${API_BASE_URL}/coins/${coinName}/export-csv`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка выгрузки CSV');
        }
        
        // Получаем blob из ответа
        const blob = await response.blob();
        
        // Создаем ссылку для скачивания
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${coinName}_data_timeseries.csv`;
        document.body.appendChild(a);
        a.click();
        
        // Очищаем
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showNotification(`CSV файл для ${coinName} успешно выгружен`, 'success');
        
    } catch (error) {
        showNotification(`Ошибка: ${error.message}`, 'error');
    }
}

async function deleteCoin(coinName) {
    if (!confirm(`Вы уверены, что хотите удалить монету ${coinName}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/coins/${coinName}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка удаления монеты');
        }
        
        const result = await response.json();
        showNotification(`Монета ${coinName} удалена`, 'success');
        loadCoins();
        
    } catch (error) {
        showNotification(`Ошибка: ${error.message}`, 'error');
    }
}

// Refresh all data
function refreshAll() {
    const activeTab = document.querySelector('.tab-content.active');
    if (activeTab.id === 'coins-tab') {
        loadCoins();
    } else if (activeTab.id === 'news-tab') {
        loadNews();
    } else if (activeTab.id === 'parsing-tab') {
        loadTasks();
    }
    showNotification('Данные обновлены', 'success');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadCoins();
    
    // Загружаем монеты для парсинга после небольшой задержки, чтобы убедиться, что DOM готов
    setTimeout(() => {
        loadCoinsForParsing();
    }, 100);
    
    // Auto-refresh tasks every 10 seconds
    setInterval(() => {
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab && activeTab.id === 'parsing-tab') {
            loadTasks();
        }
    }, 10000);
});

