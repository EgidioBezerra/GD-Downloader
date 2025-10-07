# Google Drive Downloader - Instalação e Uso

## 📋 requirements.txt

Crie um arquivo `requirements.txt` com o seguinte conteúdo:

```
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.100.0
requests>=2.31.0
urllib3>=2.0.0
tqdm>=4.66.0
rich>=13.7.0
selenium>=4.15.0
webdriver-manager>=4.0.1
Pillow>=10.0.0
```

## 🔧 Instalação

### 1. Instalar Python
Certifique-se de ter Python 3.8 ou superior instalado.

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Instalar FFmpeg (necessário para vídeos view-only)

**Windows:**
- Baixe do site oficial: https://ffmpeg.org/download.html
- Extraia e adicione ao PATH do sistema

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Verificar instalação:**
```bash
ffmpeg -version
```

### 4. Configurar credenciais do Google Drive

1. Acesse: https://console.cloud.google.com/
2. Crie um novo projeto ou selecione um existente
3. Ative a API do Google Drive:
   - Vá em "APIs e Serviços" > "Biblioteca"
   - Procure por "Google Drive API"
   - Clique em "Ativar"
4. Crie credenciais OAuth 2.0:
   - Vá em "APIs e Serviços" > "Credenciais"
   - Clique em "Criar Credenciais" > "ID do cliente OAuth"
   - Escolha "Aplicativo para computador"
   - Baixe o arquivo JSON
5. Renomeie o arquivo baixado para `credentials.json`
6. Coloque `credentials.json` na mesma pasta dos scripts

## 🚀 Uso

### Comando básico
```bash
python main.py "URL_DA_PASTA" ./downloads
```

### Exemplos

**Download padrão com 8 workers:**
```bash
python main.py "https://drive.google.com/drive/folders/FOLDER_ID" ./downloads --workers 8
```

**Download apenas de arquivos view-only:**
```bash
python main.py "URL_DA_PASTA" ./downloads --only-view-only
```

**Download de vídeos com aceleração NVIDIA:**
```bash
python main.py "URL_DA_PASTA" ./downloads --gpu nvidia
```

**Download com aceleração Intel Quick Sync:**
```bash
python main.py "URL_DA_PASTA" ./downloads --gpu intel
```

**Download com aceleração AMD:**
```bash
python main.py "URL_DA_PASTA" ./downloads --gpu amd
```

**Debug de vídeos (salva HTML para análise):**
```bash
python main.py "URL_DA_PASTA" ./downloads --debug-html
```

## 📝 Parâmetros

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `folder_url` | URL da pasta do Google Drive (obrigatório) | - |
| `destination` | Caminho local para salvar os arquivos (obrigatório) | - |
| `--workers` | Número de downloads simultâneos | 4 |
| `--gpu` | Aceleração GPU para vídeos (nvidia/intel/amd) | Nenhum |
| `--only-view-only` | Baixa apenas arquivos view-only | False |
| `--debug-html` | Salva HTML das páginas para debug | False |

## 🎯 Tipos de Arquivos Suportados

### ✅ Download Automático
- Arquivos padrão (com permissão de download)
- Google Docs (exportados como PDF)
- Google Sheets (exportados como PDF)
- Google Slides (exportados como PDF)

### 🔐 View-Only Automático
- **Vídeos**: Baixados via FFmpeg com stream HLS

### 🖱️ View-Only Manual (requer interação)
- **PDFs**: Requer login manual no navegador

### ❌ Não Suportados
- Atalhos do Google Drive
- Google Forms
- Outros tipos de arquivos do Google Workspace não listados

## 🐛 Troubleshooting

### Erro: "Credenciais inválidas"
**Solução:** Delete o arquivo `token.json` e execute novamente

### Erro: FFmpeg não encontrado
**Solução:** Certifique-se de que o FFmpeg está instalado e no PATH do sistema

### Erro: "Não foi possível encontrar o manifesto HLS"
**Solução:** 
1. Use a flag `--debug-html` para salvar o HTML
2. Verifique o arquivo `debug_page_*.html` gerado
3. O vídeo pode ter proteções adicionais que impedem o download

### Vídeos não baixam ou ficam corrompidos
**Soluções:**
- Tente usar aceleração GPU: `--gpu nvidia` (ou intel/amd)
- Verifique se o FFmpeg está atualizado
- Alguns vídeos view-only têm proteções que não podem ser contornadas

### Downloads lentos
**Soluções:**
- Aumente o número de workers: `--workers 8`
- Verifique sua conexão de internet
- Note que vídeos view-only são processados sequencialmente (1 por vez)

### Erro 403 (Forbidden)
**Causa:** O arquivo realmente não tem permissão de download
**Solução:** Não há solução técnica - é uma restrição imposta pelo proprietário

## 📊 Arquivos Gerados

- `download.log`: Log detalhado de todas as operações
- `token.json`: Token de autenticação (gerado automaticamente)
- `debug_page_*.html`: HTMLs de debug (se `--debug-html` for usado)

## ⚠️ Avisos Importantes

1. **Respeite os direitos autorais**: Use apenas para arquivos que você tem permissão para baixar
2. **Termos de Serviço**: O download de arquivos view-only pode violar os ToS do Google Drive
3. **Rate Limits**: Downloads em massa podem ativar limites de taxa da API do Google
4. **Arquivos grandes**: Vídeos podem demorar muito tempo para processar

## 🔒 Privacidade

- Suas credenciais ficam armazenadas localmente em `token.json`
- O script não envia dados para servidores de terceiros
- Autenticação via OAuth 2.0 oficial do Google

## 📞 Suporte

Se encontrar problemas:
1. Verifique o arquivo `download.log` para detalhes
2. Certifique-se de que todas as dependências estão instaladas
3. Verifique se o FFmpeg está funcionando: `ffmpeg -version`
4. Para vídeos, tente usar a flag `--debug-html` para investigar
