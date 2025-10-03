# Notas Técnicas - Correções Aplicadas

## 🔧 Principais Correções Implementadas

### 1. **Autenticação Corrigida** (`auth_drive.py`)

**Problema original:**
- Não retornava o objeto `creds` junto com o `service`
- Threads não podiam criar sessões autenticadas

**Solução:**
- Função agora retorna tupla: `(service, creds)`
- Credenciais podem ser usadas em múltiplas threads
- Adicionado refresh automático do token

```python
service, creds = get_drive_service()
```

### 2. **Download de Vídeos View-Only** (`downloader.py`)

**Problemas originais:**
1. AuthorizedSession sem headers apropriados
2. Apenas um padrão regex para encontrar HLS
3. FFmpeg sem headers de autorização
4. Sem tratamento de erros detalhado

**Soluções aplicadas:**

#### A. Headers HTTP apropriados
```python
headers = {
    'User-Agent': 'Mozilla/5.0...',
    'Accept': 'text/html,application/xhtml+xml...',
    'Accept-Language': 'pt-BR,pt;q=0.9...',
}
```

#### B. Múltiplos padrões regex
```python
patterns = [
    r'"(https://[^"]*googlevideo\.com[^"]*itag=301[^"]*)"',
    r'hlsManifestUrl["\s:]+["\']([^"\']+)["\']',
    r'"(https://[^"]*\.googlevideo\.com[^"]*\.m3u8[^"]*)"',
    # ... mais padrões
]
```

#### C. FFmpeg com autorização
```python
command.extend([
    '-headers', f'Authorization: Bearer {creds.token}\r\n',
    '-user_agent', 'Mozilla/5.0...'
])
```

#### D. Validação de credenciais
```python
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
```

#### E. Verificação do arquivo gerado
```python
if process.returncode == 0 and os.path.exists(save_path):
    file_size = os.path.getsize(save_path)
    if file_size > 0:
        return True
```

### 3. **Melhorias no Main** (`main.py`)

#### A. Interface mais amigável
- Emojis para melhor visualização
- Mensagens mais claras e informativas
- Barra de progresso para cada etapa

#### B. Relatório detalhado
```python
print(f"\n📊 Classificação dos arquivos:")
print(f"   • Downloads padrão: {len(parallel_tasks)}")
print(f"   • Vídeos view-only: {len(video_view_only_tasks)}")
```

#### C. Flag de debug
```bash
--debug-html  # Salva HTML das páginas para análise
```

#### D. Tratamento melhorado de erros
- Cada tipo de erro tem mensagem específica
- Logs detalhados em `download.log`
- Contadores de sucesso/falha

## 🎯 Limitações Conhecidas

### 1. **Vídeos View-Only**

**Limitações técnicas:**
- Alguns vídeos têm proteção DRM adicional
- URLs de manifesto podem expirar rapidamente
- Google pode alterar estrutura HTML a qualquer momento

**Quando NÃO funciona:**
- Vídeos com DRM (Widevine, PlayReady)
- Vídeos em contas corporativas com restrições
- Vídeos muito grandes (>10GB) podem ter timeouts

### 2. **PDFs View-Only**

**Limitações:**
- Requer interação manual (login no navegador)
- Qualidade limitada à resolução das imagens
- Lento para PDFs grandes
- Pode falhar se PDF tiver proteções especiais

### 3. **Rate Limits**

**Cuidados:**
- API do Google tem limite de 1000 requisições/100 segundos
- Downloads muito grandes podem ser bloqueados
- Recomendado: usar `--workers 4` ou menos

## 🚀 Otimizações Possíveis

### 1. **Cache de Manifestos**
```python
# Implementação futura
manifest_cache = {}
if file_id in manifest_cache:
    hls_url = manifest_cache[file_id]
```

### 2. **Retry com Backoff Exponencial**
Já implementado em `download_standard_file`:
```python
delay = 2
for attempt in range(max_retries):
    # ... tentativa ...
    time.sleep(delay)
    delay *= 2  # Backoff exponencial
```

### 3. **Download Resumível**
Futura implementação para vídeos grandes:
```python
ffmpeg -ss 00:10:00 -i url -c copy output.mp4  # Resume de 10min
```

## 🔒 Considerações de Segurança

### 1. **Credenciais**
- ✅ Armazenadas localmente em `token.json`
- ✅ Não são enviadas para servidores externos
- ⚠️ Proteja o arquivo `credentials.json`
- ⚠️ Não compartilhe `token.json`

### 2. **Acesso a Arquivos**
- ✅ Usa OAuth 2.0 oficial
- ✅ Escopo read-only (`drive.readonly`)
- ❌ Não pode modificar/deletar arquivos

### 3. **View-Only**
- ⚠️ Contornar restrições view-only pode violar ToS
- ⚠️ Use apenas para arquivos que você tem direito
- ⚠️ Respeite direitos autorais

## 🧪 Testes Recomendados

### 1. **Teste de Autenticação**
```bash
# Deve abrir navegador e solicitar login
python main.py "URL_TESTE" ./test
```

### 2. **Teste de Downloads Padrão**
```bash
# Pasta com arquivos normais
python main.py "URL_PASTA_NORMAL" ./test --workers 2
```

### 3. **Teste de Vídeos View-Only**
```bash
# Com debug ativado
python main.py "URL_VIDEO" ./test --debug-html
```

### 4. **Teste de GPU**
```bash
# Verificar se GPU está disponível
python main.py "URL_VIDEO" ./test --gpu nvidia
```

## 📈 Monitoramento

### Logs Importantes

**Sucesso:**
```
SUCESSO (Download Padrão): 'arquivo.pdf' salvo em './downloads/arquivo.pdf'
SUCESSO (Vídeo View-Only): 'video.mp4' salvo em './downloads/video.mp4'
```

**Falha:**
```
FALHA (Download Padrão): Não foi possível baixar 'arquivo.pdf' após 5 tentativas
FALHA (Vídeo View-Only): Erro para 'video.mp4': Não foi possível encontrar o manifesto HLS
```

**Avisos:**
```
HttpError na tentativa 2 para arquivo.pdf: 403. Tentando novamente em 4s.
```

## 🔄 Fluxo de Execução

```
1. Autenticação
   ↓
2. Extração do ID da pasta
   ↓
3. Mapeamento recursivo (BFS)
   ↓
4. Classificação dos arquivos
   ├─→ Downloads padrão (paralelo)
   ├─→ Vídeos view-only (sequencial)
   ├─→ PDFs view-only (manual)
   └─→ Não suportados (ignorar)
   ↓
5. Relatório final
```

## 🛠️ Debugging

### Problema: Vídeo não baixa

**Passo 1:** Ativar debug
```bash
python main.py URL ./test --debug-html
```

**Passo 2:** Verificar HTML gerado
```bash
# Procurar por:
# - "googlevideo.com"
# - "hlsManifestUrl"
# - "m3u8"
grep -i "m3u8" debug_page_*.html
```

**Passo 3:** Testar FFmpeg manualmente
```bash
ffmpeg -i "URL_DO_MANIFESTO" -c copy test.mp4
```

### Problema: Token expirado

**Solução:**
```bash
rm token.json
python main.py URL ./test  # Fará novo login
```

### Problema: FFmpeg não encontrado

**Verificar:**
```bash
which ffmpeg  # Linux/Mac
where ffmpeg  # Windows
ffmpeg -version
```

## 📚 Referências

- [Google Drive API](https://developers.google.com/drive/api/v3/reference)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [OAuth 2.0](https://oauth.net/2/)
- [HLS Streaming](https://developer.apple.com/streaming/)

## 🤝 Contribuições

Para melhorias futuras:
1. Suporte a mais formatos do Google Workspace
2. Download paralelo de vídeos (se possível)
3. Interface gráfica (GUI)
4. Docker container
5. Suporte a proxies/VPN
