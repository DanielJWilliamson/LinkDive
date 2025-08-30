# Link Dive AI - SEO Backlink Analysis Platform

A comprehensive SEO analysis tool that aggregates backlink data from multiple premium sources (Ahrefs and DataForSEO APIs) to provide actionable insights for link building and competitor analysis.

## ✨ Features

- **Multi-API Integration**: Combines Ahrefs and DataForSEO data for comprehensive analysis
- **Backlink Analysis**: Deep dive into domain backlink profiles and quality metrics
- **Competitor Intelligence**: Gap analysis and link building opportunities
- **Risk Assessment**: Identify potentially toxic or harmful backlinks
- **Real-time Analysis**: Fast, async processing with intelligent caching
- **Interactive API**: Auto-generated documentation with live testing interface

## 🚀 Technology Stack

- **Backend**: FastAPI (Python) - Modern, high-performance async web framework
- **Frontend**: React 18 with TypeScript *(coming next)*
- **Database**: PostgreSQL with Redis caching *(planned)*
- **APIs**: Ahrefs API, DataForSEO API - Premium SEO data sources
- **Documentation**: Auto-generated interactive API docs

## 🏗️ Project Structure

```
LinkDive/
├── src/
│   └── backend/                 # FastAPI Backend Application
│       ├── app/
│       │   ├── api/
│       │   │   └── v1/
│       │   │       └── endpoints/  # API endpoint definitions
│       │   │           ├── health.py
│       │   │           ├── backlinks.py
│       │   │           └── analysis.py
│       │   ├── models/             # Pydantic data models
│       │   │   ├── backlink.py
│       │   │   └── analysis.py
│       │   ├── services/           # Business logic & API clients
│       │   │   ├── base_api.py
│       │   │   ├── ahrefs_client.py
│       │   │   ├── dataforseo_client.py
│       │   │   └── link_analysis_service.py
│       │   └── main.py            # FastAPI application entry point
│       ├── config/
│       │   └── settings.py        # Environment configuration
│       ├── requirements.txt       # Python dependencies
│       ├── .env.example          # Environment variables template
│       └── run_dev.py            # Development server launcher
├── Markdowns/                    # Project documentation
├── TaskOverview/                 # Project specifications
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation & Setup

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd LinkDive/src/backend
   ```

2. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn structlog httpx pydantic-settings
   ```

3. **Start the development server:**
   ```bash
   python run_dev.py
   ```

   The server will start at: **http://127.0.0.1:8000**

### 📖 API Documentation

Once the server is running, explore the interactive documentation:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 🔗 Available API Endpoints

### Health & Monitoring
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed system health with metrics

### Backlink Analysis
- `POST /api/v1/backlinks/analyze` - Comprehensive backlink analysis for any URL
- `GET /api/v1/backlinks/domain/{domain}/metrics` - Domain SEO metrics and authority
- `POST /api/v1/backlinks/competitor-analysis` - Compare backlink profiles with competitors
- `GET /api/v1/backlinks/{domain}/risks` - Identify toxic and harmful backlinks

### SEO Intelligence
- `POST /api/v1/analysis/domain` - Complete domain SEO analysis
- `POST /api/v1/analysis/quality-score` - Link quality assessment
- `GET /api/v1/analysis/recommendations/{domain}` - Actionable SEO recommendations

## 🖼️ Screenshots

### Frontend - Login Page
![LinkDive Login](docs/images/linkdive-login-page.png)

*Secure authentication with Google OAuth. For testing purposes, you can use "admin" as the email to bypass domain restrictions.*

### Backend - API Documentation
![LinkDive API Documentation](docs/images/linkdive-api-docs.png)

*Comprehensive FastAPI documentation with interactive testing interface available at http://localhost:8000/docs*

## 🔐 Authentication

The application uses NextAuth.js with Google OAuth for secure authentication. Access is restricted to:

- **Production**: `@linkdive.ai` email addresses only
- **Testing/Development**: Use `"admin"` as the email for backdoor access (no actual Google account needed)

This backdoor allows developers and testers to quickly access the application without needing a specific domain email.

## 🧪 Testing the API

### Example: Check Domain Metrics
```bash
curl http://127.0.0.1:8000/api/v1/backlinks/domain/example.com/metrics
```

### Example: Analyze Backlinks
```bash
curl -X POST http://127.0.0.1:8000/api/v1/backlinks/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://example.com",
    "mode": "domain",
    "limit": 100
  }'
```

### Example: Competitor Analysis
```bash
curl -X POST http://127.0.0.1:8000/api/v1/backlinks/competitor-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "target_domain": "yoursite.com",
    "competitor_domains": ["competitor1.com", "competitor2.com"],
    "analysis_depth": "standard"
  }'
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# API Keys (optional for development - uses mock data)
AHREFS_API_KEY=your-ahrefs-api-key
DATAFORSEO_USERNAME=your-dataforseo-username
DATAFORSEO_PASSWORD=your-dataforseo-password

# Database (for production)
DATABASE_URL=postgresql://user:password@localhost:5432/linkdive_db

# Redis Cache (for production)
REDIS_URL=redis://localhost:6379/0
```

## 🛠️ Development Features

- **Mock Data**: Fully functional with development data (no API keys required)
- **Auto-reload**: Development server automatically reloads on code changes
- **Type Safety**: Full Pydantic model validation throughout
- **Async Support**: High-performance async/await implementation
- **Rate Limiting**: Built-in API rate limiting and error handling
- **Structured Logging**: JSON-formatted logs for production monitoring

## 🚧 Current Status

### ✅ Completed
- **Backend Foundation**: Complete FastAPI application
- **API Integration**: Ahrefs and DataForSEO client implementations
- **Service Architecture**: Clean separation of concerns
- **Data Models**: Comprehensive Pydantic models
- **Mock Implementation**: Full functionality for development

### 🔄 Next Steps
- **Frontend Development**: React TypeScript dashboard
- **Database Integration**: PostgreSQL with SQLAlchemy
- **Real API Integration**: Production API key configuration
- **Authentication**: User management and API security
- **Caching**: Redis integration for performance

## 🏆 Technical Achievements

- **Service Integration**: Intelligent aggregation of multiple SEO data sources
- **API Design**: RESTful endpoints with comprehensive OpenAPI documentation  
- **Error Handling**: Robust exception management and rate limiting
- **Performance**: Async processing with built-in caching strategy
- **Code Quality**: Type-safe implementation with Pydantic models
- **Developer Experience**: Auto-reload, structured logging, interactive docs

## 📞 Contact & Support

**Project**: LinkDive - SEO Backlink Analysis Platform  
**Contact**: tools@linkdive.ai  
**Company**: [LinkDive](http://linkdive.ai)

---

*Built with ❤️ as a comprehensive SEO analysis platform. This demonstrates a production-ready FastAPI backend with comprehensive SEO analysis capabilities.*
