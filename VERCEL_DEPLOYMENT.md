# Vercel Deployment Guide

## 🚀 Deploy Agent Kit Web Demo to Vercel

This guide shows how to deploy the Agent Kit web demo to Vercel.

### 📋 Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Integration**: Connect your GitHub account to Vercel

### 🛠️ Deployment Steps

#### 1. Push Changes to GitHub
```bash
git add .
git commit -m "Add web demo for Vercel deployment"
git push origin main
```

#### 2. Deploy on Vercel

**Option A: Automatic (Recommended)**
1. Go to [vercel.com](https://vercel.com)
2. Click "Import Project"
3. Select your `ontology-kit` repository
4. Vercel will auto-detect the configuration

**Option B: Manual**
1. Install Vercel CLI: `npm i -g vercel`
2. Login: `vercel login`
3. Deploy: `vercel --prod`

#### 3. Configuration Files Created

- **`package.json`**: Node.js configuration for Vercel
- **`vercel.json`**: Vercel deployment configuration
- **`requirements.txt`**: Python dependencies
- **`web_app.py`**: Streamlit web application

### ⚙️ Configuration Details

#### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "web_app.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "web_app.py"
    }
  ]
}
```

#### package.json
```json
{
  "scripts": {
    "start": "streamlit run web_app.py --server.port $PORT --server.headless true"
  }
}
```

### 🌐 Web Demo Features

The deployed app includes:

1. **🏠 Home**: Project overview and architecture
2. **🔍 Ontology Explorer**: SPARQL query interface (requires ontology files)
3. **📊 Vector Search**: Embedding and semantic search demo
4. **🎯 Leverage Analysis**: Business leverage point visualization
5. **⚙️ Agent Playground**: Interactive agent demos

### 🚨 Limitations

- **File Dependencies**: Ontology files (`assets/`) may not be accessible
- **Resource Limits**: Vercel serverless functions have time/CPU limits
- **API Keys**: Sensitive credentials should use Vercel environment variables

### 🔧 Troubleshooting

#### Still Getting 404?
1. Check Vercel deployment logs
2. Ensure `web_app.py` is in the root directory
3. Verify `vercel.json` configuration

#### Import Errors?
1. Check `requirements.txt` has all dependencies
2. Some ML libraries may exceed Vercel's size limits
3. Consider using lighter alternatives for demo

#### Performance Issues?
1. Vercel serverless functions have cold start delays
2. Large ML models may timeout
3. Consider caching or pre-computed results

### 🔄 Alternative Deployment Options

If Vercel doesn't work well:

- **Streamlit Cloud**: `streamlit run web_app.py`
- **Heroku**: Standard Python deployment
- **Railway**: Modern alternative to Heroku
- **Render**: Free tier available

### 📞 Support

For Vercel-specific issues:
- Check [Vercel Python Docs](https://vercel.com/docs/concepts/functions/serverless-functions/python)
- Review deployment logs in Vercel dashboard
- Test locally: `streamlit run web_app.py`
