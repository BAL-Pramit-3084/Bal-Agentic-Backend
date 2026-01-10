# Balasore Alloys Dashboard System

A modular, AI-powered dashboard system for manufacturing operations across multiple departments.

## 🏢 Departments

- **Furnace Operations** - FeCr production monitoring and efficiency tracking
- **Geology & Mines** - Ore excavation, quality analysis, and planning
- **Quality Control** - Testing, compliance, and quality metrics
- **Supply Chain** - Inventory, logistics, and procurement
- **Automobile** - Fleet management and maintenance
- **CRM** - Customer relationship and order management
- **Environment** - Compliance, emissions, and sustainability

## 🚀 Features

- **Real-time Dashboards** - Live production data visualization
- **Date Range Analysis** - Historical trends and comparisons
- **AI Insights** - LLM-powered analysis and recommendations
- **Multi-department** - Isolated, modular architecture
- **RESTful API** - Easy integration with external systems
- **JWT Authentication** - Secure access control
- **Responsive UI** - Works on desktop, tablet, and mobile

## 📋 Tech Stack

- **Backend**: Python 3.12, Flask
- **Database**: MySQL (via MCP Server)
- **AI/ML**: OpenAI API (Claude/Local LLM)
- **Frontend**: HTML5, JavaScript, Chart.js
- **Auth**: JWT tokens
- **Deployment**: Docker, PM2

## 🏗️ Project Structure

```
MCP-with-API/
├── app_main.py                 # Main application entry point
├── config_modules/             # Configuration management
├── core/                       # Core utilities (MCP, database)
├── departments/                # Department-specific code
│   ├── furnace/               # Furnace department
│   │   ├── formatter.py       # Data processing
│   │   ├── template_engine.py # HTML generation
│   │   └── claude_analyzer.py # AI insights
│   ├── geology/               # Geology department
│   ├── qc/                    # QC department
│   ├── scm/                   # SCM department
│   ├── automobile/            # Automobile department
│   ├── crm/                   # CRM department
│   └── env/                   # Environment department
├── templates/                  # HTML templates
├── static/                     # CSS, JS, images
├── auth/                       # Authentication
├── routes/                     # API routes
├── dashboards/                 # Department configuration
└── docs/                       # Documentation

```

## 🔧 Installation

### Prerequisites

- Python 3.12+
- MySQL database
- Git

### Setup

```bash
# Clone repository
git clone <repository-url>
cd MCP-with-API

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
# (Ensure MySQL is running and configured)

# Run application
python app_main.py
```

## 🌿 Git Workflow

### Branch Structure

- `main` - Production-ready code
- `develop` - Integration branch
- `dept/furnace` - Furnace team development
- `dept/geology` - Geology team development
- `dept/qc` - QC team development
- `dept/scm` - SCM team development
- `dept/automobile` - Automobile team development
- `dept/crm` - CRM team development
- `dept/env` - Environment team development

### For Department Developers

```bash
# Checkout your department branch
git checkout dept/furnace

# Pull latest changes
git pull origin develop

# Make changes to your department
# Edit files in: departments/furnace/

# Commit changes
git add departments/furnace/
git commit -m "feat(furnace): add power efficiency chart"

# Push to your branch
git push origin dept/furnace

# Create Pull Request on GitHub
# dept/furnace → develop
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed workflow.

## 📚 Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Git workflow and collaboration guidelines
- **[DEPARTMENT_DEVELOPMENT_GUIDE.md](docs/DEPARTMENT_DEVELOPMENT_GUIDE.md)** - How to develop your department
- **[API Documentation](docs/API.md)** - API endpoints and usage *(coming soon)*
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment *(coming soon)*

## 🧪 Testing

```bash
# Run all tests
pytest

# Run department-specific tests
pytest tests/test_furnace.py -v

# Generate test dashboard
python app_main.py furnace 2025-12-24

# Check generated output
ls generated_dashboards/
```

## 📡 API Endpoints

### Health Check
```http
GET /health
```

### Department Dashboards
```http
GET /api/v1/dashboard/furnace?date=2025-12-24
GET /api/v1/dashboard/geology?start_date=2025-12-10&end_date=2025-12-24
```

### Department List
```http
GET /api/v1/departments
```

### Authentication
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user",
  "password": "pass"
}
```

See full API documentation in [docs/API.md](docs/API.md).

## 🔐 Security

- JWT token-based authentication
- Environment variable configuration
- SQL injection prevention (parameterized queries)
- CORS configuration
- Rate limiting *(coming soon)*

**Important**: Never commit `.env` file or credentials to Git.

## 🐛 Troubleshooting

### Common Issues

**Import Error**
```python
ImportError: cannot import name 'FurnaceDataProcessor'
```
→ Check class name matches filename in `departments/furnace/formatter.py`

**Template Not Found**
```
FileNotFoundError: templates/furnace_dashboard.html
```
→ Ensure template exists and path is relative to project root

**Database Connection Error**
```
Error: Can't connect to MySQL server
```
→ Check `.env` file has correct database credentials
→ Ensure MySQL service is running

**Unicode Encoding Error (Windows)**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```
→ Already handled in code with fallback to ASCII

## 🤝 Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Department Ownership

| Department | Lead | Branch |
|------------|------|--------|
| Furnace | @furnace-lead | `dept/furnace` |
| Geology | @geology-lead | `dept/geology` |
| QC | @qc-lead | `dept/qc` |
| SCM | @scm-lead | `dept/scm` |
| Automobile | @automobile-lead | `dept/automobile` |
| CRM | @crm-lead | `dept/crm` |
| Environment | @env-lead | `dept/env` |

## 📞 Support

- **Issues**: Create GitHub issue with appropriate label
- **Questions**: Tag department lead or tech lead
- **Urgent**: Contact tech lead directly

## 📄 License

Proprietary - Balasore Alloys Limited

## 👥 Team

- **Tech Lead**: [@tech-lead](https://github.com/tech-lead)
- **Furnace Lead**: [@furnace-lead](https://github.com/furnace-lead)
- **Geology Lead**: [@geology-lead](https://github.com/geology-lead)
- **QC Lead**: [@qc-lead](https://github.com/qc-lead)
- **SCM Lead**: [@scm-lead](https://github.com/scm-lead)
- **Automobile Lead**: [@automobile-lead](https://github.com/automobile-lead)
- **CRM Lead**: [@crm-lead](https://github.com/crm-lead)
- **Environment Lead**: [@env-lead](https://github.com/env-lead)

---

**Built with ❤️ by Balasore Alloys IT Team**
