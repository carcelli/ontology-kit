"""
Main API endpoint for Ontology Kit on Vercel.
Lightweight version without heavy ML dependencies.
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Agent Kit - Ontology-Driven ML</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    line-height: 1.6;
                }
                h1 { color: #2563eb; }
                .card {
                    background: #f8fafc;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }
                .endpoint {
                    background: #1e293b;
                    color: #e2e8f0;
                    padding: 10px;
                    border-radius: 4px;
                    font-family: monospace;
                    margin: 10px 0;
                }
                a { color: #2563eb; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>🤖 Agent Kit API</h1>
            <p><strong>Ontology-Driven ML Framework for Small Businesses</strong></p>
            
            <div class="card">
                <h2>📡 Available Endpoints</h2>
                <div class="endpoint">GET /api/health</div>
                <p>Health check endpoint</p>
                
                <div class="endpoint">GET /api/ontology</div>
                <p>Query ontology metadata</p>
            </div>
            
            <div class="card">
                <h2>🚀 Full Features</h2>
                <p>For the complete Agent Kit experience with ML models, vector search, and interactive demos:</p>
                <ul>
                    <li><strong>Local Setup:</strong> <code>git clone</code> and run <code>./QUICKSTART.sh</code></li>
                    <li><strong>Streamlit Demo:</strong> <code>streamlit run web_app.py</code></li>
                    <li><strong>Documentation:</strong> See <a href="https://github.com/your-repo">GitHub</a></li>
                </ul>
            </div>
            
            <div class="card">
                <h2>⚠️ Deployment Note</h2>
                <p>This is a lightweight API version for Vercel. Heavy ML dependencies (PyTorch, Transformers) 
                are not supported on Vercel's serverless platform.</p>
                <p><strong>Recommended:</strong> Deploy full app on Streamlit Cloud, Railway, or Render.</p>
            </div>
        </body>
        </html>
        """

        self.wfile.write(html.encode())
        return


