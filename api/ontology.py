"""
Lightweight ontology metadata API endpoint.
"""
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        # Check for ontology files
        ontology_path = Path(__file__).parent.parent / "assets" / "ontologies"
        ontologies = []

        if ontology_path.exists():
            for ttl_file in ontology_path.glob("*.ttl"):
                ontologies.append({
                    "name": ttl_file.stem,
                    "path": str(ttl_file.relative_to(Path(__file__).parent.parent)),
                    "size": ttl_file.stat().st_size
                })

        response = {
            "status": "success",
            "ontologies_found": len(ontologies),
            "ontologies": ontologies,
            "note": "Full ontology querying requires local setup with RDFLib"
        }

        self.wfile.write(json.dumps(response, indent=2).encode())
        return


