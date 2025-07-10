# AIRIES AI Backend

Multi-tenant SaaS platform for creating intelligent voice and web AI agents with comprehensive telephony integration, knowledge base management, and enterprise-grade features.

## 🚀 Features

### Core Platform
- **Multi-tenant SaaS Architecture** - Isolated user environments with role-based access
- **RESTful API** - Comprehensive API with OpenAPI/Swagger documentation
- **Real-time Communication** - WebSocket support for live interactions
- **Scalable Infrastructure** - Microservices architecture with async/await patterns

### AI & Voice Processing
- **Multi-LLM Support** - Groq, OpenAI, DeepInfra integration with intelligent routing
- **Advanced Voice Processing** - Deepgram, Whisper STT with ElevenLabs, Azure TTS
- **Voice Cloning** - Custom voice synthesis and cloning capabilities
- **Real-time Audio Streaming** - Low-latency audio processing and streaming

### Telephony Integration
- **Multi-Provider Support** - Twilio, Telnyx, and SIP protocol handling
- **WebRTC Integration** - Browser-based calling capabilities
- **Call Management** - Recording, transcription, and speaker diarization
- **DTMF & IVR** - Interactive voice response and touch-tone detection

### Knowledge Management
- **Enterprise RAG** - Advanced retrieval-augmented generation pipeline
- **Multi-format Support** - PDF, DOCX, TXT, CSV document processing
- **Web Scraping** - Automated content extraction with Puppeteer
- **Vector Search** - ChromaDB integration for semantic search
- **Knowledge Versioning** - Automatic updates and version control

### Billing & Usage
- **Credit-based System** - Granular usage tracking and billing
- **Multi-tier Pricing** - Free, Pro, and Enterprise tiers
- **Payment Integration** - Stripe and Paystack support
- **Usage Analytics** - Detailed usage reports and cost optimization

## 🏗️ Architecture

### Technology Stack
- **Backend Framework**: FastAPI with async/await
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Vector Database**: ChromaDB for embeddings
- **Cache**: Redis for session management
- **Authentication**: JWT with refresh tokens
- **File Storage**: Supabase Storage
- **Containerization**: Docker with multi-stage builds

### Project Structure
```
backend/
├── app/
│   ├── api/                 # API routes and endpoints
│   │   └── v1/
│   │       ├── endpoints/   # Individual endpoint modules
│   │       └── api.py       # Main API router
│   ├── core/                # Core functionality
│   │   ├── config.py        # Configuration management
│   │   ├── database.py      # Database setup
│   │   └── security.py      # Security utilities
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py          # User model
│   │   ├── agent.py         # Agent model
│   │   ├── conversation.py  # Conversation model
│   │   ├── usage.py         # Usage tracking models
│   │   └── knowledge.py     # Knowledge base models
│   ├── schemas/             # Pydantic schemas
│   │   ├── user.py          # User schemas
│   │   └── ...              # Other schemas
│   ├── services/            # Business logic
│   │   ├── user_service.py  # User operations
│   │   ├── agent_service.py # Agent operations
│   │   └── ...              # Other services
│   └── main.py              # FastAPI application
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Multi-service setup
└── .env.example            # Environment variables template
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+

### Local Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd airies-ai/backend
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Start services with Docker Compose**
```bash
docker-compose up -d db redis chromadb
```

5. **Run database migrations**
```bash
python -m alembic upgrade head
```

6. **Start the development server**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

1. **Build and start all services**
```bash
docker-compose up -d
```

2. **View logs**
```bash
docker-compose logs -f api
```

3. **Stop services**
```bash
docker-compose down
```

## 📚 API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## 🔧 Configuration

### Environment Variables

Key configuration options (see `.env.example` for complete list):

```bash
# Application
DEBUG=false
SECRET_KEY="your-secret-key"

# Database
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/airies_ai"

# LLM Providers
OPENAI_API_KEY="sk-..."
GROQ_API_KEY="gsk_..."
DEEPINFRA_API_KEY="..."

# Voice Services
DEEPGRAM_API_KEY="..."
ELEVENLABS_API_KEY="..."

# Telephony
TWILIO_ACCOUNT_SID="..."
TWILIO_AUTH_TOKEN="..."
```

### Database Configuration

The application uses PostgreSQL with async SQLAlchemy. Key models:

- **Users**: Authentication, billing, and account management
- **Agents**: AI agent configurations and settings
- **Conversations**: Call records and interaction history
- **Usage**: Billing and usage tracking
- **Knowledge**: Document storage and RAG pipeline

## 🔐 Security

### Authentication
- JWT tokens with refresh token rotation
- Password hashing with bcrypt
- Account lockout after failed attempts
- Email verification and password reset

### Authorization
- Role-based access control
- API key authentication for external integrations
- Rate limiting and request throttling
- CORS configuration for web clients

### Data Protection
- Row-level security policies
- Encrypted sensitive data storage
- GDPR and CCPA compliance features
- Audit logging for security events

## 📊 Monitoring & Analytics

### Health Checks
- Application health endpoint: `/health`
- Database connectivity checks
- External service availability monitoring

### Logging
- Structured JSON logging
- Request/response logging
- Error tracking and alerting
- Performance metrics collection

### Metrics (Optional)
- Prometheus metrics collection
- Grafana dashboards
- Usage analytics and reporting
- Performance monitoring

## 🧪 Testing

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

### Test Structure
```
tests/
├── conftest.py              # Test configuration
├── test_auth.py             # Authentication tests
├── test_agents.py           # Agent functionality tests
├── test_conversations.py    # Conversation tests
└── integration/             # Integration tests
```

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
```bash
# Set production environment variables
export DEBUG=false
export DATABASE_URL="postgresql+asyncpg://..."
# ... other production configs
```

2. **Database Migration**
```bash
python -m alembic upgrade head
```

3. **Start with Gunicorn**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Google Cloud Deployment

1. **Build and push Docker image**
```bash
docker build -t gcr.io/PROJECT_ID/airies-ai-backend .
docker push gcr.io/PROJECT_ID/airies-ai-backend
```

2. **Deploy to Cloud Run**
```bash
gcloud run deploy airies-ai-backend \
  --image gcr.io/PROJECT_ID/airies-ai-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive tests
- Update documentation for new features
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.airies.ai](https://docs.airies.ai)
- **Issues**: [GitHub Issues](https://github.com/airies-ai/backend/issues)
- **Email**: support@airies.ai
- **Discord**: [AIRIES AI Community](https://discord.gg/airies-ai)

## 🗺️ Roadmap

### Phase 1 (Current)
- [x] Core API infrastructure
- [x] User authentication and management
- [x] Basic agent configuration
- [x] Database models and migrations
- [ ] Voice processing integration
- [ ] Telephony provider setup

### Phase 2 (Next)
- [ ] Knowledge base and RAG pipeline
- [ ] Advanced agent features
- [ ] Usage tracking and billing
- [ ] Web scraping automation
- [ ] Performance optimization

### Phase 3 (Future)
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Custom tool framework
- [ ] Enterprise features
- [ ] Mobile API support

---

Built with ❤️ by the AIRIES AI Team