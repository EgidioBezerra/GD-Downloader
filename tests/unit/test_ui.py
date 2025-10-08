"""
Unit tests for ui module.

Tests UIManager class, message formatting, and UI consistency.
"""

from unittest.mock import Mock, patch

import pytest

from ui import UIManager, ui


class TestUIManager:
    """Test UIManager class."""

    @pytest.fixture
    def mock_console(self):
        """Create a mock console for testing."""
        console = Mock()
        console.print = Mock()
        return console

    @pytest.fixture
    def ui_manager(self, mock_console):
        """Create UIManager instance with mock console."""
        return UIManager(console=mock_console)

    @pytest.fixture
    def ui_manager_default(self):
        """Create UIManager instance with default console."""
        return UIManager()


class TestUIManagerInit:
    """Test UIManager initialization."""

    @pytest.mark.critical
    def test_init_with_custom_console(self, mock_console):
        """Test initialization with custom console."""
        manager = UIManager(console=mock_console)
        
        assert manager.console is mock_console
        assert hasattr(manager, '_indent_levels')
        assert len(manager._indent_levels) == 4

    @pytest.mark.critical
    def test_init_with_default_console(self):
        """Test initialization with default console."""
        with patch('ui.Console') as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console
            
            manager = UIManager()
            
            mock_console_class.assert_called_once()
            assert manager.console is mock_console

    @pytest.mark.high
    def test_indent_levels_initialization(self, mock_console):
        """Test that indent levels are properly initialized."""
        manager = UIManager(console=mock_console)
        
        expected_levels = ["", "  ", "    ", "      "]
        assert manager._indent_levels == expected_levels

    @pytest.mark.medium
    def test_console_creation_with_no_args(self):
        """Test console creation when no arguments provided."""
        manager = UIManager()
        
        assert manager.console is not None
        assert hasattr(manager.console, 'print')


class TestGetIndent:
    """Test _get_indent method."""

    @pytest.mark.critical
    def test_get_indent_level_0(self, ui_manager):
        """Test getting indent for level 0."""
        result = ui_manager._get_indent(0)
        assert result == ""

    @pytest.mark.critical
    def test_get_indent_level_1(self, ui_manager):
        """Test getting indent for level 1."""
        result = ui_manager._get_indent(1)
        assert result == "  "

    @pytest.mark.critical
    def test_get_indent_level_2(self, ui_manager):
        """Test getting indent for level 2."""
        result = ui_manager._get_indent(2)
        assert result == "    "

    @pytest.mark.critical
    def test_get_indent_level_3(self, ui_manager):
        """Test getting indent for level 3."""
        result = ui_manager._get_indent(3)
        assert result == "      "

    @pytest.mark.high
    def test_get_indent_above_max(self, ui_manager):
        """Test getting indent for level above maximum."""
        result = ui_manager._get_indent(10)
        assert result == "      "  # Should cap at max level

    @pytest.mark.high
    def test_get_indent_negative_level(self, ui_manager):
        """Test getting indent for negative level."""
        result = ui_manager._get_indent(-1)
        assert result == ""  # Should handle gracefully

    @pytest.mark.medium
    def test_get_indent_boundary_levels(self, ui_manager):
        """Test getting indent at boundary levels."""
        assert ui_manager._get_indent(-1) == ""
        assert ui_manager._get_indent(0) == ""
        assert ui_manager._get_indent(3) == "      "
        assert ui_manager._get_indent(4) == "      "  # Capped
        assert ui_manager._get_indent(100) == "      "  # Capped


class TestBasicMessageMethods:
    """Test basic message methods."""

    @pytest.mark.critical
    def test_info_method(self, ui_manager, mock_console):
        """Test info message method."""
        ui_manager.info("Test message", emoji="🔍", indent=2)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "🔍 Test message" in call_args
        assert "[cyan]Test message[/cyan]" in call_args
        assert "    " in call_args  # Indent level 2

    @pytest.mark.critical
    def test_success_method(self, ui_manager, mock_console):
        """Test success message method."""
        ui_manager.success("Success message", emoji="✅", indent=1)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "✅ Success message" in call_args
        assert "[green]Success message[/green]" in call_args
        assert "  " in call_args  # Indent level 1

    @pytest.mark.critical
    def test_warning_method(self, ui_manager, mock_console):
        """Test warning message method."""
        ui_manager.warning("Warning message", emoji="⚠️", indent=3)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "⚠️ Warning message" in call_args
        assert "[yellow]Warning message[/yellow]" in call_args
        assert "      " in call_args  # Indent level 3

    @pytest.mark.critical
    def test_error_method(self, ui_manager, mock_console):
        """Test error message method."""
        ui_manager.error("Error message", emoji="❌", indent=2)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "❌ Error message" in call_args
        assert "[red]Error message[/red]" in call_args
        assert "    " in call_args  # Indent level 2

    @pytest.mark.high
    def test_special_method(self, ui_manager, mock_console):
        """Test special message method."""
        ui_manager.special("Special message", emoji="🔥", indent=1)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "🔥 Special message" in call_args
        assert "[magenta]Special message[/magenta]" in call_args

    @pytest.mark.high
    def test_dim_method(self, ui_manager, mock_console):
        """Test dim message method."""
        ui_manager.dim("Dim message", indent=2)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "    Dim message" in call_args
        assert "[dim]Dim message[/dim]" in call_args

    @pytest.mark.high
    def test_plain_method(self, ui_manager, mock_console):
        """Test plain message method."""
        ui_manager.plain("Plain message", indent=1)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "  Plain message" in call_args
        # Should not have any markup

    @pytest.mark.medium
    def test_info_no_emoji(self, ui_manager, mock_console):
        """Test info method without emoji."""
        ui_manager.info("Message without emoji")
        
        call_args = mock_console.print.call_args[0][0]
        assert "[cyan]Message without emoji[/cyan]" in call_args
        assert not call_args.startswith("🔍")

    @pytest.mark.medium
    def test_success_default_emoji(self, ui_manager, mock_console):
        """Test success method with default emoji."""
        ui_manager.success("Success")
        
        call_args = mock_console.print.call_args[0][0]
        assert "✓ Success" in call_args

    @pytest.mark.medium
    def test_warning_default_emoji(self, ui_manager, mock_console):
        """Test warning method with default emoji."""
        ui_manager.warning("Warning")
        
        call_args = mock_console.print.call_args[0][0]
        assert "⚠ Warning" in call_args

    @pytest.mark.medium
    def test_error_default_emoji(self, ui_manager, mock_console):
        """Test error method with default emoji."""
        ui_manager.error("Error")
        
        call_args = mock_console.print.call_args[0][0]
        assert "✗ Error" in call_args

    @pytest.mark.low
    def test_empty_message(self, ui_manager, mock_console):
        """Test methods with empty message."""
        ui_manager.info("")
        
        call_args = mock_console.print.call_args[0][0]
        assert "[cyan][/cyan]" in call_args


class TestProcessingMessageMethods:
    """Test processing-specific message methods."""

    @pytest.mark.critical
    def test_processing_method(self, ui_manager, mock_console):
        """Test processing message method."""
        ui_manager.processing("Processing file", emoji="🔄", indent=2)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "🔄 Processing file" in call_args
        assert "[cyan]Processing file[/cyan]" in call_args

    @pytest.mark.critical
    def test_file_action_method(self, ui_manager, mock_console):
        """Test file action message method."""
        ui_manager.file_action("Downloading file.pdf", emoji="📄", indent=1)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "📄 Downloading file.pdf" in call_args
        assert "[cyan]Downloading file.pdf[/cyan]" in call_args

    @pytest.mark.high
    def test_progress_update_method(self, ui_manager, mock_console):
        """Test progress update message method."""
        ui_manager.progress_update(25, 100, label="files", emoji="📁", indent=2)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "📁 25/100 files" in call_args
        assert "[cyan]25/100 files[/cyan]" in call_args
        assert "    " in call_args  # Indent level 2

    @pytest.mark.high
    def test_progress_update_default_params(self, ui_manager, mock_console):
        """Test progress update with default parameters."""
        ui_manager.progress_update(50, 100)
        
        call_args = mock_console.print.call_args[0][0]
        assert "📄 50/100 páginas" in call_args

    @pytest.mark.medium
    def test_progress_update_zero_values(self, ui_manager, mock_console):
        """Test progress update with zero values."""
        ui_manager.progress_update(0, 0, label="items")
        
        call_args = mock_console.print.call_args[0][0]
        assert "📄 0/0 items" in call_args


class TestSectionAndSeparatorMethods:
    """Test section and separator methods."""

    @pytest.mark.critical
    def test_section_method(self, ui_manager, mock_console):
        """Test section method."""
        ui_manager.section("Test Section", style="bold blue")
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "[bold blue]Test Section[/bold blue]" in call_args

    @pytest.mark.critical
    def test_section_default_style(self, ui_manager, mock_console):
        """Test section method with default style."""
        ui_manager.section("Default Section")
        
        call_args = mock_console.print.call_args[0][0]
        assert "[bold cyan]Default Section[/bold cyan]" in call_args

    @pytest.mark.critical
    def test_separator_method(self, ui_manager, mock_console):
        """Test separator method."""
        ui_manager.separator()
        
        mock_console.print.assert_called_once()
        # Should just print a newline

    @pytest.mark.medium
    def test_section_empty_title(self, ui_manager, mock_console):
        """Test section method with empty title."""
        ui_manager.section("")
        
        call_args = mock_console.print.call_args[0][0]
        assert "[bold cyan][/bold cyan]" in call_args

    @pytest.mark.medium
    def test_multiple_separators(self, ui_manager, mock_console):
        """Test multiple separator calls."""
        ui_manager.separator()
        ui_manager.separator()
        ui_manager.separator()
        
        assert mock_console.print.call_count == 3


class TestPanelAndTableMethods:
    """Test panel and table methods."""

    @pytest.mark.critical
    def test_panel_method(self, ui_manager, mock_console):
        """Test panel method."""
        with patch('ui.Panel') as mock_panel_class:
            mock_panel = Mock()
            mock_panel_class.fit.return_value = mock_panel
            
            ui_manager.panel("Panel content", title="Test Panel", border_style="green")
            
            mock_panel_class.fit.assert_called_once_with(
                "Panel content",
                title="Test Panel",
                border_style="green",
                title_align="center"
            )
            mock_console.print.assert_called_once_with(mock_panel)

    @pytest.mark.high
    def test_panel_minimal_params(self, ui_manager, mock_console):
        """Test panel method with minimal parameters."""
        with patch('ui.Panel') as mock_panel_class:
            mock_panel = Mock()
            mock_panel_class.fit.return_value = mock_panel
            
            ui_manager.panel("Simple content")
            
            mock_panel_class.fit.assert_called_once_with(
                "Simple content",
                title=None,
                border_style="cyan",
                title_align="center"
            )

    @pytest.mark.high
    def test_table_method(self, ui_manager, mock_console):
        """Test table method."""
        with patch('ui.Table') as mock_table_class:
            mock_table = Mock()
            mock_table_class.return_value = mock_table
            
            columns = [("Name", "cyan", "left"), ("Count", "green", "right")]
            rows = [["Item 1", "10"], ["Item 2", "20"]]
            
            ui_manager.table("Test Table", columns, rows)
            
            mock_table_class.assert_called_once_with(title="Test Table", box=mock_table_class.ROUNDED)
            mock_table.add_column.assert_called()
            mock_table.add_row.assert_called()
            mock_console.print.assert_called_once_with(mock_table)

    @pytest.mark.medium
    def test_panel_with_markup_content(self, ui_manager, mock_console):
        """Test panel with Rich markup content."""
        with patch('ui.Panel') as mock_panel_class:
            mock_panel = Mock()
            mock_panel_class.fit.return_value = mock_panel
            
            content = "[bold]Bold text[/bold] and [red]red text[/red]"
            ui_manager.panel(content)
            
            mock_panel_class.fit.assert_called_once_with(
                content,
                title=None,
                border_style="cyan",
                title_align="center"
            )


class TestContextHelpers:
    """Test context helper methods."""

    @pytest.mark.critical
    def test_status_method(self, ui_manager):
        """Test status method returns context manager."""
        with patch('ui.Console') as mock_console_class:
            mock_console = Mock()
            mock_status = Mock()
            mock_console.status.return_value = mock_status
            mock_console_class.return_value = mock_console
            
            manager = UIManager(console=mock_console)
            status_context = manager.status("Loading...")
            
            mock_console.status.assert_called_once_with("[bold green]Loading...")
            assert status_context is mock_status

    @pytest.mark.high
    def test_status_as_context_manager(self, ui_manager):
        """Test status method used as context manager."""
        with patch('ui.Console') as mock_console_class:
            mock_console = Mock()
            mock_status = Mock()
            mock_status.__enter__ = Mock(return_value="context")
            mock_status.__exit__ = Mock(return_value=None)
            mock_console.status.return_value = mock_status
            mock_console_class.return_value = mock_console
            
            manager = UIManager(console=mock_console)
            
            with manager.status("Processing...") as status:
                assert status == "context"
            
            mock_status.__enter__.assert_called_once()
            mock_status.__exit__.assert_called_once()


class TestDomainSpecificMethods:
    """Test domain-specific message methods."""

    @pytest.mark.critical
    def test_ocr_active_method(self, ui_manager, mock_console):
        """Test OCR active method."""
        ui_manager.ocr_active("por+eng", indent=2)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "🔍 OCR ativo (por+eng)" in call_args
        assert "[magenta]OCR ativo (por+eng)[/magenta]" in call_args
        assert "    " in call_args  # Indent level 2

    @pytest.mark.critical
    def test_document_pages_method(self, ui_manager, mock_console):
        """Test document pages method."""
        ui_manager.document_pages(25, indent=2)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "📊 Documento tem 25 páginas" in call_args
        assert "[cyan]Documento tem 25 páginas[/cyan]" in call_args
        assert "    " in call_args  # Indent level 2

    @pytest.mark.critical
    def test_file_complete_method(self, ui_manager, mock_console):
        """Test file complete method."""
        ui_manager.file_complete(15.5, 10, has_ocr=True, indent=1)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "✓ Completo: 15.50 MB (10 páginas, com OCR)" in call_args
        assert "[green]Completo: 15.50 MB (10 páginas, com OCR)[/green]" in call_args
        assert "  " in call_args  # Indent level 1

    @pytest.mark.high
    def test_file_complete_without_ocr(self, ui_manager, mock_console):
        """Test file complete method without OCR."""
        ui_manager.file_complete(8.2, 5, has_ocr=False)
        
        call_args = mock_console.print.call_args[0][0]
        assert "✓ Completo: 8.20 MB (5 páginas, sem OCR)" in call_args

    @pytest.mark.high
    def test_scroll_warning_method(self, ui_manager, mock_console):
        """Test scroll warning method."""
        ui_manager.scroll_warning(indent=2)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "⚠ Não use mouse durante o scroll (~40s)" in call_args
        assert "[yellow]Não use mouse durante o scroll (~40s)[/yellow]" in call_args

    @pytest.mark.high
    def test_waiting_method(self, ui_manager, mock_console):
        """Test waiting method."""
        ui_manager.waiting(5, indent=1)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "  Aguardando (5s)..." in call_args
        assert "[dim]Aguardando (5s)...[/dim]" in call_args

    @pytest.mark.high
    def test_file_interrupted_method(self, ui_manager, mock_console):
        """Test file interrupted method."""
        ui_manager.file_interrupted("test_file.pdf", indent=2)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "⚠️ Interrompido: test_file.pdf" in call_args
        assert "[yellow]Interrompido: test_file.pdf[/yellow]" in call_args

    @pytest.mark.high
    def test_file_cancelled_method(self, ui_manager, mock_console):
        """Test file cancelled method."""
        ui_manager.file_cancelled("cancelled_file.pdf", indent=1)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "⚠️ Cancelado: cancelled_file.pdf" in call_args
        assert "[yellow]Cancelado: cancelled_file.pdf[/yellow]" in call_args

    @pytest.mark.medium
    def test_file_complete_decimal_sizes(self, ui_manager, mock_console):
        """Test file complete method with decimal sizes."""
        ui_manager.file_complete(0.123, 1, has_ocr=False)
        
        call_args = mock_console.print.call_args[0][0]
        assert "0.12 MB" in call_args  # Should format to 2 decimal places

    @pytest.mark.medium
    def test_ocr_active_default_indent(self, ui_manager, mock_console):
        """Test OCR active method with default indent."""
        ui_manager.ocr_active("eng")
        
        call_args = mock_console.print.call_args[0][0]
        assert "🔍 OCR ativo (eng)" in call_args
        assert "  " in call_args  # Default indent level 1

    @pytest.mark.low
    def test_waiting_default_seconds(self, ui_manager, mock_console):
        """Test waiting method with default seconds."""
        ui_manager.waiting()
        
        call_args = mock_console.print.call_args[0][0]
        assert "Aguardando (2s)..." in call_args


class TestGlobalUIInstance:
    """Test global UI instance."""

    @pytest.mark.critical
    def test_global_ui_instance_exists(self):
        """Test that global ui instance exists."""
        assert ui is not None
        assert isinstance(ui, UIManager)

    @pytest.mark.high
    def test_global_ui_has_console(self):
        """Test that global ui has console."""
        assert hasattr(ui, 'console')
        assert ui.console is not None

    @pytest.mark.high
    def test_global_ui_methods_work(self):
        """Test that global ui methods work."""
        # This should not raise any exceptions
        ui.info("Test message")
        ui.success("Success message")
        ui.warning("Warning message")
        ui.error("Error message")

    @pytest.mark.medium
    def test_global_ui_singleton_behavior(self):
        """Test that global ui behaves like singleton."""
        ui1 = ui
        ui2 = ui
        assert ui1 is ui2

    @pytest.mark.low
    def test_global_ui_initialization(self):
        """Test global ui initialization."""
        # Should be initialized automatically when module is imported
        assert hasattr(ui, '_indent_levels')
        assert len(ui._indent_levels) == 4


class TestUIIntegration:
    """Integration tests for UI functionality."""

    @pytest.mark.integration
    def test_complete_workflow_scenario(self):
        """Test complete UI workflow scenario."""
        # This simulates a typical download workflow
        ui.section("Download Process")
        ui.info("Starting download", emoji="🚀")
        ui.file_action("Processing file.pdf")
        ui.progress_update(25, 100, "files")
        ui.file_complete(5.2, 10, has_ocr=True)
        ui.success("Download completed")
        ui.separator()

    @pytest.mark.integration
    def test_error_handling_scenario(self):
        """Test UI error handling scenario."""
        ui.section("Error Scenario")
        ui.warning("Potential issue detected")
        ui.error("Download failed", emoji="💥")
        ui.file_interrupted("corrupted_file.pdf")
        ui.info("Attempting recovery...")

    @pytest.mark.integration
    def test_progress_tracking_scenario(self):
        """Test progress tracking scenario."""
        ui.section("Progress Tracking")
        
        files = ["file1.pdf", "file2.pdf", "file3.pdf"]
        total_files = len(files)
        
        for i, filename in enumerate(files, 1):
            ui.file_action(filename)
            ui.progress_update(i, total_files, "files")
        
        ui.success("All files processed")

    @pytest.mark.integration
    def test_multilingual_scenario(self):
        """Test UI with different language content."""
        ui.section("Internationalization Test")
        ui.info("English message")
        ui.info("Mensagem em português")
        ui.info("消息中文")
        ui.info("Сообщение на русском")
        ui.success("All languages supported")

    @pytest.mark.integration
    def test_nested_indentation_scenario(self):
        """Test nested indentation scenarios."""
        ui.section("Nested Indentation")
        
        ui.info("Level 0 message")
        ui.info("Level 1 message", indent=1)
        ui.info("Level 2 message", indent=2)
        ui.info("Level 3 message", indent=3)
        
        ui.plain("Plain at level 2", indent=2)
        ui.dim("Dim at level 1", indent=1)

    @pytest.mark.integration
    def test_performance_with_many_calls(self):
        """Test performance with many UI calls."""
        import time
        
        start_time = time.time()
        
        for i in range(100):
            ui.file_action(f"file_{i}.pdf")
            ui.progress_update(i, 100, "files")
        
        elapsed_time = time.time() - start_time
        
        # Should be reasonably fast
        assert elapsed_time < 2.0