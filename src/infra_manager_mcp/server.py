"""
Main MCP Server for Infrastructure Manager
"""

import asyncio
import logging
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server

from .config import init_config, get_config
from .tools import register_tools

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
    ],
)

logger = logging.getLogger(__name__)


async def main():
    """Point d'entrée principal du serveur MCP"""
    try:
        # Charger la configuration
        logger.info("Loading configuration...")
        config = init_config()
        logger.info(f"Configuration loaded: {config.mcp.name} v{config.mcp.version}")

        # Créer le serveur MCP
        server = Server(config.mcp.name)
        logger.info("MCP Server created")

        # Enregistrer les outils
        logger.info("Registering MCP tools...")
        register_tools(server)
        logger.info("Tools registered successfully")

        # Configurer le logging selon la configuration
        log_level = getattr(logging, config.mcp.log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)

        # Ajouter un handler pour le fichier de log si spécifié
        if config.mcp.log_file:
            try:
                log_file = Path(config.mcp.log_file)
                log_file.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(
                    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
                )
                logging.getLogger().addHandler(file_handler)
                logger.info(f"Logging to file: {config.mcp.log_file}")
            except Exception as e:
                logger.warning(f"Failed to setup file logging: {e}")

        # Démarrer le serveur via stdio
        logger.info("Starting MCP server via stdio...")
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        logger.error("Please create a config.yaml file. See config.example.yaml for reference.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


def run():
    """Fonction wrapper pour exécuter le serveur"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run()
