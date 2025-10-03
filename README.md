# 📦 GD-Downloader

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)]()

> Download inteligente de arquivos do Google Drive com sistema de pause/resume

---

## ⚠️ AVISO LEGAL IMPORTANTE

**Este software pode baixar arquivos view-only do Google Drive, o que pode violar os Termos de Serviço do Google.**

🔴 **Use por sua conta e risco**  
🔴 **Apenas para fins educacionais e backup pessoal autorizado**  
🔴 **Leia [LEGAL_NOTICE.md](LEGAL_NOTICE.md) antes de usar**

Os desenvolvedores **NÃO se responsabilizam** por uso indevido, violação de ToS, ou consequências legais.

---

## ✨ Recursos

### ✅ Funcionalidades Principais

- **Download Paralelo**: Até 20 downloads simultâneos
- **Pause/Resume**: Sistema de checkpoint para retomar downloads interrompidos
- **Exportação Inteligente**: Converte Google Docs/Sheets/Slides para PDF automaticamente
- **Filtros Avançados**: Baixe apenas vídeos, documentos, ou tipos específicos
- **Interface Rica**: Barras de progresso, tabelas e painéis coloridos
- **Thread-Safe**: Operações seguras em ambientes multi-thread

### ⚠️ Funcionalidades Experimentais

- **Vídeos View-Only**: Download usando técnica gdrive_videoloader (rápido e eficiente)
- **PDFs View-Only**: Captura automática de páginas

---

## 📋 Pré-requisitos

### Software Necessário

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **FFmpeg** (para vídeos view-only) ([Instruções de instalação](requirements_and_setup.md#-instala%C3%A7%C3%A3o))
- **Google Cloud Credentials** ([Como configurar](requirements_and_setup.md#-configurar-credenciais-do-google-drive))

### Sistemas Operacionais Suportados

- ✅ Windows 10/11
- ✅ Linux (Ubuntu, Debian, Fedora, etc.)
- ✅ macOS 10.15+

---

## 🚀 Instalação Rápida

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/gd-downloader.git
cd gd-downloader
```

### 2. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 3. Configure Credenciais

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto e ative a Google Drive API
3. Crie credenciais OAuth 2.0 (tipo: Desktop app)
4. Baixe o arquivo JSON e renomeie para `credentials.json`
5. Coloque `credentials.json` na pasta do projeto

📖 **Instruções detalhadas**: [requirements_and_setup.md](requirements_and_setup.md#-configurar-credenciais-do-google-drive)

### 4. Instale FFmpeg (Opcional - para vídeos)

**Windows:**
```bash
# Baixe de https://ffmpeg.org/download.html
# Adicione ao PATH do sistema
```

**Linux:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Verificar instalação:**
```bash
ffmpeg -version
```

---

## 📖 Uso Básico

### Comando Simples

```bash
python main.py "URL_DA_PASTA" ./downloads
```

### Primeiro Uso

1. Execute o comando acima
2. Uma janela do navegador abrirá para autenticação
3. Faça login com sua conta Google
4. Autorize o aplicativo
5. O download começará automaticamente

---

## 🎯 Exemplos de Uso

### 1. Download Padrão

```bash
python main.py "https://drive.google.com/drive/folders/1a2b3c4d5e6f" ./MinhaPasta
```

**Baixa**: Todos os arquivos com permissão de download  
**Workers**: 5 (padrão)

### 2. Download Rápido (Mais Workers)

```bash
python main.py "URL_DA_PASTA" ./downloads --workers 15
```

**Ideal para**: Muitos arquivos pequenos  
**Workers**: 15 simultâneos

### 3. Apenas Vídeos

```bash
python main.py "URL_DA_PASTA" ./Videos --only-videos --workers 10
```

**Baixa**: Apenas arquivos de vídeo (MP4, AVI, etc.)  
**Ignora**: Documentos, PDFs, imagens

### 4. Apenas Documentos

```bash
python main.py "URL_DA_PASTA" ./Documentos --only-docs --workers 8
```

**Baixa**: PDFs, Google Docs, Sheets, Slides  
**Ignora**: Vídeos

### 5. Apenas Arquivos View-Only

```bash
python main.py "URL_DA_PASTA" ./ViewOnly --only-view-only --workers 20
```

**Baixa**: Apenas arquivos sem permissão de download  
⚠️ **Atenção**: Pode violar ToS do Google Drive

### 6. Combinar Filtros: Apenas Vídeos View-Only

```bash
python main.py "URL_DA_PASTA" ./VideoAulas --only-videos --only-view-only --workers 15
```

**Baixa**: Apenas vídeos que são view-only  
**Ignora**: Vídeos com download normal, documentos

### 7. Download com Aceleração GPU

```bash
python main.py "URL_DA_PASTA" ./downloads --gpu nvidia --workers 10
```

**Opções de GPU**:
- `--gpu nvidia` (NVENC)
- `--gpu intel` (Quick Sync)
- `--gpu amd` (VCE)

### 8. Retomar Download Pausado

```bash
# Pause com Ctrl+C durante o download
# Depois execute:
python main.py "MESMA_URL" ./MESMO_DESTINO --resume
```

**Pula**: Arquivos já baixados  
**Retenta**: Arquivos que falharam

### 9. Recomeçar do Zero

```bash
python main.py "URL_DA_PASTA" ./downloads --clear-checkpoint
```

**Remove**: Checkpoint anterior  
**Baixa**: Tudo novamente

---

## 🎨 Interface Visual

### Exemplo de Saída

```
╭──────────── Google Drive Downloader ────────────╮
│  📦 Google Drive Downloader                     │
│  Download inteligente com pause/resume          │
│  Versão 2.0 - Melhorada e Segura               │
╰─────────────────────────────────────────────────╯

⚠️  AVISO LEGAL IMPORTANTE
...

🔍 Validando entrada...
✓ Validação concluída

🔐 Autenticando...
✓ Autenticado com sucesso

📁 Verificando pasta...
✓ Pasta: Curso Completo de Python

🔍 Mapeando arquivos...
✓ Mapeamento concluído: 150 arquivos encontrados

┌─────── Classificação dos Arquivos ───────┐
│ Tipo              │ Quantidade │ Status  │
├───────────────────┼────────────┼─────────┤
│ Downloads padrão  │     80     │    ✓    │
│ Vídeos view-only  │     50     │    ✓    │
│ PDFs view-only    │     10     │    ✓    │
│ Já completados    │      0     │    ⊙    │
│ Não suportados    │     10     │    ⊗    │
└───────────────────┴────────────┴─────────┘

🔽 Iniciando Downloads Padrão
Workers: 10 | Arquivos: 80
⠋ Baixando... ████████████████ 100% • 0:00:00
✓ Concluídos: 80/80

🎬 Iniciando Vídeos View-Only
Workers: 10 | Vídeos: 50
⠋ Baixando vídeos... ████████████ 75% • 0:05:30
```

---

## 📊 Flags e Parâmetros

### Parâmetros Obrigatórios

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `folder_url` | URL da pasta do Google Drive | `"https://drive.google.com/..."` |
| `destination` | Caminho local de destino | `./downloads` |

### Parâmetros Opcionais

| Flag | Tipo | Padrão | Descrição |
|------|------|--------|-----------|
| `--workers` | int | 5 | Downloads simultâneos (1-20) |
| `--gpu` | string | None | Aceleração GPU: nvidia/intel/amd |
| `--only-view-only` | bool | False | Apenas arquivos view-only |
| `--only-videos` | bool | False | Apenas vídeos |
| `--only-docs` | bool | False | Apenas documentos |
| `--resume` | bool | False | Retoma download anterior |
| `--clear-checkpoint` | bool | False | Remove checkpoint |
| `--debug-html` | bool | False | Salva HTML para debug |
| `--no-legal-warning` | bool | False | Suprime aviso legal |

### Combinações de Filtros

| --only-videos | --only-docs | --only-view-only | Resultado |
|---------------|-------------|------------------|-----------|
| ❌ | ❌ | ❌ | **Tudo** |
| ✅ | ❌ | ❌ | Todos os vídeos |
| ❌ | ✅ | ❌ | Todos os documentos |
| ❌ | ❌ | ✅ | View-only (vídeos+docs) |
| ✅ | ❌ | ✅ | **Vídeos view-only** |
| ❌ | ✅ | ✅ | **Documentos view-only** |

---

## 🔧 Sistema de Checkpoint

### Como Funciona

1. **Auto-save**: A cada 10 arquivos (padrão) ou 5 vídeos
2. **Ctrl+C Seguro**: Salva progresso antes de sair
3. **Resume Inteligente**: Pula arquivos já baixados
4. **Retry Automático**: Retenta arquivos que falharam

### Arquivos de Checkpoint

```
.checkpoints/
└── checkpoint_a1b2c3d4e5f6.json
```

### Exemplo de Uso

```bash
# 1. Inicia download
python main.py "URL" ./downloads --workers 10

# 2. Pressiona Ctrl+C para pausar
# Download pausado! Checkpoint salvo.

# 3. Retoma mais tarde (pode ser dias depois)
python main.py "URL" ./downloads --resume

# Checkpoint encontrado!
# Arquivos já baixados: 45
# Deseja retomar? (s/n): s
```

---

## 📁 Estrutura de Arquivos

```
gd-downloader/
├── auth_drive.py          # Autenticação Google Drive
├── checkpoint.py          # Sistema de checkpoints
├── downloader.py          # Lógica de download
├── errors.py              # Exceções personalizadas
├── validators.py          # Validação de entrada
├── main.py                # Programa principal
├── requirements.txt       # Dependências Python
├── credentials.json       # Suas credenciais (não commitar!)
├── token.json            # Token OAuth (gerado automaticamente)
├── download.log          # Log detalhado
├── .checkpoints/         # Checkpoints (auto-criado)
├── README.md             # Este arquivo
├── LEGAL_NOTICE.md       # Aviso legal importante
└── requirements_and_setup.md  # Guia de instalação
```

---

## 🎓 Casos de Uso Práticos

### Backup de Curso Online

```bash
# 1. Baixa vídeos view-only (aulas)
python main.py "URL_CURSO" ./Curso/Videos \
  --only-videos --only-view-only --workers 15

# 2. Baixa material de apoio
python main.py "URL_CURSO" ./Curso/Material \
  --only-docs --workers 8
```

### Download Seletivo

```bash
# Apenas PDFs
python main.py "URL" ./PDFs \
  --only-docs --workers 5

# Apenas vídeos com download normal
python main.py "URL" ./Videos \
  --only-videos --workers 10
```

### Download com Retry Automático

```bash
# Script bash para retry automático
while true; do
    python main.py "URL" ./downloads --workers 10 --resume
    if [ $? -eq 0 ]; then break; fi
    echo "Tentando novamente em 60s..."
    sleep 60
done
```

---

## 🛠️ Troubleshooting

### Erro: "Credenciais inválidas"

**Solução:**
```bash
rm token.json
python main.py "URL" ./downloads
# Fará novo login
```

### Erro: "FFmpeg não encontrado"

**Solução:**
```bash
# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows: Baixe e adicione ao PATH
```

### Downloads lentos

**Soluções:**
```bash
# Aumente workers
python main.py "URL" ./downloads --workers 15

# Use aceleração GPU (para vídeos)
python main.py "URL" ./downloads --gpu nvidia --workers 15
```

### Checkpoint corrompido

**Solução:**
```bash
python main.py "URL" ./downloads --clear-checkpoint
```

### Erro 403 (Forbidden)

**Causa**: Arquivo não tem permissão de download

**Não há solução técnica** - É uma restrição do proprietário

### Vídeo não baixa ou fica corrompido

**Soluções:**
1. Tente com aceleração GPU: `--gpu nvidia`
2. Verifique se FFmpeg está atualizado
3. Use `--debug-html` para investigar
4. Alguns vídeos têm proteção DRM (não há solução)

---

## 📈 Performance

### Benchmarks (aproximados)

| Tipo | Workers | Velocidade | Observação |
|------|---------|------------|------------|
| Arquivos padrão | 5 | ~50 MB/s | Depende da conexão |
| Arquivos padrão | 15 | ~100 MB/s | Máximo prático |
| Vídeos view-only | 10 | ~20 MB/s | Limitado pelo servidor |
| PDFs view-only | 1 | ~2 MB/min | Captura de tela |

### Recomendações

- **Arquivos pequenos** (<10MB): Use mais workers (15-20)
- **Arquivos grandes** (>100MB): Use menos workers (5-10)
- **Vídeos view-only**: Use aceleração GPU
- **Conexão lenta**: Reduza workers para 3-5

---

## 🔒 Segurança e Privacidade

### Dados Locais

✅ **Armazenados localmente**:
- `credentials.json` - Suas credenciais
- `token.json` - Token de autenticação
- `.checkpoints/` - Progresso de downloads

❌ **NUNCA compartilhe estes arquivos!**

### O que NÃO fazemos

- ✅ Não enviamos dados para servidores externos
- ✅ Não coletamos informações pessoais
- ✅ Não registramos histórico de downloads
- ✅ Autenticação via OAuth 2.0 oficial do Google

### Escopo de Permissões

O aplicativo usa escopo **readonly**:
```python
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
```

**Significa**: Apenas leitura, não pode modificar ou deletar arquivos

---

## 🤝 Contribuindo

### Como Contribuir

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-feature`
3. Commit suas mudanças: `git commit -m 'Adiciona nova feature'`
4. Push para a branch: `git push origin feature/nova-feature`
5. Abra um Pull Request

### Diretrizes

- ✅ Adicione testes para novas funcionalidades
- ✅ Mantenha compatibilidade com Python 3.8+
- ✅ Siga PEP 8 (style guide)
- ✅ Atualize documentação
- ✅ Adicione type hints

---

## 📝 Changelog

### Versão 2.0 (2025-10-02)

#### ✨ Novos Recursos
- Sistema de validação de entrada completo
- Exceções personalizadas padronizadas
- Thread-safe checkpoint manager
- Aviso legal integrado
- Sanitização de logs (tokens não vazam)

#### 🔧 Melhorias
- Interface visual rica (Rich)
- Combinação de filtros (`--only-videos` + `--only-view-only`)
- Validação robusta de URLs
- Melhor tratamento de erros

#### 🐛 Correções
- Race condition em checkpoints corrigida
- Logs não expõem tokens de autenticação
- Validação de credenciais aprimorada
- Melhor detecção de FFmpeg

### Versão 1.0 (Original)
- Download básico de arquivos
- Sistema de checkpoint simples
- Suporte a vídeos view-only

---

## 📄 Licença

Este projeto está licenciado sob a **MIT License**.

```
MIT License

Copyright (c) 2025 GD-Downloader Contributors

É concedida permissão, gratuitamente, a qualquer pessoa que obtenha
uma cópia deste software, para usar, copiar, modificar, mesclar,
publicar, distribuir, sublicenciar e/ou vender cópias do Software.

SEM GARANTIAS DE QUALQUER TIPO, expressas ou implícitas.
```

Veja [LICENSE](LICENSE) para o texto completo.

---

## ⚖️ Disclaimer

**USO POR SUA CONTA E RISCO**

- Este software é fornecido "como está"
- Sem garantias de qualquer tipo
- Os desenvolvedores não se responsabilizam por danos
- Leia [LEGAL_NOTICE.md](LEGAL_NOTICE.md) antes de usar

---

## 🌟 Suporte

### Documentação

- 📖 [Guia de Instalação](requirements_and_setup.md)
- 📖 [Sistema de Checkpoint](checkpoint_usage_guide.md)
- 📖 [Interface Visual](interface_guide.md)
- 📖 [Notas Técnicas](technical_notes.md)

### Problemas?

1. Verifique `download.log` para detalhes
2. Consulte a seção [Troubleshooting](#%EF%B8%8F-troubleshooting)
3. Leia as [Issues no GitHub](https://github.com/seu-usuario/gd-downloader/issues)
4. Abra uma nova Issue (se necessário)

### Comunidade

- 💬 [Discussions](https://github.com/seu-usuario/gd-downloader/discussions)
- 🐛 [Report Bugs](https://github.com/seu-usuario/gd-downloader/issues)
- ✨ [Request Features](https://github.com/seu-usuario/gd-downloader/issues)

---

## 🙏 Agradecimentos

- Google Drive API
- FFmpeg Project
- Rich (biblioteca de terminal)
- Comunidade Python
- Todos os contribuidores

---

## 📞 Contato

**Importante**: Para relatar uso indevido ou violação de direitos, **NÃO** entre em contato com os desenvolvedores. Entre em contato com:

- Google Drive: https://support.google.com/drive/answer/2463296
- Autoridades competentes em sua jurisdição

---

<div align="center">

**Feito com ❤️ para a comunidade**

[⬆ Voltar ao topo](#-gd-downloader)

</div>