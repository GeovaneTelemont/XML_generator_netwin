const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const progressPercent = document.getElementById('progressPercent');
const currentCount = document.getElementById('currentCount');
const totalCount = document.getElementById('totalCount');
const logContainer = document.getElementById('logContainer');
const statusMessage = document.getElementById('statusMessage');
const statusIcon = document.getElementById('statusIcon');
const connectionStatus = document.getElementById('connectionStatus');
const statusText = document.getElementById('statusText');
const actionButtons = document.getElementById('actionButtons');
const resultButton = document.getElementById('resultButton');

let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

// Função para adicionar log
function addLog(message) {
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.innerHTML = message;
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
    
    // Limitar número de logs
    const logs = logContainer.getElementsByClassName('log-entry');
    if (logs.length > 100) {
        logContainer.removeChild(logs[0]);
    }
}

// Função para atualizar status da conexão
function updateConnectionStatus(connected) {
    if (connected) {
        connectionStatus.className = 'connection-status connected';
        statusText.innerHTML = '<i class="fas fa-wifi"></i> Conectado';
        reconnectAttempts = 0;
    } else {
        connectionStatus.className = 'connection-status disconnected';
        statusText.innerHTML = '<i class="fas fa-wifi-slash"></i> Desconectado';
    }
}

// Função para conectar ao SSE
function connectSSE() {
    updateConnectionStatus(false);
    
    const eventSource = new EventSource('/progress');

    eventSource.onopen = function() {
        console.log('Conexão SSE aberta');
        updateConnectionStatus(true);
        addLog('✅ Conectado ao servidor');
    };

    eventSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            
            // Atualizar barra de progresso
            if (data.progress !== undefined) {
                progressBar.style.width = data.progress + '%';
                progressText.textContent = Math.round(data.progress) + '%';
                progressPercent.textContent = Math.round(data.progress) + '%';
            }
            
            // Atualizar contadores
            if (data.current !== undefined) {
                currentCount.textContent = data.current.toLocaleString();
            }
            if (data.total !== undefined) {
                totalCount.textContent = data.total.toLocaleString();
            }
            
            // Atualizar mensagem de status
            if (data.message) {
                statusMessage.textContent = data.message;
                if (data.message !== 'Aguardando...' && data.message !== 'Conectado...') {
                    addLog(data.message);
                }
            }
            
            // Verificar status
            if (data.status === 'completed') {
                statusIcon.className = 'fas fa-check-circle text-success';
                statusMessage.innerHTML = '<span class="text-success">✅ Processamento concluído com sucesso!</span>';
                actionButtons.style.display = 'block';
                resultButton.style.display = 'inline-block';
                eventSource.close();
                
            } else if (data.status === 'error') {
                statusIcon.className = 'fas fa-exclamation-triangle text-danger';
                statusMessage.innerHTML = '<span class="text-danger">❌ Erro no processamento!</span>';
                actionButtons.style.display = 'block';
                resultButton.style.display = 'none';
                eventSource.close();
            }
            
        } catch (e) {
            console.error('Erro ao processar mensagem:', e);
        }
    };

    eventSource.onerror = function(event) {
        console.error('Erro na conexão SSE:', event);
        updateConnectionStatus(false);
        eventSource.close();
        
        // Tentar reconectar
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            addLog(`🔁 Tentativa de reconexão ${reconnectAttempts}/${maxReconnectAttempts}...`);
            setTimeout(connectSSE, 2000);
        } else {
            addLog('❌ Falha na conexão. Por favor, recarregue a página.');
            statusIcon.className = 'fas fa-exclamation-triangle text-danger';
            actionButtons.style.display = 'block';
        }
    };

    return eventSource;
}

// Iniciar conexão quando a página carregar
let sseConnection = connectSSE();

// Tentar reconectar se a página ficar visível novamente
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && (sseConnection.readyState === EventSource.CLOSED)) {
        addLog('🔄 Reconectando...');
        sseConnection = connectSSE();
    }
});

// Limpar recursos quando a página for fechada
window.addEventListener('beforeunload', function() {
    if (sseConnection) {
        sseConnection.close();
    }
});