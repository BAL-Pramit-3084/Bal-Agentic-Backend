# Changelog

All notable changes to the Balasore Alloys Dashboard System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] - 2025-12-01

### Added

- Docker containerization support (`Dockerfile`, `docker-compose.yml`)
- Production lifecycle management files
- Centralized logging system with file rotation
- Deployment scripts for easy updates
- Health monitoring capabilities

### Changed

- **BREAKING**: Reorganized department modules into `departments/` folder
  - `furnace_formatter.py` → `departments/furnace/formatter.py`
  - `qc_formatter.py` → `departments/qc/formatter.py`
  - `scm_formatter.py` → `departments/scm/formatter.py`
  - `crm_formatter.py` → `departments/crm/formatter.py`
- Updated all import paths to use new department structure
- Template paths now correctly resolve from project root

### Removed

- God's Eye project (discarded by management)
  - Removed `routes/god_eye_routes.py`
  - Removed `frontend/god_eye/`
  - Removed `static/js/god_eye.js`
- Legacy/unused files:
  - `app_flask.py` (old Gemini version)
  - `dashboards/dashboard_api.py` (old standalone API)
  - `dashboards/dashboard_definitions.py` (old HR queries)
  - `dashboards/kpi_formats_master.py` (old EAV config)
  - `dashboards/data_processor_eav.py` (broken EAV processor)
  - `data_formatters/formatter_env.py` (old ENV formatter)
  - `chat/chatbot_api.py`, `chat/schema_manager.py` (empty files)
  - `auth/intranet_adapter.py`, `auth/user_auth_service.py` (empty files)
  - `check_html.py` (debug script)

### Deprecated

- ENV department (old EAV format) - disabled, needs reimplementation

### Fixed

- Template path resolution in all department template engines

---

## [2.0.0] - 2025-11-28

### Added

- CRM/Sales & Distribution dashboard
- SCM (Supply Chain Management) dashboard
- QC (Quality Control) dashboard
- Furnace Operations dashboard
- Claude AI-powered insights for all departments
- JWT authentication system
- Activity logging and audit trail
- Admin panel for user management

### Changed

- Migrated from Gemini to Claude API
- Switched from EAV to normalized table format for new departments

---

## [1.0.0] - 2025-11-01

### Added

- Initial release
- Environment department dashboard (EAV format)
- Basic Flask API
- Gemini AI integration
