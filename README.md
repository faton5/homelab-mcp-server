# Homelab MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

**Extensible MCP server for homelab infrastructure management** - Supports Proxmox VE, with planned support for VMware and other homelab tools. Control your entire lab directly from Claude AI.

## 🌟 Supported Platforms

- ✅ **Proxmox VE** - Full support (VMs, containers, command execution, monitoring)
- 🚧 **VMware vSphere** - Planned
- 🚧 **Docker Management** - Planned
- 🚧 **Network Equipment** - Planned
- 🚧 **Monitoring Tools** (Grafana, Prometheus) - Planned

## 🎯 Current Features (Proxmox VE)

- **🔍 Auto-Discovery**: Automatically detects all VMs and containers from your Proxmox cluster
- **🎮 VM Control**: Start, stop, restart VMs and containers
- **💻 Command Execution**: Execute shell commands on VMs via Proxmox API (qemu-guest-agent) or SSH
- **📊 Monitoring**: Get real-time status, system info, and resource usage
- **🔄 Updates Management**: Check and install system updates on your VMs
- **🔒 Security**: Built-in command validation and confirmation for dangerous operations
- **⚙️ Easy Setup**: Configure everything via docker-compose environment variables

## 📋 Requirements

- **Proxmox VE** 7.0+ with API access
- **Docker** and **Docker Compose**
- **Proxmox API Token** (created in Proxmox)
- **qemu-guest-agent** installed on VMs (for command execution via API)
- Optionally: SSH access to VMs for advanced command execution

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/faton5/homelab-mcp-server.git
cd homelab-mcp-server
```

### 2. Create your configuration

Copy the example docker-compose file:

```bash
cp docker-compose.example.yml docker-compose.yml
```

Edit `docker-compose.yml` and fill in your Proxmox credentials:

```yaml
environment:
  # Proxmox Configuration (REQUIRED)
  - PROXMOX_HOST=192.168.1.100          # Your Proxmox host IP
  - PROXMOX_PORT=8006                    # Proxmox API port
  - PROXMOX_TOKEN_ID=root@pam!mcp        # Your API token ID
  - PROXMOX_TOKEN_SECRET=your-secret-here # Your API token secret
  - PROXMOX_VERIFY_SSL=false             # Set to true if you have valid SSL cert
```

### 3. Start the MCP server

```bash
docker compose up -d
```

### 4. Configure your Claude client

The MCP server supports two connection modes:
- **Local (stdio)**: For Claude Desktop running on the same machine as the Docker container
- **Remote (SSE)**: For Claude Desktop on another machine, Claude Code, Codeium, or other MCP clients

#### Option A: Remote Access (Recommended for remote servers)

If your MCP server runs on a remote server (e.g., in your Proxmox VM), use **SSE mode**:

**1. Configure docker-compose.yml for SSE:**

```yaml
environment:
  - MCP_TRANSPORT=sse
  - MCP_HOST=0.0.0.0
  - MCP_PORT=8000

ports:
  - "8000:8000"
```

**2. Configure your client:**

<details>
<summary><b>Claude Desktop</b></summary>

Edit your config file:
- **macOS/Linux**: `~/.config/claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "homelab": {
      "url": "http://YOUR_SERVER_IP:8000/sse"
    }
  }
}
```

Replace `YOUR_SERVER_IP` with your Docker host IP (e.g., `192.168.1.50`).
</details>

<details>
<summary><b>Claude Code (CLI)</b></summary>

```bash
# Add to your Claude Code config
claude-code mcp add homelab http://YOUR_SERVER_IP:8000/sse
```
</details>

<details>
<summary><b>Codeium</b></summary>

Add to Codeium settings:

```json
{
  "mcp.servers": {
    "homelab": {
      "url": "http://YOUR_SERVER_IP:8000/sse"
    }
  }
}
```
</details>

<details>
<summary><b>Other MCP clients (Gemini, Continue.dev, etc.)</b></summary>

Use the SSE endpoint URL:
```
http://YOUR_SERVER_IP:8000/sse
```

Configure according to your client's MCP server settings.
</details>

#### Option B: Local Access (stdio mode)

If Claude Desktop runs on the same machine as Docker:

**1. Configure docker-compose.yml:**

```yaml
environment:
  - MCP_TRANSPORT=stdio  # or remove this line (stdio is default)
```

**2. Configure Claude Desktop:**

Edit your config file:
- **macOS/Linux**: `~/.config/claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "homelab": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "infra-manager-mcp",
        "python",
        "-m",
        "infra_manager_mcp"
      ]
    }
  }
}
```

### 5. Restart your client

- **Claude Desktop**: Press **Ctrl+R** (or **Cmd+R** on macOS)
- **Claude Code**: Restart the CLI
- **Codeium/Others**: Reload the MCP configuration

## 🎯 Usage Examples

Once configured, you can ask Claude:

- *"List all my Proxmox VMs"*
- *"What's the status of my HLB-VPN-01 VM?"*
- *"Start the TIKTOK VM"*
- *"Execute 'uptime' on HLB-Adguard-01"*
- *"Get system information for HLB-NAS-01"*
- *"Check for updates on my VMs"*
- *"Show me the AdGuard configuration"*

## 🔧 Configuration Options

### Environment Variables

All configuration is done via environment variables in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `PROXMOX_HOST` | *(required)* | Proxmox server IP/hostname |
| `PROXMOX_PORT` | `8006` | Proxmox API port |
| `PROXMOX_TOKEN_ID` | *(required)* | API token (format: `user@realm!tokenname`) |
| `PROXMOX_TOKEN_SECRET` | *(required)* | API token secret |
| `PROXMOX_VERIFY_SSL` | `false` | Verify SSL certificates |
| `PROXMOX_TIMEOUT` | `30` | API request timeout (seconds) |
| `SSH_ENABLED` | `true` | Enable SSH support |
| `SSH_DEFAULT_USER` | `root` | Default SSH user |
| `MCP_NAME` | `infra-manager` | MCP server name |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Advanced Configuration (Optional)

For advanced users, you can create a `config.yaml` file for more detailed configuration including:
- Manual server definitions with SSH access
- Custom security restrictions
- Command blocking rules

See `config.example.yaml` for details.

## 🛡️ Security Features

- **Command Validation**: Dangerous commands require explicit user confirmation
- **Blocked Commands**: Fork bombs, system wipes, and other destructive commands are blocked
- **API Token Authentication**: Uses Proxmox API tokens (not root password)
- **No Secrets in Git**: All sensitive data configured via environment variables

### Confirmed Actions

These actions require explicit user confirmation:
- Stopping/restarting VMs
- Installing system updates
- Dangerous commands (rm -rf, mkfs, reboot, etc.)

### Blocked Commands

Completely blocked and never executed:
- `rm -rf /` and variants
- Fork bombs
- Disk formatting on system drives

## 📚 Available MCP Tools

### Proxmox Management

| Tool | Description |
|------|-------------|
| `list_servers` | List all configured servers and auto-detected VMs |
| `list_nodes` | List all Proxmox nodes with status |
| `list_vms` | List all VMs and containers |
| `get_vm_status` | Get detailed status of a specific VM |
| `start_vm` | Start a VM or container |
| `stop_vm` | Stop a VM or container (requires confirmation) |
| `restart_vm` | Restart a VM or container (requires confirmation) |
| `execute_command` | Execute a shell command on a VM |
| `get_system_info` | Get CPU, RAM, disk, and load information |
| `check_updates` | Check for available system updates |
| `install_updates` | Install system updates (requires confirmation) |

## 🔮 Roadmap

Future platform support planned:

- [ ] **VMware vSphere/ESXi** - VM management and monitoring
- [ ] **Docker** - Container management across hosts
- [ ] **Network Equipment** - Ubiquiti, pfSense, etc.
- [ ] **Monitoring Integration** - Grafana, Prometheus, Zabbix
- [ ] **Backup Systems** - Proxmox Backup Server, Veeam
- [ ] **Home Automation** - Home Assistant, Node-RED
- [ ] **Storage Systems** - TrueNAS, Synology

## 🔍 Troubleshooting

### VMs not detected
- Ensure your API token has proper permissions in Proxmox
- Check that the Proxmox host is reachable from the Docker container
- Verify `PROXMOX_HOST` and credentials in `docker-compose.yml`

### Command execution fails
- For Proxmox API method: Install `qemu-guest-agent` in your VMs
- For SSH method: Configure SSH access in `config.yaml`

### MCP server not appearing in Claude
- Check that the container is running: `docker ps`
- Verify the config path in `claude_desktop_config.json`
- Check container logs: `docker logs infra-manager-mcp`
- Restart Claude Desktop (Ctrl+R / Cmd+R)

## 📖 Documentation

- [Quick Start Guide](docs/QUICK_START.md)
- [Proxmox Setup](docs/PROXMOX_SETUP.md)
- [SSH Configuration](docs/SSH_SETUP.md)
- [Windows Setup Guide](docs/WINDOWS_SETUP.md)

## 🤝 Contributing

Contributions are welcome! Whether you want to:
- Add support for a new platform (VMware, Docker, etc.)
- Improve existing features
- Fix bugs or improve documentation

Please feel free to submit a Pull Request or open an issue.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- Powered by [proxmoxer](https://github.com/proxmoxer/proxmoxer) Python library
- Designed for [Claude AI](https://claude.ai/) by Anthropic

## 🔗 Links

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Proxmox VE API Documentation](https://pve.proxmox.com/pve-docs/api-viewer/)
- [Claude Desktop](https://claude.ai/download)

---

**Made with ❤️ for the homelab community**
