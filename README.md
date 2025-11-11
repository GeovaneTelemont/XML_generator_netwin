# 🧩 Sistema de Processamento e Conversão de Arquivos CSV

Um sistema **web Flask** para geração de arquivos **XML** a partir de **CSV**, de acordo com a estrutura de importação do sistema **Netwin**.

---

## 📋 Funcionalidades

### 🏗️ Gerador de XML para Edificações
- Processa arquivos CSV para gerar XML no formato Netwin  
- Suporte a **2 ou 3 complementos de endereço**  
- Conversão automática de **coordenadas geográficas**  
- Mapeamento inteligente de **códigos de complementos**  
- Geração de **arquivos ZIP** organizados por pasta  

### 🔄 Conversor de CSV para Power Query
- Converte `Enderecos_Totais_CO.csv` para formato **Power Query**  
- Processamento otimizado para arquivos grandes (**até 2GB**)  
- Validação de estrutura de colunas  
- Formatação automática de dados  
- Interface web com **progresso em tempo real**  

---

## 🚀 Instalação e Execução

### 🔧 Pré-requisitos
- **Python 3.13+**  
- **Poetry** (gerenciador de dependências)

### 🧰 Instalação

Clone o repositório:
```bash
git clone <url-do-repositorio>
cd geradorxml
```

Instale as dependências:
```bash
poetry install
```

Ative o ambiente virtual:
```bash
poetry shell
```

Execute a aplicação:
```bash
python app.py
```

Acesse no navegador:
```
http://localhost:5000
```

---

## 📁 Estrutura do Projeto
```
geradorxml/
├── app.py                  # Aplicação principal Flask
├── pyproject.toml          # Configuração do Poetry
├── README.md               # Este arquivo
├── templates/              # Templates HTML
│   ├── index.html          # Página inicial
│   ├── conversor_csv.html  # Interface do conversor
│   ├── progresso.html      # Página de progresso
│   ├── resultado.html      # Resultado do processamento
│   └── sobre.html          # Página sobre o sistema
├── static/
│   └── img/                # Imagens e ícones
├── downloads/              # Arquivos gerados para download
├── roteiros/               # Arquivos de roteiro para conversão
│   ├── roteiro_aparecida.xlsx
│   └── roteiro_goiania.xlsx
└── csv_modelo/             # Modelos de CSV
    └── modelo.csv
```

---

## 🛠️ Dependências

| Pacote | Versão | Descrição |
|--------|---------|-----------|
| Flask | >=3.1.2,<4.0.0 | Framework web |
| Pandas | >=2.3.3,<3.0.0 | Processamento de dados |
| OpenPyXL | >=3.1.5,<4.0.0 | Leitura de arquivos Excel |
| Python-dotenv | >=0.9.9,<0.10.0 | Gerenciamento de variáveis de ambiente |

---

## 🔧 Configuração

### ⚙️ Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=sua_chave_secreta_aqui
FLASK_ENV=development
```

### 📜 Arquivos de Roteiro
O sistema requer os seguintes arquivos na pasta `roteiros/`:
```
roteiro_aparecida.xlsx
roteiro_goiania.xlsx
```

---

## 📊 Uso

### Página Principal (`/`)
- Upload de CSV para geração de XML  
- Download do modelo CSV  
- Acesso ao conversor de CSV  

### 🧱 Gerador de XML
**Colunas obrigatórias no CSV:**
```
COMPLEMENTO, COMPLEMENTO2, RESULTADO,
LATITUDE, LONGITUDE, COD_ZONA,
LOCALIDADE, LOGRADOURO, BAIRRO,
MUNICIPIO, UF, COD_LOGRADOURO,
ID_ENDERECO, ID_ROTEIRO, ID_LOCALIDADE,
CEP, NUM_FACHADA, COD_SURVEY,
QUANTIDADE_UMS, UCS_RESIDENCIAIS, UCS_COMERCIAIS
```

### ⚙️ Conversor de CSV (`/conversor-csv`)
- Processa `Enderecos_Totais_CO.csv`  
- Validação em tempo real  
- Barra de progresso via **SSE**  
- Download do arquivo convertido  

---

## 🎯 Desenvolvimento

### 🔩 Comandos Poetry Úteis
```bash
# Instalar dependências
poetry install

# Ativar ambiente virtual
poetry shell

# Adicionar nova dependência
poetry add nome-pacote

# Executar aplicação
python app.py
```

---

## 📝 Notas Técnicas
- Suporte a arquivos de até **2GB**  
- Processamento em **chunks** para otimização de memória  
- Validação assíncrona no cliente  
- Encodings suportados: `UTF-8`, `Latin-1`, `ISO-8859-1`  

---

## 🐛 Solução de Problemas

| Problema | Causa Provável | Solução |
|-----------|----------------|----------|
| Arquivos de roteiro não encontrados | Pasta `roteiros/` ausente ou incorreta | Verifique o caminho e os nomes dos arquivos |
| Colunas faltantes | Estrutura do CSV inválida | Use o validador integrado |
| Memória insuficiente | Arquivo muito grande | O sistema processa em *chunks* automaticamente |

📜 **Logs**
- Logs detalhados no console  
- Mensagens de progresso em tempo real  
- Validação de estrutura antes do processamento  

---

## 📄 Licença
Projeto desenvolvido para uso interno da **Telemont**.

👤 **Desenvolvido por:** Geovane Carvalho  
📧 **Email:** geovane.carvalho@telemont.com.br  
🔖 **Versão:** 0.1.0
