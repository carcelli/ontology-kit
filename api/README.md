# Agent Kit API for Vercel

This directory contains lightweight API endpoints designed to run on Vercel's serverless platform.

## 🎯 Why a Separate API?

The main Agent Kit project has heavy ML dependencies (~2GB) that **exceed Vercel's 50MB Lambda limit**:
- PyTorch (~800MB)
- Transformers (~400MB)  
- Sentence Transformers (~300MB)
- FAISS, MLflow, Streamlit, etc.

This API provides a minimal subset for demonstration purposes.

## 📡 Endpoints

### `GET /`
Landing page with API documentation.

### `GET /api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "ontology-kit-api",
  "message": "Agent Kit API is running"
}
```

### `GET /api/ontology`
Query ontology metadata.

**Response:**
```json
{
  "status": "success",
  "ontologies_found": 5,
  "ontologies": [
    {
      "name": "core",
      "path": "assets/ontologies/core.ttl",
      "size": 4532
    }
  ],
  "note": "Full ontology querying requires local setup"
}
```

## 🚀 Local Testing

```bash
# Install Vercel CLI
npm i -g vercel

# Run locally
vercel dev

# Test endpoints
curl http://localhost:3000/api/health
curl http://localhost:3000/api/ontology
```

## 📦 Dependencies

See `api/requirements.txt` for the minimal dependency list (kept under 50MB):
- `rdflib` - Ontology parsing (lightweight)
- `pydantic` - Data validation
- `python-dotenv` - Environment variables

## 🔗 Full Features

For complete Agent Kit functionality:
- **Local Setup**: Clone repo and run `./QUICKSTART.sh`
- **Streamlit Demo**: Run `streamlit run web_app.py`
- **Jupyter Notebooks**: See `examples/` directory

## 🌐 Deployment

This API automatically deploys when you push to GitHub (if connected to Vercel):

```bash
git add .
git commit -m "Update API"
git push origin main
```

Or manually:
```bash
vercel --prod
```

## ⚠️ Platform Recommendation

**For production ML workloads**, use platforms that support larger deployments:
- **Streamlit Cloud** - Best for Streamlit apps
- **Railway** - Full Python support, larger limits
- **Render** - Free tier with reasonable limits
- **AWS Lambda** - If you configure custom layers
- **Google Cloud Run** - Container-based deployment


