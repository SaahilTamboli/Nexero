# 🏠 Nexero VR Backend

Backend API for VR real estate behavioral analytics platform. Receives tracking data from Unreal Engine VR tours and processes it for AI-powered sales insights.

## 📋 Overview

**Nexero** is a VR real estate platform that tracks customer behavior during virtual property tours to generate actionable sales insights for builders and sales teams.

### Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Unreal Engine  │─────▶│  FastAPI Backend │─────▶│    Supabase     │
│   VR Client     │ HTTP │   (This Repo)    │      │   PostgreSQL    │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  AI/ML Pipeline │
                         │    Analytics    │
                         └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │    Dashboard    │
                         │  (Sales Team)   │
                         └─────────────────┘
```

### Current Workflow (MVP)

1. **Sales person** starts VR session from dashboard
2. **Customer** experiences property tour in VR (Unreal Engine)
3. **Unreal** collects behavioral data locally during tour
4. **Session ends** → Unreal sends all tracking data in batch to backend
5. **Backend** validates, processes, and stores data in Supabase
6. **AI/ML** analyzes data to generate insights
7. **Dashboard** displays insights to sales team and builders

## 🚀 Features

- ✅ **Session Management** - Track VR tour sessions (start/end times, duration)
- ✅ **Tracking Events** - Store gaze, zone transitions, interactions
- ✅ **Batch Processing** - Efficient bulk event ingestion
- ✅ **Data Validation** - Pydantic models ensure data integrity
- ✅ **Health Monitoring** - Health check endpoints for uptime monitoring
- ✅ **API Documentation** - Auto-generated Swagger/OpenAPI docs

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation and settings management
- **Supabase** - PostgreSQL database with real-time capabilities
- **Uvicorn** - Lightning-fast ASGI server
- **Python 3.9+** - Async/await support

## 📁 Project Structure

```
nexero-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── unreal.py          # Unreal Engine API endpoints
│   ├── core/
│   │   └── database.py            # Supabase database wrapper
│   ├── models/
│   │   └── unreal.py              # Pydantic models for validation
│   ├── services/
│   │   ├── session_service.py     # Session business logic
│   │   └── tracking_service.py    # Tracking event logic
│   ├── config.py                  # Configuration & settings
│   └── main.py                    # FastAPI application entry point
├── .env                           # Environment variables (not in git)
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🔧 Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Supabase account (free tier available)

### Setup Steps

1. **Clone the repository**
   ```powershell
   cd nexero-backend
   ```

2. **Create virtual environment**
   ```powershell
   python -m venv venv
   ```

3. **Activate virtual environment**
   ```powershell
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   
   # Windows CMD
   venv\Scripts\activate.bat
   
   # Mac/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   
   Create `.env` file in the root directory:
   ```env
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-service-role-key-here
   
   # Application Settings
   ENVIRONMENT=development
   LOG_LEVEL=info
   CORS_ORIGINS=["*"]
   API_VERSION=v1
   ```
   
   **Get Supabase credentials:**
   - Go to [Supabase Dashboard](https://supabase.com/dashboard)
   - Select your project
   - Navigate to **Settings** → **API**
   - Copy **Project URL** and **service_role key** (⚠️ keep secret!)

6. **Run the application**
   ```powershell
   # Option 1: Direct Python execution
   python app/main.py
   
   # Option 2: Using uvicorn
   uvicorn app.main:app --reload
   ```

7. **Verify it's running**
   
   Open your browser and visit:
   - **API Root**: http://localhost:8000
   - **Interactive Docs**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

## 📡 API Endpoints

### Root & Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information and available endpoints |
| GET | `/health` | Health check with database status |
| GET | `/docs` | Interactive API documentation (Swagger UI) |

### Unreal Engine Integration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/unreal/session` | Receive session start/end data |
| POST | `/api/v1/unreal/tracking/event` | Single tracking event (legacy) |
| POST | `/api/v1/unreal/tracking/batch` | Batch tracking events (⭐ preferred) |
| GET | `/api/v1/unreal/session/{id}/status` | Check session status |
| POST | `/api/v1/unreal/session/{id}/heartbeat` | Keep session alive |

## 📝 API Usage Examples

### Start Session (Legacy Format)

```bash
curl -X POST "http://localhost:8000/api/v1/unreal/session" \
  -H "Content-Type: application/json" \
  -d '{
    "session_start": "1727653800",
    "session_end": "1727654100",
    "customer_id": "cust_12345",
    "property_id": "prop_67890"
  }'
```

### Send Tracking Events Batch (Preferred)

```bash
curl -X POST "http://localhost:8000/api/v1/unreal/tracking/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_abc123",
    "sent_at": 1727654100.500,
    "events": [
      {
        "event_type": "gaze",
        "timestamp": 1727653850.125,
        "zone_name": "kitchen",
        "gaze_target": "granite_countertop",
        "dwell_time_ms": 2500
      },
      {
        "event_type": "zone_enter",
        "timestamp": 1727653855.450,
        "zone_name": "master_bedroom",
        "position": {"x": 10.5, "y": 2.0, "z": -5.3}
      }
    ]
  }'
```

### Check Session Status

```bash
curl -X GET "http://localhost:8000/api/v1/unreal/session/session_abc123/status"
```

## 🗄️ Database Schema

### Tables

**vr_sessions**
- `id` (UUID, primary key)
- `started_at` (timestamp)
- `ended_at` (timestamp, nullable)
- `duration_seconds` (integer, nullable)
- `status` (text: "active" | "completed")
- `customer_id` (text, nullable)
- `property_id` (text, nullable)

**tracking_events**
- `id` (UUID, primary key)
- `session_id` (UUID, foreign key)
- `event_type` (text: "gaze" | "zone_enter" | "zone_exit" | "interaction")
- `timestamp` (timestamp)
- `zone_name` (text, nullable)
- `object_name` (text, nullable)
- `position` (jsonb, nullable)
- `rotation` (jsonb, nullable)
- `gaze_target` (text, nullable)
- `dwell_time_ms` (integer, nullable)
- `interaction_type` (text, nullable)
- `metadata` (jsonb)

## 🧪 Testing

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_session_service.py

# Run with verbose output
pytest -v
```

## 📊 Monitoring

### Health Check

The `/health` endpoint provides:
- Application status
- Database connectivity
- Current timestamp
- Environment info

Use this endpoint for:
- Load balancer health checks
- Uptime monitoring (UptimeRobot, Pingdom, etc.)
- CI/CD pipeline validation

## 🔐 Security

- ⚠️ **Never commit `.env` files** - Contains sensitive credentials
- 🔒 Use **service_role key** for backend (not anon key)
- 🌐 Restrict **CORS origins** in production
- 🛡️ Enable **rate limiting** for production deployments
- 📝 Review **Supabase Row Level Security (RLS)** policies

## 🚀 Deployment

### Production Checklist

- [ ] Update `ENVIRONMENT=production` in `.env`
- [ ] Restrict `CORS_ORIGINS` to your frontend domain
- [ ] Use strong Supabase service role key
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up logging aggregation (e.g., Sentry, LogDNA)
- [ ] Configure monitoring and alerts
- [ ] Set up automated backups for Supabase
- [ ] Review and optimize database indexes
- [ ] Enable rate limiting middleware
- [ ] Set `reload=False` in uvicorn for production

### Deployment Platforms

- **Railway** - Easy Python deployment
- **Render** - Free tier available
- **Fly.io** - Global edge deployment
- **AWS EC2** - Full control
- **Google Cloud Run** - Serverless containers
- **Azure App Service** - Enterprise ready

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Ensure tests pass: `pytest`
5. Submit pull request

## 📄 License

[Add your license here]

## 👥 Team

Built by the Nexero team for revolutionizing real estate sales with VR analytics.

## 📞 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Contact: [your-email@example.com]

---

**Made with ❤️ for the future of real estate**
