# Sistema de Checkpoint - Guia de Uso

## 🎯 O que é o Sistema de Checkpoint?

O sistema de checkpoint permite **pausar e retomar** downloads do Google Drive de forma inteligente. Se o programa for fechado (intencionalmente ou por erro), você pode continuar de onde parou.

## 📋 Recursos

### ✅ Implementados

1. **Auto-save Inteligente**
   - Salva progresso a cada 10 arquivos (downloads padrão)
   - Salva progresso a cada 5 vídeos (view-only)
   - Salva ao pressionar Ctrl+C

2. **Resume Automático**
   - Detecta checkpoint anterior
   - Pula arquivos já baixados
   - Retenta arquivos que falharam

3. **Controle Manual**
   - `--resume`: Retoma download anterior
   - `--clear-checkpoint`: Remove checkpoint e recomeça

## 🚀 Como Usar

### Iniciar Download Normal

```bash
python main.py "URL_DA_PASTA" ./downloads --workers 10
```

### Pausar Download

Pressione **Ctrl+C** durante o download:

```
⚠️  Interrupção detectada! Salvando progresso...
Os downloads podem ser retomados executando o comando novamente.
💾 Checkpoint salvo! Execute novamente com --resume para continuar.
```

### Retomar Download

Execute o mesmo comando com `--resume`:

```bash
python main.py "URL_DA_PASTA" ./downloads --workers 10 --resume
```

Você verá:

```
📋 Checkpoint encontrado!
   • Arquivos já baixados: 45
   • Falhas anteriores: 2
   • Data: 2025-10-02T01:30:45

❓ Deseja retomar o download? (s/n):
```

Digite `s` para continuar de onde parou.

### Recomeçar do Zero

Se quiser ignorar o checkpoint e recomeçar:

```bash
python main.py "URL_DA_PASTA" ./downloads --clear-checkpoint
```

## 📂 Estrutura dos Checkpoints

Os checkpoints são salvos em `.checkpoints/`:

```
.checkpoints/
├── checkpoint_a1b2c3d4e5f6.json
├── checkpoint_f6e5d4c3b2a1.json
└── ...
```

### Exemplo de Checkpoint JSON

```json
{
  "folder_id": "1aovMhkPV0LN8GgGzQcW014y_uD9c95rs",
  "destination_path": "./downloads/Minha Pasta",
  "timestamp": "2025-10-02T01:30:45.123456",
  "completed_files": [
    "1abc_video1.mp4",
    "2def_video2.mp4",
    "3ghi_documento.pdf"
  ],
  "failed_files": [
    "4jkl_video_erro.mp4"
  ],
  "total_completed": 45,
  "total_failed": 2
}
```

## 🔄 Fluxo de Trabalho Típico

### Cenário 1: Download Interrompido por Erro

```bash
# Inicia download
python main.py "URL" ./downloads --workers 10

# ... download em progresso ...
# [Erro de rede / crash / queda de energia]

# Retoma automaticamente
python main.py "URL" ./downloads --workers 10 --resume
```

### Cenário 2: Pausar Intencionalmente

```bash
# Inicia download
python main.py "URL" ./downloads --workers 10

# Pressiona Ctrl+C quando quiser pausar
# [Ctrl+C]

# Continua mais tarde (pode ser horas/dias depois)
python main.py "URL" ./downloads --workers 10 --resume
```

### Cenário 3: Tentar Novamente Apenas Falhas

```bash
# Após um download com falhas
python main.py "URL" ./downloads --workers 10 --resume

# O sistema automaticamente:
# 1. Pula arquivos já baixados (sucesso)
# 2. Tenta novamente arquivos que falharam
```

## 📊 Estatísticas de Progresso

Durante a execução, você verá:

```
📊 Classificação dos arquivos:
   • Downloads padrão: 50
   • Vídeos view-only: 30
   • PDFs view-only: 5
   • Já completados: 45  ← Arquivos do checkpoint
   • Não suportados: 2
```

Ao final:

```
📊 Estatísticas:
   • Sucesso: 83
   • Falhas: 2
```

## 🛡️ Segurança e Confiabilidade

### Quando o Checkpoint é Salvo?

1. **Automaticamente**:
   - A cada 10 arquivos baixados (padrão)
   - A cada 5 vídeos baixados (view-only)
   - Ao final de cada tipo de download

2. **Manualmente**:
   - Ao pressionar Ctrl+C
   - Em caso de exceção crítica

### Quando o Checkpoint é Removido?

- Automaticamente após **100% dos arquivos baixados com sucesso**
- Manualmente com `--clear-checkpoint`

### Integridade dos Dados

- Downloads parciais são retomados usando **HTTP Range requests**
- Cada arquivo tem validação de tamanho mínimo (1KB)
- Arquivos corrompidos são redetectados e rebaixados

## 🔧 Troubleshooting

### Problema: "Checkpoint não carrega"

**Causa**: Arquivo JSON corrompido

**Solução**:
```bash
python main.py "URL" ./downloads --clear-checkpoint
```

### Problema: "Arquivos estão sendo rebaixados"

**Causa**: Checkpoints de diferentes execuções

**Solução**:
```bash
# Remove todos os checkpoints
rm -rf .checkpoints/
# Ou no Windows:
rmdir /s .checkpoints
```

### Problema: "Resume não funciona após mover arquivos"

**Causa**: O checkpoint salva caminhos absolutos

**Solução**: Use sempre o mesmo `destination` path ou limpe o checkpoint

## 💡 Dicas de Uso

### 1. Downloads Longos
Para downloads que levam horas:
```bash
python main.py "URL" ./downloads --workers 15 --resume
```

### 2. Conexão Instável
Checkpoints salvam progresso frequentemente:
```bash
# Se conexão cair, apenas execute novamente
python main.py "URL" ./downloads --resume
```

### 3. Múltiplas Pastas
Cada pasta tem seu próprio checkpoint:
```bash
# Pasta 1
python main.py "URL1" ./downloads --resume

# Pasta 2 (checkpoint independente)
python main.py "URL2" ./downloads --resume
```

### 4. Teste de Velocidade
Comece com poucos workers e aumente:
```bash
# Teste inicial
python main.py "URL" ./downloads --workers 5

# Se estável, pressione Ctrl+C e aumente
python main.py "URL" ./downloads --workers 15 --resume
```

## 📝 Arquivos Relacionados

- `checkpoint.py` - Sistema de gerenciamento de checkpoints
- `main.py` - Integração com download
- `.checkpoints/` - Diretório de checkpoints (auto-criado)
- `download.log` - Log detalhado (modo append)

## ⚠️ Limitações

1. **PDFs view-only**: Requerem interação manual, checkpoint menos efetivo
2. **Arquivos renomeados**: Se arquivo for renomeado no Drive, será rebaixado
3. **Múltiplas instâncias**: Não execute múltiplas instâncias na mesma pasta
4. **Checkpoints antigos**: Limpe manualmente checkpoints muito antigos

## 🎓 Exemplos Avançados

### Download com Retry Automático

```bash
# Script para retry automático em caso de falha
while true; do
    python main.py "URL" ./downloads --workers 10 --resume
    if [ $? -eq 0 ]; then break; fi
    echo "Tentando novamente em 60s..."
    sleep 60
done
```

### Monitoramento de Progresso

```bash
# Monitora checkpoint enquanto download roda
watch -n 5 'cat .checkpoints/*.json | grep total_completed'
```

### Limpeza Automática

```bash
# Remove checkpoints de downloads completos
find .checkpoints -name "*.json" -mtime +7 -delete
```

## 📞 Suporte

Se encontrar problemas:

1. Verifique `download.log` para detalhes
2. Use `--clear-checkpoint` se checkpoint estiver corrompido
3. Teste com menos workers se houver instabilidade
4. Reporte bugs com o arquivo de log completo
