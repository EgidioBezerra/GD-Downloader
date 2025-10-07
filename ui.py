# ui.py
"""
Interface de Usuário Unificada para GD-Downloader v2.5

Fornece métodos padronizados para exibir mensagens, painéis e indicadores de progresso
usando Rich Console, garantindo consistência visual em todo o programa.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from typing import Optional


class UIManager:
    """
    Gerenciador de Interface Unificada.

    Padronização:
    - Cores: cyan=info, green=sucesso, yellow=aviso, red=erro, magenta=especial
    - Emojis: 📄=arquivo, 🔍=processamento, ✓=sucesso, ⚠=aviso, ✗=erro
    - Indentação: 0=título, 1=principal, 2=detalhe, 3=sub-detalhe
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Inicializa o gerenciador de UI.

        Args:
            console: Console Rich existente (opcional)
        """
        self.console = console or Console()
        self._indent_levels = ["", "  ", "    ", "      "]

    def _get_indent(self, level: int) -> str:
        """Retorna string de indentação para o nível especificado."""
        return self._indent_levels[min(level, len(self._indent_levels) - 1)]

    # ============================================================================
    # MENSAGENS BÁSICAS
    # ============================================================================

    def info(self, message: str, emoji: str = "", indent: int = 1):
        """
        Exibe mensagem informativa em cyan.

        Args:
            message: Texto da mensagem
            emoji: Emoji opcional (padrão: nenhum)
            indent: Nível de indentação (0-3)
        """
        prefix = self._get_indent(indent)
        emoji_str = f"{emoji} " if emoji else ""
        self.console.print(f"{prefix}{emoji_str}[cyan]{message}[/cyan]")

    def success(self, message: str, emoji: str = "✓", indent: int = 1):
        """
        Exibe mensagem de sucesso em verde.

        Args:
            message: Texto da mensagem
            emoji: Emoji opcional (padrão: ✓)
            indent: Nível de indentação (0-3)
        """
        prefix = self._get_indent(indent)
        emoji_str = f"{emoji} " if emoji else ""
        self.console.print(f"{prefix}{emoji_str}[green]{message}[/green]")

    def warning(self, message: str, emoji: str = "⚠", indent: int = 1):
        """
        Exibe mensagem de aviso em amarelo.

        Args:
            message: Texto da mensagem
            emoji: Emoji opcional (padrão: ⚠)
            indent: Nível de indentação (0-3)
        """
        prefix = self._get_indent(indent)
        emoji_str = f"{emoji} " if emoji else ""
        self.console.print(f"{prefix}{emoji_str}[yellow]{message}[/yellow]")

    def error(self, message: str, emoji: str = "✗", indent: int = 1):
        """
        Exibe mensagem de erro em vermelho.

        Args:
            message: Texto da mensagem
            emoji: Emoji opcional (padrão: ✗)
            indent: Nível de indentação (0-3)
        """
        prefix = self._get_indent(indent)
        emoji_str = f"{emoji} " if emoji else ""
        self.console.print(f"{prefix}{emoji_str}[red]{message}[/red]")

    def special(self, message: str, emoji: str = "", indent: int = 1):
        """
        Exibe mensagem especial em magenta (para OCR, GPU, etc).

        Args:
            message: Texto da mensagem
            emoji: Emoji opcional
            indent: Nível de indentação (0-3)
        """
        prefix = self._get_indent(indent)
        emoji_str = f"{emoji} " if emoji else ""
        self.console.print(f"{prefix}{emoji_str}[magenta]{message}[/magenta]")

    def dim(self, message: str, indent: int = 1):
        """
        Exibe mensagem em texto cinza/esmaecido.

        Args:
            message: Texto da mensagem
            indent: Nível de indentação (0-3)
        """
        prefix = self._get_indent(indent)
        self.console.print(f"{prefix}[dim]{message}[/dim]")

    def plain(self, message: str, indent: int = 1):
        """
        Exibe mensagem sem formatação de cor.

        Args:
            message: Texto da mensagem
            indent: Nível de indentação (0-3)
        """
        prefix = self._get_indent(indent)
        self.console.print(f"{prefix}{message}")

    # ============================================================================
    # MENSAGENS DE PROCESSAMENTO
    # ============================================================================

    def processing(self, message: str, emoji: str = "🔍", indent: int = 1):
        """Exibe mensagem de processamento/análise."""
        self.info(message, emoji=emoji, indent=indent)

    def file_action(self, message: str, emoji: str = "📄", indent: int = 1):
        """Exibe mensagem relacionada a arquivo."""
        self.info(message, emoji=emoji, indent=indent)

    def progress_update(self, current: int, total: int, label: str = "páginas", emoji: str = "📄", indent: int = 2):
        """
        Exibe atualização de progresso numérico.

        Args:
            current: Número atual
            total: Total
            label: Rótulo (ex: "páginas", "arquivos")
            emoji: Emoji opcional
            indent: Nível de indentação
        """
        self.info(f"{current}/{total} {label}", emoji=emoji, indent=indent)

    # ============================================================================
    # SEÇÕES E SEPARADORES
    # ============================================================================

    def section(self, title: str, style: str = "bold cyan"):
        """
        Exibe título de seção.

        Args:
            title: Título da seção
            style: Estilo Rich (padrão: "bold cyan")
        """
        self.console.print(f"\n[{style}]{title}[/{style}]")

    def separator(self):
        """Exibe linha separadora."""
        self.console.print()

    # ============================================================================
    # PAINÉIS E TABELAS
    # ============================================================================

    def panel(
        self,
        content: str,
        title: str = "",
        border_style: str = "cyan",
        title_align: str = "center"
    ):
        """
        Exibe painel Rich.

        Args:
            content: Conteúdo do painel (suporta markup Rich)
            title: Título do painel
            border_style: Cor da borda
            title_align: Alinhamento do título
        """
        panel = Panel.fit(
            content,
            title=title if title else None,
            border_style=border_style,
            title_align=title_align
        )
        self.console.print(panel)

    def table(
        self,
        title: str,
        columns: list,  # Lista de tuplas (nome, estilo, justify)
        rows: list,
        box_style=box.ROUNDED
    ):
        """
        Exibe tabela Rich.

        Args:
            title: Título da tabela
            columns: Lista de tuplas (nome, estilo, justify). Ex: [("Nome", "cyan", "left")]
            rows: Lista de listas com dados das linhas
            box_style: Estilo da caixa (padrão: ROUNDED)
        """
        table = Table(title=title, box=box_style)

        for col_name, col_style, col_justify in columns:
            table.add_column(col_name, style=col_style, justify=col_justify)

        for row in rows:
            table.add_row(*[str(cell) for cell in row])

        self.console.print(table)

    # ============================================================================
    # HELPERS DE CONTEXTO
    # ============================================================================

    def status(self, message: str):
        """
        Retorna context manager para status spinner.

        Uso:
            with ui.status("Carregando..."):
                # código aqui
        """
        return self.console.status(f"[bold green]{message}")

    # ============================================================================
    # MENSAGENS ESPECÍFICAS DO DOMÍNIO
    # ============================================================================

    def ocr_active(self, lang: str, indent: int = 1):
        """Exibe mensagem de OCR ativo."""
        self.special(f"OCR ativo ({lang})", emoji="🔍", indent=indent)

    def document_pages(self, pages: int, indent: int = 2):
        """Exibe número de páginas do documento."""
        self.info(f"Documento tem {pages} páginas", emoji="📊", indent=indent)

    def file_complete(self, size_mb: float, pages: int, has_ocr: bool = False, indent: int = 2):
        """Exibe mensagem de arquivo completo."""
        ocr_status = "com OCR" if has_ocr else "sem OCR"
        self.success(
            f"Completo: {size_mb:.2f} MB ({pages} páginas, {ocr_status})",
            indent=indent
        )

    def scroll_warning(self, indent: int = 2):
        """Exibe aviso sobre não usar o mouse durante scroll."""
        self.warning("Não use mouse durante o scroll (~40s)", emoji="⚠", indent=indent)

    def waiting(self, seconds: int = 2, indent: int = 2):
        """Exibe mensagem de aguardo."""
        self.dim(f"Aguardando ({seconds}s)...", indent=indent)

    def file_interrupted(self, file_name: str, indent: int = 2):
        """Exibe mensagem de interrupção."""
        self.warning(f"Interrompido: {file_name}", emoji="⚠️", indent=indent)

    def file_cancelled(self, file_name: str, indent: int = 2):
        """Exibe mensagem de cancelamento."""
        self.warning(f"Cancelado: {file_name}", emoji="⚠️", indent=indent)


# ============================================================================
# INSTÂNCIA GLOBAL (para uso fácil em outros módulos)
# ============================================================================

# Cria instância global do UIManager
ui = UIManager()
