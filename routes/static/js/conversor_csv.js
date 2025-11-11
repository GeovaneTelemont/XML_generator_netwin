// Elementos da página
    const fileInput = document.getElementById('file');
    const fileInfo = document.getElementById('fileInfo');
    const submitBtn = document.getElementById('submitBtn');
    const validationResult = document.getElementById('validationResult');
    const validationContent = document.getElementById('validationContent');

    // Criar elemento de loading
    const loadingSpinner = document.createElement('div');
    loadingSpinner.id = 'loadingSpinner';
    loadingSpinner.style.cssText = `
        display: none;
        text-align: center;
        padding: 10px;
        margin: 10px 0;
    `;
    
    const spinnerHTML = `
        <div style="display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        <span style="margin-left: 10px; color: #3498db;">Validando arquivo...</span>
        <div style="font-size: 12px; color: #666; margin-top: 5px;" id="loadingTime">Tempo: 0s</div>
    `;
    
    loadingSpinner.innerHTML = spinnerHTML;
    
    // Adicionar estilo de animação
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
    
    // Inserir o spinner após o fileInfo
    fileInfo.parentNode.insertBefore(loadingSpinner, fileInfo.nextSibling);

    // Variáveis para o temporizador
    let validationTimer;
    let seconds = 0;

    // Função para iniciar o temporizador
    function startTimer() {
        seconds = 0;
        const timeElement = document.getElementById('loadingTime');
        timeElement.textContent = `Tempo: 0s`;
        
        validationTimer = setInterval(() => {
            seconds++;
            timeElement.textContent = `Tempo: ${seconds}s`;
        }, 1000);
        
        loadingSpinner.style.display = 'block';
    }

    // Função para parar o temporizador
    function stopTimer() {
        if (validationTimer) {
            clearInterval(validationTimer);
            validationTimer = null;
        }
        loadingSpinner.style.display = 'none';
    }

    // Função para mostrar resultado da validação
    function showValidationResult(result) {
        validationResult.style.display = 'block';
        
        if (result.valido) {
            validationResult.className = 'validation-result validation-success';
            let html = `<strong>✅ Arquivo válido!</strong><br>`;
            html += `${result.total_colunas} - Colunas encontradas<br>`;
            if (result.colunas_extras && result.colunas_extras.length > 0) {
                html += `<small>Colunas extras: ${result.colunas_extras.join(', ')}</small>`;
            }
            validationContent.innerHTML = html;
            submitBtn.disabled = false;
        } else {
            validationResult.className = 'validation-result validation-error';
            let html = `<strong>❌ Arquivo inválido!</strong><br>`;
            if (result.erro) {
                html += `Erro: ${result.erro}`;
            } else {
                html += `Colunas faltantes: ${result.colunas_faltantes.join(', ')}<br>`;
                html += `Total de colunas no arquivo: ${result.total_colunas}`;
            }
            validationContent.innerHTML = html;
            submitBtn.disabled = true;
        }
    }

    // Função para validar tamanho do arquivo
    function validarTamanhoArquivo(file) {
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
        const fileSizeGB = (file.size / (1024 * 1024 * 1024)).toFixed(2);
        
        // Definir limites de tamanho
        const LIMITE_PEQUENO = 5; // 5MB
        const LIMITE_GRANDE = 100; // 100MB
        const LIMITE_MAXIMO = 2 * 1024; // 2GB
        
        if (file.size > LIMITE_MAXIMO * 1024 * 1024) {
            return {
                valido: false,
                tipo: 'tamanho',
                mensagem: `❌ Arquivo muito grande! Tamanho: ${fileSizeGB} GB (Máximo: 2GB)`
            };
        } else if (file.size > LIMITE_GRANDE * 1024 * 1024) {
            return {
                valido: true,
                tipo: 'tamanho',
                mensagem: `⚠️ Arquivo grande: ${fileSizeMB} MB. A conversão pode demorar.`
            };
        } else if (file.size < LIMITE_PEQUENO * 1024 * 1024) {
            return {
                valido: true,
                tipo: 'tamanho',
                mensagem: `📄 Arquivo pequeno: ${fileSizeMB} MB. Processamento rápido.`
            };
        } else {
            return {
                valido: true,
                tipo: 'tamanho',
                mensagem: `📊 Arquivo de tamanho moderado: ${fileSizeMB} MB.`
            };
        }
    }

    // Função para validar estrutura do arquivo via AJAX
    function validarEstruturaArquivo(file) {
        const formData = new FormData();
        formData.append('file', file);

        return fetch('/validar-csv', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            return {
                valido: data.valido,
                tipo: 'estrutura',
                dados: data
            };
        })
        .catch(error => {
            console.error('Erro na validação:', error);
            return {
                valido: false,
                tipo: 'estrutura',
                dados: {
                    valido: false,
                    erro: 'Erro ao validar estrutura do arquivo'
                }
            };
        });
    }

    // Função para atualizar informações do arquivo
    function atualizarFileInfo(mensagem, classe = '') {
        if (classe) {
            fileInfo.innerHTML = `<span class="${classe}">${mensagem}</span>`;
        } else {
            fileInfo.innerHTML = mensagem;
        }
    }

    // Event listener para mudança de arquivo
    fileInput.addEventListener('change', async function(e) {
        validationResult.style.display = 'none';
        submitBtn.disabled = true;
        stopTimer(); // Parar qualquer timer anterior
        
        if (this.files && this.files[0]) {
            const file = this.files[0];
            
            // Iniciar o temporizador e mostrar spinner
            startTimer();
            
            // Primeira validação: Estrutura do CSV
            atualizarFileInfo('🔍 Validando estrutura do arquivo CSV...', 'text-warning');
            
            try {
                // Validar estrutura (colunas)
                const resultadoEstrutura = await validarEstruturaArquivo(file);
                
                // Parar o temporizador após a validação
                stopTimer();
                
                if (!resultadoEstrutura.valido) {
                    // Se a estrutura for inválida, mostrar erro e parar aqui
                    showValidationResult(resultadoEstrutura.dados);
                    atualizarFileInfo(`📁 ${file.name} - Estrutura inválida`, 'text-danger');
                    return;
                }
                
                // Segunda validação: Tamanho do arquivo (só se a estrutura for válida)
                const resultadoTamanho = validarTamanhoArquivo(file);
                
                // Mostrar resultado da validação de estrutura
                showValidationResult(resultadoEstrutura.dados);
                
                // Atualizar informações do arquivo com resultado do tamanho
                const infoBase = `📁 Arquivo: ${file.name}`;
                if (resultadoTamanho.valido) {
                    atualizarFileInfo(`${infoBase} | ${resultadoTamanho.mensagem}`, 
                                   resultadoTamanho.mensagem.includes('⚠️') ? 'text-warning' : 'text-success');
                } else {
                    atualizarFileInfo(`${infoBase} | ${resultadoTamanho.mensagem}`, 'text-danger');
                    submitBtn.disabled = true;
                }
                
            } catch (error) {
                // Parar o temporizador em caso de erro
                stopTimer();
                
                console.error('Erro no processo de validação:', error);
                atualizarFileInfo('❌ Erro durante a validação do arquivo', 'text-danger');
                showValidationResult({
                    valido: false,
                    erro: 'Falha no processo de validação'
                });
            }
            
        } else {
            atualizarFileInfo('📁 Tamanho máximo: 2GB | Formato: CSV com separador |');
            submitBtn.disabled = true;
        }
    });

    // Prevenir envio se o botão estiver desabilitado
    document.getElementById('uploadForm').addEventListener('submit', function(e) {
        if (submitBtn.disabled) {
            e.preventDefault();
            alert('Por favor, selecione um arquivo CSV válido antes de converter.');
        }
    });

    // Parar o timer se o usuário mudar de página ou fechar
    window.addEventListener('beforeunload', function() {
        stopTimer();
    });