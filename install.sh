#!/bin/bash

# ------------------------------------------------------------------------------
# py2puml Installation Script
# ------------------------------------------------------------------------------
# This script installs py2puml with optional MCP server support.
# It provides interactive component selection and Cursor configuration.
# ------------------------------------------------------------------------------

# --- Global Variables ---
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Installation options
INSTALL_MCP=false
CONFIGURE_CURSOR=false
SKIP_MCP=false

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

# Print colored text
print_color() {
    printf "${!1}%s${NC}\n" "$2"
}

# Print the banner
print_banner() {
    print_color "BLUE" "
   py2puml - Python to PlantUML Converter
   "
}

# Handle errors and exit
handle_error() {
    echo ""
    print_color "RED" "Error: $1"
    print_color "YELLOW" "Press Enter to exit..."
    read -r
    exit 1
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ------------------------------------------------------------------------------
# Prerequisite Checks
# ------------------------------------------------------------------------------

check_prerequisites() {
    print_color "BLUE" "Checking prerequisites..."
    
    # Check Python
    if ! command_exists python3; then
        handle_error "Python 3 is required but not installed"
    fi
    
    # Check pip
    if ! command_exists pip3; then
        handle_error "pip3 is required but not installed"
    fi
    
    # Check Python version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    required_version="3.7"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        handle_error "Python 3.7 or higher is required. Found: $python_version"
    fi
    
    print_color "GREEN" "✓ Prerequisites check passed"
}

# ------------------------------------------------------------------------------
# Installation Functions
# ------------------------------------------------------------------------------

install_py2puml() {
    print_color "BLUE" "Installing py2puml..."
    
    # Install in development mode
    if pip3 install -e .; then
        print_color "GREEN" "✓ py2puml installed successfully"
    else
        handle_error "Failed to install py2puml"
    fi
}

install_mcp_server() {
    print_color "BLUE" "Installing MCP server..."
    
    # Make MCP server executable
    if chmod +x mcp_file_analyzer.py; then
        print_color "GREEN" "✓ MCP server made executable"
    else
        print_color "YELLOW" "Warning: Could not make MCP server executable"
    fi
    
    # Test MCP server (check if it can be imported and instantiated)
    if python3 -c "from mcp_file_analyzer import MCPFileAnalyzer; analyzer = MCPFileAnalyzer(); print('MCP server test passed')" >/dev/null 2>&1; then
        print_color "GREEN" "✓ MCP server test passed"
    else
        print_color "YELLOW" "Warning: MCP server test failed"
    fi
}

configure_cursor() {
    print_color "BLUE" "Configuring Cursor for MCP server..."
    
    # Create Cursor configuration directory
    cursor_config_dir="$HOME/.cursor"
    mkdir -p "$cursor_config_dir"
    
    # Create backup of existing mcp.json if it exists
    if [[ -f "$cursor_config_dir/mcp.json" ]]; then
        backup_file="$cursor_config_dir/mcp.json.backup"
        cp "$cursor_config_dir/mcp.json" "$backup_file"
        print_color "GREEN" "✓ Backup created: $backup_file"
    fi
    
    # Create MCP server configuration
    cat > "$cursor_config_dir/mcp.json" << EOF
{
    "mcpServers": {
        "context7": {
            "url": "https://mcp.context7.com/mcp"
        },
        "how_to_do": {
            "transport": "stdio",
            "command": "python3",
            "args": [
                "/home/mike/.cursor/tools/how_to_do.py"
            ]
        },
        "py-analyzer": {
            "command": "python3",
            "args": ["$(pwd)/mcp_file_analyzer.py"],
            "env": {}
        }
    }
}
EOF
    
    print_color "GREEN" "✓ Cursor configuration created at $cursor_config_dir/mcp.json"
    print_color "YELLOW" "Note: You may need to restart Cursor for changes to take effect"
}

# ------------------------------------------------------------------------------
# Interactive Selection
# ------------------------------------------------------------------------------

show_menu() {
    echo ""
    print_color "BLUE" "py2puml Installation Options:"
    echo "1) Install py2puml only (basic functionality)"
    echo "2) Install py2puml + MCP server (recommended)"
    echo "3) Install py2puml + MCP server + configure Cursor"
    echo "4) Exit"
    echo ""
}

get_user_choice() {
    while true; do
        read -p "Please select an option (1-4): " choice
        case $choice in
            1)
                INSTALL_MCP=false
                CONFIGURE_CURSOR=false
                break
                ;;
            2)
                INSTALL_MCP=true
                CONFIGURE_CURSOR=false
                break
                ;;
            3)
                INSTALL_MCP=true
                CONFIGURE_CURSOR=true
                break
                ;;
            4)
                print_color "YELLOW" "Installation cancelled"
                exit 0
                ;;
            *)
                print_color "RED" "Invalid option. Please select 1-4."
                ;;
        esac
    done
}

# ------------------------------------------------------------------------------
# Command Line Arguments
# ------------------------------------------------------------------------------

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --install-mcp)
                INSTALL_MCP=true
                shift
                ;;
            --skip-mcp)
                SKIP_MCP=true
                shift
                ;;
            --configure-cursor)
                CONFIGURE_CURSOR=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --install-mcp        Install MCP server"
                echo "  --skip-mcp          Skip MCP server installation"
                echo "  --configure-cursor  Configure Cursor for MCP server"
                echo "  --help, -h          Show this help message"
                echo ""
                echo "If no options are provided, interactive mode will be used."
                exit 0
                ;;
            *)
                print_color "RED" "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
        shift
    done
}

# ------------------------------------------------------------------------------
# Main Installation Process
# ------------------------------------------------------------------------------

main() {
    print_banner
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # Check prerequisites
    check_prerequisites
    
    # If no command line options, show interactive menu
    if [[ "$INSTALL_MCP" == false && "$SKIP_MCP" == false && "$CONFIGURE_CURSOR" == false ]]; then
        show_menu
        get_user_choice
    fi
    
    # Install py2puml
    install_py2puml
    
    # Install MCP server if requested
    if [[ "$INSTALL_MCP" == true && "$SKIP_MCP" == false ]]; then
        install_mcp_server
    fi
    
    # Configure Cursor if requested
    if [[ "$CONFIGURE_CURSOR" == true ]]; then
        configure_cursor
    fi
    
    # Final summary
    echo ""
    print_color "GREEN" "Installation completed successfully!"
    echo ""
    
    if [[ "$INSTALL_MCP" == true ]]; then
        print_color "BLUE" "MCP server is available at: $(pwd)/mcp_file_analyzer.py"
        echo "You can test it with: python3 mcp_file_analyzer.py"
    fi
    
    if [[ "$CONFIGURE_CURSOR" == true ]]; then
        print_color "BLUE" "Cursor has been configured for MCP server"
        echo "Restart Cursor to activate the MCP server"
    fi
    
    echo ""
    print_color "YELLOW" "Press Enter to exit..."
    read -r
}

# ------------------------------------------------------------------------------
# Script Execution
# ------------------------------------------------------------------------------

# Run main function with all arguments
main "$@"
