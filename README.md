# Social Video Explorer

A platform for exploring and analyzing video content from social media platforms.

**Current Status**: Basic skeleton with mock demonstration mode and Meta provider stub. Future releases will add real multi-platform integration.

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- pip or uv package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd social-video-explorer
```

2. Create and activate a virtual environment:
```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using uv (faster)
uv venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
# Using pip
pip install -r requirements.txt

# Or using uv
uv pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run ui/streamlit_app.py
```

The application will open in your web browser at `http://localhost:8501`

## 📋 Features

### Current Implementation (v0.1.0)
- **Mock Mode**: Demo mode with realistic sample data for testing and demonstrations
- **Meta Provider Stub**: Placeholder for future Facebook/Instagram integration
- **Provider Framework**: Extensible architecture for adding new video platforms
- **Normalized Results**: Consistent data format across all providers
- **Simple UI**: Clean, responsive interface built with Streamlit
- **Configuration Management**: Secure credential handling via environment variables

### Planned Features (Future Releases)
- **Real API Integration**: Full Meta (Facebook/Instagram), YouTube, and TikTok providers
- **Advanced Search**: Filters, pagination, and multi-provider orchestration
- **Export Functionality**: JSON export of search results
- **Caching System**: Intelligent API response caching
- **Enhanced UI**: Rich media cards, detailed views, and analytics

## 🔧 Configuration

### Basic Setup (Mock Mode)

The application works out-of-the-box in mock mode, generating sample video data for demonstration.

### Real API Integration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API credentials:
```env
META_ACCESS_TOKEN=your_meta_access_token_here
```

3. Restart the application to use real API data

### Provider Setup

#### Meta (Facebook/Instagram) - Stub Implementation
1. Create a Meta Developer Account: https://developers.facebook.com/
2. Create a new app with Facebook Login and Instagram Basic Display
3. Generate an access token with required permissions
4. Add the token to your `.env` file

**Note**: Current implementation includes only a stub Meta provider that validates credentials structure but does not perform actual API calls. Full integration will be available in future releases.

## 🏗️ Architecture

```
social-video-explorer/
├── ui/                     # Streamlit frontend
│   └── streamlit_app.py    # Main web interface
├── core/                   # Core business logic
│   ├── schemas.py          # Pydantic data models
│   ├── services/           # Business services
│   │   └── search_service.py
│   └── providers/          # Video platform integrations
│       ├── base.py         # Abstract provider interface
│       ├── meta.py         # Meta/Facebook/Instagram provider
│       └── mock.py         # Mock provider for demo mode
└── workflows/              # Future: Temporal workflows
```

## 🧪 Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
```

### Type Checking

```bash
mypy .
```

### Linting

```bash
flake8 .
```

## 📜 License

MIT License - see LICENSE file for details

## 🗺️ Roadmap

### ✅ Completed (v0.1.0)
- [x] Basic architecture and mock provider
- [x] Meta provider stub with credential validation
- [x] Streamlit UI with search interface
- [x] Provider framework for extensibility
- [x] Configuration management with .env support

### 🚧 In Progress
- [ ] Complete Meta API integration with real video search

### 📋 Planned (Future Releases)
- [ ] YouTube provider implementation
- [ ] TikTok provider implementation
- [ ] Advanced search features (filters, pagination)
- [ ] Search result caching and rate limiting
- [ ] Export functionality (JSON, CSV)
- [ ] Container deployment (Docker)
- [ ] Enhanced UI with rich media cards
- [ ] Analytics and insights dashboard

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📞 Support

For questions and support, please open an issue on GitHub.