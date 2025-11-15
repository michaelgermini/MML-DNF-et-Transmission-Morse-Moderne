"""
API REST/WebSocket pour DNF-MML-Morse

Fournit une interface web pour le système de transmission
avec support REST et WebSocket temps réel.
"""

import asyncio
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .core import DNFMMLMorseSystem
from .streaming import StreamingManager


class DNFMMLMorseAPI:
    """
    API REST/WebSocket pour le système DNF-MML-Morse
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialisation de l'API

        Args:
            config: Configuration du système
        """
        self.config = config or {}
        self.system = DNFMMLMorseSystem(self.config)
        self.streaming_manager = StreamingManager() if self.config.get('streaming_enabled', True) else None

        # Sessions actives pour WebSocket
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        # Statistiques API
        self.api_stats = {
            'requests_total': 0,
            'transmissions_total': 0,
            'websocket_connections': 0,
            'errors_total': 0,
        }

    def create_app(self) -> FastAPI:
        """
        Créer l'application FastAPI

        Returns:
            Application FastAPI configurée
        """
        app = FastAPI(
            title="DNF-MML-Morse API",
            description="API REST/WebSocket pour transmission de documents via radio amateur",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # Middleware CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # À restreindre en production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Routes API
        self._setup_routes(app)

        return app

    def _setup_routes(self, app: FastAPI):
        """Configuration des routes API"""

        @app.get("/", response_class=HTMLResponse)
        async def root():
            """Page d'accueil avec interface web"""
            return self._get_web_interface()

        @app.get("/api/health")
        async def health_check():
            """Vérification de santé du système"""
            self.api_stats['requests_total'] += 1

            try:
                system_status = self.system.get_system_status()
                streaming_status = await self.system.get_streaming_status() if self.streaming_manager else {'streaming_enabled': False}

                return {
                    'status': 'healthy',
                    'system': system_status,
                    'streaming': streaming_status,
                    'api_stats': self.api_stats,
                }
            except Exception as e:
                self.api_stats['errors_total'] += 1
                raise HTTPException(status_code=500, detail=f"Health check failed: {e}")

        @app.post("/api/transmit")
        async def transmit_document(
            background_tasks: BackgroundTasks,
            file: UploadFile = File(...),
            destination: str = "WEB_CLIENT",
            use_streaming: bool = None
        ):
            """Transmettre un document"""
            self.api_stats['requests_total'] += 1

            try:
                # Sauvegarder le fichier temporairement
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_path = temp_file.name

                # Analyser le fichier pour déterminer la méthode
                if use_streaming is None:
                    analysis = await self.system.analyze_file_for_streaming(temp_path)
                    use_streaming = analysis['recommended_method'] == 'streaming'

                # Transmission
                if use_streaming and self.streaming_manager:
                    result = await self.system.transmit_file_streaming(temp_path, destination)
                else:
                    result = await self.system.transmit_document(temp_path, destination)

                self.api_stats['transmissions_total'] += 1

                # Nettoyer le fichier temporaire en arrière-plan
                background_tasks.add_task(os.unlink, temp_path)

                return {
                    'success': True,
                    'transmission': result,
                    'file_info': {
                        'original_name': file.filename,
                        'size': len(content),
                        'method': 'streaming' if use_streaming else 'direct',
                    }
                }

            except Exception as e:
                self.api_stats['errors_total'] += 1
                raise HTTPException(status_code=500, detail=f"Transmission failed: {e}")

        @app.get("/api/status")
        async def get_system_status():
            """État du système"""
            self.api_stats['requests_total'] += 1

            try:
                status = self.system.get_system_status()
                streaming = await self.system.get_streaming_status() if self.streaming_manager else None

                return {
                    'system': status,
                    'streaming': streaming,
                    'api': self.api_stats,
                }
            except Exception as e:
                self.api_stats['errors_total'] += 1
                raise HTTPException(status_code=500, detail=f"Status check failed: {e}")

        @app.get("/api/sessions")
        async def list_sessions():
            """Liste des sessions de streaming actives"""
            self.api_stats['requests_total'] += 1

            if not self.streaming_manager:
                return {'sessions': [], 'streaming_enabled': False}

            sessions = []
            for session_id in self.streaming_manager.list_active_sessions():
                status = await self.streaming_manager.get_session_status(session_id)
                sessions.append(status)

            return {
                'sessions': sessions,
                'count': len(sessions),
                'streaming_enabled': True,
            }

        @app.get("/api/sessions/{session_id}")
        async def get_session_status(session_id: str):
            """État d'une session spécifique"""
            self.api_stats['requests_total'] += 1

            if not self.streaming_manager:
                raise HTTPException(status_code=404, detail="Streaming not enabled")

            status = await self.streaming_manager.get_session_status(session_id)
            if status.get('status') == 'not_found':
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

            return status

        @app.post("/api/sessions/{session_id}/cancel")
        async def cancel_session(session_id: str):
            """Annuler une session de streaming"""
            self.api_stats['requests_total'] += 1

            if not self.streaming_manager:
                raise HTTPException(status_code=404, detail="Streaming not enabled")

            await self.streaming_manager.end_session(session_id)
            return {'status': 'cancelled', 'session_id': session_id}

        @app.post("/api/analyze")
        async def analyze_file(file: UploadFile = File(...)):
            """Analyser un fichier pour déterminer la stratégie optimale"""
            self.api_stats['requests_total'] += 1

            try:
                # Sauvegarder temporairement
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_path = temp_file.name

                # Analyser
                analysis = await self.system.analyze_file_for_streaming(temp_path)

                # Nettoyer
                os.unlink(temp_path)

                return {
                    'file_info': {
                        'name': file.filename,
                        'size': len(content),
                        'size_mb': len(content) / (1024 * 1024),
                    },
                    'analysis': analysis,
                }

            except Exception as e:
                self.api_stats['errors_total'] += 1
                raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

        @app.get("/api/config")
        async def get_config():
            """Configuration actuelle"""
            self.api_stats['requests_total'] += 1

            return {
                'system_config': self.system.config,
                'api_stats': self.api_stats,
                'capabilities': {
                    'streaming': self.streaming_manager is not None,
                    'unicode_support': True,
                    'compression_levels': ['light', 'standard', 'aggressive'],
                    'morse_modes': ['standard', 'optimized', 'robust'],
                    'transports': ['cw', 'js8call', 'packet', 'aprs'],
                }
            }

        @app.get("/api/demo")
        async def get_demo_data():
            """Données de démonstration"""
            self.api_stats['requests_total'] += 1

            return {
                'sample_transmission': {
                    'text': 'HELLO WORLD',
                    'morse_standard': '.... . .-.. .-.. --- / .-- --- .- .-. .-.. -..',
                    'morse_optimized': '.... . .-.. .-.. --- / .-- --- .- .-. .-.. -..',
                },
                'unicode_examples': {
                    'french': 'Café résumé naïve',
                    'emoji': '❤️ 👍 😂',
                    'mixed': 'Hello 世界 🌍 Café!',
                },
                'compression_example': {
                    'original': '<H1>Titre</H1><P>Paragraphe</P>' * 10,
                    'ratio_estimate': 0.65,
                }
            }

    def _get_web_interface(self) -> str:
        """Interface web HTML pour l'API"""
        html = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>DNF-MML-Morse API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                h1 { color: #2c3e50; text-align: center; }
                .section { margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; background: #ecf0f1; }
                .upload-area { border: 2px dashed #3498db; padding: 20px; text-align: center; margin: 20px 0; border-radius: 4px; }
                .btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                .btn:hover { background: #2980b9; }
                .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
                .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
                .stat-card { background: #f8f9fa; padding: 15px; border-radius: 4px; text-align: center; }
                .stat-value { font-size: 24px; font-weight: bold; color: #3498db; }
                pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📡 DNF-MML-Morse API</h1>

                <div class="section">
                    <h2>🚀 Transmission de documents</h2>
                    <div class="upload-area">
                        <form id="uploadForm" enctype="multipart/form-data">
                            <input type="file" id="fileInput" accept="*/*" required>
                            <br><br>
                            <label>Destination: <input type="text" id="destination" value="WEB_CLIENT" placeholder="Callsign destinataire"></label>
                            <br><br>
                            <button type="submit" class="btn">📤 Transmettre</button>
                        </form>
                    </div>
                    <div id="transmissionStatus"></div>
                </div>

                <div class="section">
                    <h2>📊 État du système</h2>
                    <button onclick="checkStatus()" class="btn">🔍 Vérifier l'état</button>
                    <div id="systemStatus"></div>
                </div>

                <div class="section">
                    <h2>🎯 Démonstration</h2>
                    <button onclick="runDemo()" class="btn">▶️ Lancer la démo</button>
                    <div id="demoResults"></div>
                </div>

                <div class="section">
                    <h2>📚 Liens utiles</h2>
                    <ul>
                        <li><a href="/docs">📖 Documentation API (Swagger)</a></li>
                        <li><a href="/redoc">📋 Documentation alternative (ReDoc)</a></li>
                        <li><a href="https://github.com/dnf-mml-morse/dnf-mml-morse">💻 Code source</a></li>
                    </ul>
                </div>
            </div>

            <script>
                async function uploadFile() {
                    const form = document.getElementById('uploadForm');
                    const formData = new FormData(form);
                    const fileInput = document.getElementById('fileInput');
                    const destination = document.getElementById('destination').value;

                    if (!fileInput.files[0]) {
                        alert('Veuillez sélectionner un fichier');
                        return;
                    }

                    formData.append('destination', destination);

                    const statusDiv = document.getElementById('transmissionStatus');
                    statusDiv.innerHTML = '<div class="status">📤 Transmission en cours...</div>';

                    try {
                        const response = await fetch('/api/transmit', {
                            method: 'POST',
                            body: formData
                        });

                        const result = await response.json();

                        if (result.success) {
                            statusDiv.innerHTML = `
                                <div class="status success">
                                    ✅ Transmission réussie!<br>
                                    📄 Fichier: ${result.file_info.original_name}<br>
                                    📏 Taille: ${(result.file_info.size / 1024).toFixed(1)} KB<br>
                                    🎯 Destination: ${result.transmission.destination}<br>
                                    ⏱️ Durée: ${result.transmission.transmission_time || 'N/A'}s<br>
                                    📊 Ratio compression: ${(result.transmission.compression_ratio * 100).toFixed(1)}%
                                </div>
                            `;
                        } else {
                            statusDiv.innerHTML = `<div class="status error">❌ Erreur: ${result.transmission.error}</div>`;
                        }
                    } catch (error) {
                        statusDiv.innerHTML = `<div class="status error">❌ Erreur réseau: ${error.message}</div>`;
                    }
                }

                async function checkStatus() {
                    const statusDiv = document.getElementById('systemStatus');

                    try {
                        const response = await fetch('/api/health');
                        const status = await response.json();

                        statusDiv.innerHTML = `
                            <div class="stats">
                                <div class="stat-card">
                                    <div class="stat-value">${status.api_stats.requests_total}</div>
                                    <div>Requêtes API</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${status.api_stats.transmissions_total}</div>
                                    <div>Transmissions</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${status.system.status === 'operational' ? '✅' : '❌'}</div>
                                    <div>État système</div>
                                </div>
                            </div>
                            <pre>${JSON.stringify(status, null, 2)}</pre>
                        `;
                    } catch (error) {
                        statusDiv.innerHTML = `<div class="status error">❌ Erreur: ${error.message}</div>`;
                    }
                }

                async function runDemo() {
                    const demoDiv = document.getElementById('demoResults');

                    try {
                        const response = await fetch('/api/demo');
                        const demo = await response.json();

                        demoDiv.innerHTML = `
                            <h3>Exemples de transmission:</h3>
                            <pre>${JSON.stringify(demo, null, 2)}</pre>
                        `;
                    } catch (error) {
                        demoDiv.innerHTML = `<div class="status error">❌ Erreur: ${error.message}</div>`;
                    }
                }

                // Gestionnaire de formulaire
                document.getElementById('uploadForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    uploadFile();
                });

                // Chargement initial
                window.addEventListener('load', checkStatus);
            </script>
        </body>
        </html>
        """
        return html

    async def run_server(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Lancer le serveur API

        Args:
            host: Adresse d'écoute
            port: Port d'écoute
        """
        app = self.create_app()

        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="info",
            reload=False
        )

        server = uvicorn.Server(config)
        await server.serve()


# Fonction utilitaire pour démarrage rapide
def run_api_server(host: str = "0.0.0.0", port: int = 8000, config: Optional[Dict[str, Any]] = None):
    """
    Démarrer le serveur API

    Args:
        host: Adresse d'écoute
        port: Port d'écoute
        config: Configuration du système
    """
    api = DNFMMLMorseAPI(config)

    print(f"🚀 Démarrage du serveur API DNF-MML-Morse sur http://{host}:{port}")
    print(f"📖 Documentation API: http://{host}:{port}/docs")
    print(f"🌐 Interface web: http://{host}:{port}")
    print("Appuyez sur Ctrl+C pour arrêter")

    # Lancement synchrone pour usage en ligne de commande
    import asyncio
    asyncio.run(api.run_server(host, port))
