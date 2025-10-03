# 🚀 Guia Rápido - GD-Downloader v2.0

## ⚡ Instalação em 5 Minutos

### Passo 1: Clone o Repositório
```bash
git clone https://github.com/seu-usuario/gd-downloader.git
cd gd-downloader
```

### Passo 2: Instale Dependências
```bash
pip install -r requirements.txt
```

### Passo 3: Configure Credenciais

1. Acesse: https://console.cloud.google.com/
2. Crie um projeto novo
3. Ative a "Google Drive API"
4. Crie credenciais OAuth 2.0 (Desktop app)
5. Baixe o JSON e renomeie para `credentials.json`
6. Coloque na pasta do projeto

### Passo 4: Primeiro Download
```bash
python main.py "https://drive.google.com/drive/folders/SEU_ID" ./downloads
```

**Pronto!** 🎉

---

## 📋 Checklist Pré-Uso

- [ ] Python 3.8+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] `credentials.json` configurado
- [ ] FFmpeg instalado (se for baixar vídeos)
- [ ] **Li e aceito o [LEGAL_NOTICE.md](LEGAL_NOTICE.md)**

---

## 🎯 Comandos Mais Usados

### Download Completo
```bash
python main.py "URL_DA_PASTA" ./MeuDownload
```

### Apenas Vídeos
```bash
python main.py "URL" ./Videos --only-videos --workers 15
```

### Retomar Download
```bash
python main.py "URL" ./Downloads --resume
```

### Apenas View-Only (⚠️ Leia o aviso legal!)
```bash
python main.py "URL" ./ViewOnly --only-view-only --workers 20
```

---

## ❓ Problemas Comuns

### "Credenciais inválidas"
```bash
rm token.json
python main.py "URL" ./downloads  # Fará novo login
```

### "FFmpeg não encontrado"
```bash
# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows: baixe de https://ffmpeg.org/
```

### "URL inválida"
Use o formato correto:
```
https://drive.google.com/drive/folders/1a2b3c4d5e6f...
```

---

## 📚 Documentação Completa

- **README.md** - Documentação principal
- **LEGAL_NOTICE.md** - ⚠️ **IMPORTANTE** - Leia primeiro!
- **requirements_and_setup.md** - Guia detalhado
- **MELHORIAS_IMPLEMENTADAS.md** - Changelog técnico

---

## ⚠️ AVISO IMPORTANTE

**Este software pode baixar arquivos view-only, o que pode violar os Termos de Serviço do Google Drive.**

✅ Use apenas para:
- Backup de seus próprios arquivos
- Conteúdo que você tem permissão
- Fins educacionais

❌ NÃO use para:
- Pirataria
- Violação de direitos autorais
- Download não autorizado

**Leia [LEGAL_NOTICE.md](LEGAL_NOTICE.md) para detalhes completos.**

---

## 🆘 Suporte

1. Verifique `download.log` para erros detalhados
2. Consulte [README.md](README.md#troubleshooting) para troubleshooting
3. Abra uma Issue no GitHub (se aplicável)

---

**Versão**: 2.0  
**Data**: Outubro 2025  
**Licença**: MIT

🎉 **Bom download!** (Responsável, é claro 😉)
