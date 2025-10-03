# Guia de Filtros Combinados

## 🎯 Flags Disponíveis

### Filtros Principais
- `--only-view-only` - Apenas arquivos view-only (sem permissão de download)
- `--only-videos` - Apenas vídeos
- `--only-docs` - Apenas documentos (tudo exceto vídeos)

**IMPORTANTE:** Agora você pode combinar estas flags!

## 📋 Combinações Possíveis

### 1. Apenas Vídeos View-Only
```bash
python main.py "URL" ./Videos --only-videos --only-view-only --workers 15
```
**Baixa:** Apenas vídeos que são view-only  
**Ignora:** Vídeos com download normal, documentos, PDFs

### 2. Apenas Documentos View-Only
```bash
python main.py "URL" ./Docs --only-docs --only-view-only --workers 10
```
**Baixa:** Apenas documentos que são view-only (PDFs, etc)  
**Ignora:** Vídeos, documentos com download normal

### 3. Todos os Vídeos (View-Only + Normais)
```bash
python main.py "URL" ./Videos --only-videos --workers 15
```
**Baixa:** Todos os vídeos (view-only E com download normal)  
**Ignora:** Documentos, PDFs

### 4. Todos os Documentos
```bash
python main.py "URL" ./Docs --only-docs --workers 10
```
**Baixa:** Todos os documentos (view-only E com download normal)  
**Ignora:** Vídeos

### 5. Apenas View-Only (Tudo)
```bash
python main.py "URL" ./ViewOnly --only-view-only --workers 20
```
**Baixa:** Todos os arquivos view-only (vídeos + docs)  
**Ignora:** Arquivos com download normal

### 6. Tudo (Sem Filtros)
```bash
python main.py "URL" ./Completo --workers 10
```
**Baixa:** Tudo (vídeos, documentos, view-only, normais)

## 🎓 Casos de Uso Práticos

### Baixar Apenas Videoaulas View-Only
```bash
python main.py "https://drive.google.com/..." ./Videoaulas \
    --only-videos --only-view-only --workers 15
```

### Baixar Material de Apoio (PDFs, Docs)
```bash
python main.py "https://drive.google.com/..." ./Material \
    --only-docs --workers 8
```

### Baixar Tudo Menos Vídeos
```bash
python main.py "https://drive.google.com/..." ./SemVideos \
    --only-docs --workers 10
```

### Baixar Tudo de um Curso
```bash
python main.py "https://drive.google.com/..." ./CursoCompleto \
    --workers 10
```

## 📊 Tabela de Combinações

| --only-videos | --only-docs | --only-view-only | Resultado |
|---------------|-------------|------------------|-----------|
| ❌ | ❌ | ❌ | Tudo |
| ✅ | ❌ | ❌ | Todos os vídeos |
| ❌ | ✅ | ❌ | Todos os docs |
| ❌ | ❌ | ✅ | View-only (vídeos+docs) |
| ✅ | ❌ | ✅ | **Vídeos view-only** |
| ❌ | ✅ | ✅ | **Docs view-only** |
| ✅ | ✅ | ❌ | ⚠️ Conflito (docs exclui vídeos) |

## 💡 Dicas

### Para Máxima Velocidade
Use mais workers para vídeos view-only:
```bash
python main.py "URL" ./Videos --only-videos --only-view-only --workers 20
```

### Para Downloads Seletivos
Separe por tipo em diferentes pastas:
```bash
# Primeiro os vídeos
python main.py "URL" ./Videos --only-videos --workers 15

# Depois os documentos
python main.py "URL" ./Docs --only-docs --workers 10
```

### Com Resume
Todas as combinações funcionam com `--resume`:
```bash
python main.py "URL" ./Videos --only-videos --only-view-only --resume
```

## ⚠️ Notas Importantes

1. **--only-videos e --only-docs juntos**: A flag `--only-docs` exclui vídeos, então usar ambas resulta em apenas documentos
2. **View-only mais lento**: Arquivos view-only são mais lentos para baixar
3. **Workers**: Use mais workers (15-20) para vídeos view-only, menos (5-10) para documentos
4. **Checkpoints**: São salvos por pasta, não por filtro

## 🔄 Fluxo Recomendado

### Para Cursos Online
```bash
# 1. Baixa vídeos view-only primeiro (mais demorado)
python main.py "URL" ./Curso/Videos --only-videos --only-view-only --workers 20

# 2. Baixa documentos normais
python main.py "URL" ./Curso/Docs --only-docs --workers 10
```

### Para Backup Completo
```bash
# Baixa tudo de uma vez
python main.py "URL" ./Backup --workers 15
```


### 1. Interface Visual Rica (Rich)
- **Painéis coloridos** para mensagens importantes
- **Tabelas formatadas** para estatísticas
- **Barras de progresso avançadas** com tempo estimado
- **Cores e ícones** para melhor visualização

### 2. Novas Flags de Filtro

#### `--only-videos`
Baixa apenas arquivos de vídeo (MP4, AVI, etc.)

```bash
python main.py "URL" ./downloads --only-videos --workers 10
```

#### `--only-docs`
Baixa apenas documentos (PDF, Google Docs, Sheets, Slides, etc.)

```bash
python main.py "URL" ./downloads --only-docs --workers 5
```

#### `--only-view-only`
Baixa apenas arquivos view-only (sem permissão de download)

```bash
python main.py "URL" ./downloads --only-view-only --workers 15
```

**Nota:** Estas flags são mutuamente exclusivas - use apenas uma por vez.

### 3. Indicador de Pausa

Quando você pressiona **Ctrl+C**, o programa exibe:

```
╭────────── Download Pausado! ──────────╮
│ Download Pausado!                      │
│ Salvando progresso para retomar...    │
╰────────────────────────────────────────╯

✓ Checkpoint salvo com sucesso!

Para retomar, execute:
python main.py <URL> <DESTINO> --resume
```

## 📊 Exemplos de Uso

### Exemplo 1: Download Completo
```bash
python main.py "https://drive.google.com/drive/folders/..." ./Aulas --workers 10
```

**Saída:**
```
╭──────── Google Drive Downloader ────────╮
│  Google Drive Downloader                 │
│  Download inteligente com pause/resume   │
╰──────────────────────────────────────────╯

✓ Autenticação concluída
✓ Pasta: Curso de Python
✓ Encontrados 50 arquivos

┌─────── Classificação dos Arquivos ───────┐
│ Tipo              │ Quantidade │ Status  │
├───────────────────┼────────────┼─────────┤
│ Downloads padrão  │     30     │    ✓    │
│ Vídeos view-only  │     15     │    ✓    │
│ PDFs view-only    │      3     │    ✓    │
│ Já completados    │      0     │    ⊙    │
│ Não suportados    │      2     │    ⊗    │
└───────────────────┴────────────┴─────────┘

Iniciando Downloads Padrão
Workers: 10 | Arquivos: 30
⠋ Baixando... ━━━━━━━━━━━━━━━━ 100% • 0:00:00
✓ Concluídos: 30/30
```

### Exemplo 2: Apenas Vídeos
```bash
python main.py "URL" ./Videos --only-videos --workers 15
```

### Exemplo 3: Retomar Download
```bash
python main.py "URL" ./Downloads --resume
```

**Saída:**
```
┌────── Checkpoint Encontrado ──────┐
│ Métrica          │ Valor          │
├──────────────────┼────────────────┤
│ Arquivos baixados│ 25             │
│ Falhas           │ 2              │
│ Data             │ 2025-10-02...  │
└──────────────────┴────────────────┘

Retomar download? (s/n): s
```

### Exemplo 4: Apenas Documentos
```bash
python main.py "URL" ./Documentos --only-docs --workers 8
```

## 🎯 Barras de Progresso

### Downloads Padrão (Verde)
```
⠋ Baixando... ━━━━━━━━━━━━━━━━ 75% • 0:02:30
```

### Vídeos View-Only (Magenta)
```
⠋ Baixando vídeos... ━━━━━━━━━━━━━━━━ 60% • 0:05:15
```

### PDFs View-Only (Azul)
```
⠋ PDFs... ━━━━━━━━━━━━━━━━ 33% 
```

## 🎨 Painéis de Status

### Sucesso Total
```
╭─────────── Sucesso ───────────╮
│ Download 100% Completo!        │
│ Todos os 50 arquivos foram     │
│ baixados com sucesso.          │
│ Localização: ./Downloads       │
╰────────────────────────────────╯
```

### Com Falhas
```
╭─────────── Atenção ───────────╮
│ Download Concluído com Falhas  │
│ Sucesso: 48                    │
│ Falhas: 2                      │
│                                │
│ Execute com --resume para      │
│ tentar novamente.              │
╰────────────────────────────────╯
```

### Pausado
```
╭────────── Download Pausado! ──────────╮
│ Download Pausado!                      │
│ Salvando progresso para retomar...    │
╰────────────────────────────────────────╯
```

## 🔧 Comandos Completos

### Download Normal
```bash
python main.py "URL_DA_PASTA" ./destino
```

### Com Workers Customizados
```bash
python main.py "URL_DA_PASTA" ./destino --workers 15
```

### Filtros
```bash
# Apenas vídeos
python main.py "URL" ./Videos --only-videos --workers 10

# Apenas documentos
python main.py "URL" ./Docs --only-docs --workers 5

# Apenas view-only
python main.py "URL" ./ViewOnly --only-view-only --workers 20
```

### Controle de Checkpoint
```bash
# Retomar
python main.py "URL" ./destino --resume

# Limpar e recomeçar
python main.py "URL" ./destino --clear-checkpoint

# Retomar apenas vídeos
python main.py "URL" ./Videos --only-videos --resume
```

## 💡 Dicas de Uso

### 1. Maximize a Velocidade
```bash
python main.py "URL" ./destino --only-videos --workers 20
```

### 2. Downloads Conservadores
```bash
python main.py "URL" ./destino --workers 3
```

### 3. Combinando Filtros com Resume
```bash
# Primeira execução: baixa apenas vídeos
python main.py "URL" ./Videos --only-videos --workers 15

# Se pausar, retome
python main.py "URL" ./Videos --only-videos --workers 15 --resume
```

### 4. Separar por Tipo
```bash
# Baixa vídeos
python main.py "URL" ./Videos --only-videos --workers 15

# Baixa documentos
python main.py "URL" ./Documentos --only-docs --workers 10
```

## 🎪 Recursos Visuais

- ✓ = Sucesso
- ⊙ = Neutro/Completo
- ⊗ = Ignorado
- ━ = Barra de progresso
- ⠋ = Spinner animado

## 📝 Notas Importantes

1. **Ctrl+C seguro**: Sempre salva o progresso antes de sair
2. **Checkpoint automático**: Salva a cada 10 arquivos (padrão) ou 5 vídeos
3. **Filtros exclusivos**: Use apenas um filtro por execução
4. **Rich colorido**: Funciona melhor em terminais modernos
5. **Tempo estimado**: Aparece nas barras de progresso

## 🐛 Troubleshooting

### Cores não aparecem?
Seu terminal pode não suportar cores. O programa ainda funciona, mas sem formatação.

### Barra de progresso "quebrada"?
Use um terminal moderno (Windows Terminal, iTerm2, etc.)

### Checkpoint não carrega?
Use `--clear-checkpoint` para recomeçar do zero

## 🎓 Exemplos Práticos

### Baixar Curso Completo
```bash
python main.py "https://drive.google.com/drive/folders/ID_DO_CURSO" ./MeuCurso --workers 10
```

### Baixar Apenas Videoaulas
```bash
python main.py "https://drive.google.com/drive/folders/ID_DO_CURSO" ./Videoaulas --only-videos --workers 15
```

### Baixar Material de Apoio
```bash
python main.py "https://drive.google.com/drive/folders/ID_DO_CURSO" ./Material --only-docs --workers 8
```

### Retomar Download Pausado
```bash
# Se você pausou com Ctrl+C
python main.py "URL_ANTERIOR" ./DESTINO_ANTERIOR --resume
```
