# LinkDive AI - Digital PR Campaign Monitoring Platform

> Quick start (Windows, PowerShell)

- Backend: start API on http://127.0.0.1:8000

```powershell
cd c:\source\TestInts\Kaizen\KaizenTest\src\backend
./start_server.bat
```

- Frontend: start on http://localhost:3000

```powershell
cd c:\source\TestInts\Kaizen\KaizenTest\src\frontend
npm install --no-audit --no-fund
npm run dev
```


**Automatically discover and monitor all potential online media coverage of your Digital PR campaigns.**

LinkDive AI is an intelligent campaign monitoring tool that helps PR agencies and digital marketers track the success of their campaigns by automatically discovering when their content has been mentioned, linked to, or covered across the web. The platform combines multiple data sources and AI-powered content verification to provide comprehensive coverage reporting.

## 🎯 What LinkDive Does

### For PR Agencies & Digital Marketers
- **Campaign Setup**: Create monitoring campaigns with target URLs, keywords, and verification parameters
- **Automatic Discovery**: AI continuously scans the web for potential coverage of your campaigns
- **Content Verification**: Smart keyword matching and content analysis to verify actual coverage
- **Coverage Reporting**: Export verified coverage for client reports and status updates

### The Campaign Process
1. **Create Campaign**: Set up monitoring for a specific PR campaign with target URLs and keywords
2. **AI Discovery**: System automatically finds potential coverage using Ahrefs and DataForSEO APIs
3. **Content Verification**: AI analyzes discovered content to verify if it actually covers your campaign  
4. **Report Generation**: Review, select, and export verified coverage for client reporting

### What You Get
- **Verified Coverage**: Direct backlinks to your campaign URLs with full metadata
- **Potential Coverage**: Articles mentioning your campaign that don't link directly
- **SERP Monitoring**: Track how your campaign URLs perform in Google search results
- **Professional Reports**: Export coverage data for client presentations and status reports

## ✨ Key Features

- **Multi-Source Discovery**: Integrates Ahrefs and DataForSEO APIs for comprehensive coverage detection
- **AI Content Verification**: Smart keyword matching to verify actual campaign coverage
- **24/7 Monitoring**: Automated monitoring during business hours (7am-7pm UK time, Mon-Fri)
- **Campaign Management**: Intuitive 3-step campaign creation with keyword and domain configuration
- **Professional Reporting**: Export verified coverage for client reports and presentations
- **Google OAuth Security**: Secure authentication with development access for testing

## 🚀 Technology Stack

- **Backend**: FastAPI (Python) - Modern, high-performance async web framework
- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Database**: SQLite for development, PostgreSQL-ready for production
- **Authentication**: NextAuth.js with Google OAuth and admin backdoor
- **APIs**: Ahrefs API, DataForSEO API - Premium SEO and backlink data sources
- **Monitoring**: Background task processing with intelligent scheduling

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

## 🎯 Campaign Monitoring Value

### Why Use LinkDive for PR Campaigns?

**Problem**: PR agencies spend countless hours manually searching for campaign coverage across the web, often missing mentions and struggling to prove ROI to clients.

**Solution**: LinkDive automatically monitors the entire web for your campaign coverage, providing:

- ⚡ **Time Savings**: Eliminate manual coverage hunting - get automatic discovery
- 📊 **Comprehensive Tracking**: Never miss coverage again with multi-source monitoring  
- 🎯 **Verified Results**: AI distinguishes between actual coverage and false positives
- 📈 **Client Reporting**: Professional coverage reports ready for client presentations
- 🔄 **Continuous Monitoring**: 24/7 discovery during business hours with daily updates

### Campaign Outcomes

Each campaign you create will deliver:

1. **Verified Coverage List**: Direct backlinks to your campaign URLs with metadata
2. **Potential Coverage Discovery**: Articles mentioning your campaign without direct links
3. **SERP Performance**: Track how your URLs rank for target keywords
4. **Professional Reports**: Export-ready coverage data for client deliverables
5. **ROI Demonstration**: Clear metrics showing campaign reach and impact

## 🚀 Current Development Status

✅ **Completed Features:**
- Campaign creation workflow (3-step process)
- User authentication (Google OAuth + admin backdoor)
- Campaign management dashboard
- Database schema and API endpoints
- Professional UI with responsive design

🚧 **In Development:**
- Campaign submission validation fixes
- Ahrefs API integration for verified coverage
- DataForSEO API integration for potential coverage discovery
- Content verification and keyword matching
- SERP monitoring and reporting features

📋 **Planned Features:**
- Automated daily monitoring (7am-7pm UK time)
- Coverage export and client reporting
- Real-time notifications via Slack
- Advanced content analysis with AI
- Campaign performance analytics

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

4. **Start the frontend and open the app:**
  ```bash
  cd ../frontend
  npm install
  npm run dev
  ```

  The frontend runs at: **http://localhost:3000** — open it in your browser to view the campaigns dashboard.

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

*Secure authentication with Google OAuth and development backdoor. Click "Show development access" and enter "admin" for testing.*

### Frontend - Campaign Dashboard
![LinkDive Dashboard](docs/images/campaigns-listed.png)

*Main campaign management dashboard showing empty state with options to create new campaigns. User is authenticated as "Admin User (Development)".*

### Example – Campaigns Listed
The dashboard now shows seeded/example campaigns out of the box when running in mock mode. Here is an example of campaigns listed in the UI:

![Example Campaigns Listed](docs/images/campaigns-listed.png)

Note: When Live mode is enabled and provider credentials don’t have the required scope/subscription, the UI will surface a short explainer in the Data Source Mode card and automatically fall back to Mock.

### Frontend - Campaign Creation Process

#### Step 1: Basic Information
![Campaign Creation Step 1](docs/images/campaign-creation-step1.png)

*Campaign creation form - Step 1: Enter basic campaign details including client name, campaign name, domain, and optional URL and launch date.*

#### Step 2: Keywords Configuration
![Campaign Creation Step 2](docs/images/campaign-creation-step2.png)

*Campaign creation form - Step 2: Configure SERP monitoring keywords and coverage verification keywords for comprehensive tracking.*

#### Step 3: Settings & Summary
![Campaign Creation Step 3](docs/images/campaign-creation-step3.png)

*Campaign creation form - Step 3: Optional domain blacklist configuration and campaign summary review before creation.*

### Backend - API Documentation Overview
![LinkDive API Documentation](docs/images/linkdive-api-docs.png)

*Comprehensive FastAPI documentation with interactive testing interface available at http://localhost:8000/docs*

### Backend - Detailed API Endpoint
![LinkDive API Backlinks Detail](docs/images/linkdive-api-backlinks-detail.png)

*Detailed view of the backlinks analysis endpoint showing request/response schemas, parameters, and example data structures.*

## 🔐 Authentication

The application uses NextAuth.js with multiple authentication providers:

### Production Authentication
- **Google OAuth**: Restricted to `@linkdive.ai` email addresses only
- Secure domain-based access control

### Development/Testing Authentication  
- **Admin Backdoor**: Click "Show development access" on the login page
- Enter `"admin"` in the email field and click "Development Sign In"
- **No Google account required** - bypasses OAuth entirely for testing

This dual authentication system allows:
- ✅ **Secure production access** via Google OAuth with domain restrictions
- ✅ **Easy development testing** without needing domain-specific email accounts
- ✅ **Quick demo access** for showcasing the platform

### Transitional API Authentication (Backend)

The backend currently supports a lightweight header-based override while full OAuth wiring is completed:

- Provide `X-User-Email: user@example.com` on any API request to impersonate that user.
- If the header is omitted, a fallback `demo@linkdive.ai` user is assumed (development & tests) unless strict mode is enabled.
- To require the header (e.g. staging/production hardening), set environment variable:

```bash
ENFORCE_AUTH_HEADERS=1
```

When enabled, requests without `X-User-Email` receive `401 Missing authentication header`.

### Structured Logging with User Context

Each request log line now includes the resolved user (header or fallback) plus a correlation ID:

Example (JSON pretty printed):
```json
{
  "event": "request.end",
  "request_id": "c3f6a9b0-9d3c-4e2a-8c07-6e97e0e7d5b1",
  "method": "GET",
  "path": "/api/campaigns",
  "user": "demo@linkdive.ai",
  "status_code": 200,
  "duration_ms": 12.41
}
```
Use `request_id` for tracing multi-step workflows in logs; supply your own via `X-Request-ID` to propagate across services.

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

For questions, support, or to request a demo, contact:---

*Built with ❤️ as a comprehensive SEO analysis platform. This demonstrates a production-ready FastAPI backend with comprehensive SEO analysis capabilities.*

## ▶️ Run Locally (Windows, PowerShell)

Backend (FastAPI):

1) Create and activate a virtual environment

```powershell
cd c:\source\TestInts\Kaizen\KaizenTest\src\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Start the API server

```powershell
python start_server.py
# or
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

3) Verify health

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -Method GET
```

Frontend (Next.js 15):

```powershell
cd c:\source\TestInts\Kaizen\KaizenTest\src\frontend
npm install --no-audit --no-fund
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000"  # optional; default is 127.0.0.1:8000
npm run dev
```

Open http://localhost:3000 in your browser.

Notes:
- Development auth: the frontend and Axios client send `X-User-Email` automatically (demo identity) for backend routes.
- Mock/Live toggle: On the dashboard, use the “Data Source Mode” card to switch between Mock and Live. If provider credentials are missing scope/subscription, the UI shows an explainer and the system safely falls back to Mock.
- Seeded/example data: A few example campaigns are visible in Mock mode to help you explore the UI quickly.

## 🔐 Pre-public Repo Security Checklist

- Ensure no real secrets are tracked:
  - `.env`, `*.env`, and `TaskOverview/` are ignored by `.gitignore`.
  - Redact/remove any secrets in documentation/spec files before commit.
- Verify no hardcoded tokens/passwords exist in source files (scan passed in this repo; examples remain placeholders only).
- Confirm CORS is restricted to local dev by default (production origins must be set via env).
- Keep provider credentials only in local `.env` files; do not commit them.
