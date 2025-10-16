# CalCtl - Command Line Calendar Manager

A command-line calendar management tool that helps you organize, track, and manage your appointments and events efficiently.

## Features

- **Event Management**: Add, edit, delete, and view events
- **Smart Search**: Search events by title, description, or location  
- **Agenda Views**: Daily and weekly agenda displays
- **Conflict Detection**: Automatic scheduling conflict validation
- **Flexible Filtering**: Filter by date ranges, today, or this week
- **JSON Storage**: Simple file-based storage in JSON format
- **Docker Support**: Containerized deployment with persistent storage
- **CI/CD Ready**: GitHub Actions workflows included

## Installation

### From Source
```bash
git clone https://github.com/yourusername/calctl
cd calctl
pip install -e .
```

### Using Docker
```bash
# Pull from Docker Hub
docker pull yourusername/calctl:latest

# Create volume for persistent storage
docker volume create calctl-data

# Create alias for easy usage
alias calctl='docker run -v calctl-data:/home/appuser/.calctl yourusername/calctl:latest'
```

## Quick Start

```bash
# Add a new event
calctl add --title "Team Meeting" --date 2025-01-15 --time 14:00 --duration 60

# List today's events
calctl list --today

# Show this week's agenda
calctl agenda --week

# Search for events
calctl search "meeting"
```

## Usage

### Adding Events

```bash
# Basic event
calctl add --title "Meeting" --date 2025-01-15 --time 14:00 --duration 60

# Event with location and description
calctl add --title "Conference Call" \
  --date 2025-01-15 --time 10:00 --duration 90 \
  --location "Room 101" --description "Quarterly review"

# Override conflict detection
calctl add --title "Urgent Meeting" --date 2025-01-15 --time 14:30 --duration 60 --force
```

### Listing and Viewing Events

```bash
# List all future events
calctl list

# List today's events
calctl list --today

# List this week's events  
calctl list --week

# List events in date range
calctl list --from 2025-01-15 --to 2025-01-20

# Show detailed event information
calctl show evt-a1b2
```

### Editing and Deleting

```bash
# Edit event details
calctl edit evt-a1b2 --title "Updated Meeting" --duration 90

# Delete single event (with confirmation)
calctl delete evt-a1b2

# Delete without confirmation
calctl delete evt-a1b2 --force

# Delete all events on a date
calctl delete --date 2025-01-15
```

### Search and Agenda

```bash
# Search all fields
calctl search "meeting"

# Search titles only
calctl search "standup" --title

# Today's agenda
calctl agenda

# Specific date agenda
calctl agenda --date 2025-01-15

# Weekly agenda
calctl agenda --week
```

## Output Formats

CalCtl supports multiple output formats:

```bash
# Default table format
calctl list

# JSON output
calctl list --json

# Plain text (no colors/formatting)
calctl list --plain
```

## Docker Usage

### Building the Image

```bash
docker build -t calctl:latest .
```

### Running with Persistent Storage

```bash
# Create named volume
docker volume create calctl-data

# Run commands with persistent storage
docker run -v calctl-data:/home/appuser/.calctl calctl:latest add --title "Meeting" --date 2025-01-15 --time 14:00 --duration 60
docker run -v calctl-data:/home/appuser/.calctl calctl:latest list --today

# Create convenient alias
alias calctl='docker run -v calctl-data:/home/appuser/.calctl calctl:latest'
```

## Configuration

### Environment Variables

- `CALCTL_DB`: Override default database location
- `NO_COLOR`: Disable colored output

### Default Storage Location

Events are stored in `~/.calctl/events.json` by default.

## Development

### Setting up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/calctl
cd calctl

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ --cov=calctl

# Run integration tests (requires bats)
bats tests/test_integration.bats
```

### Project Structure

```
calctl/
├── src/calctl/           # Source code
│   ├── __init__.py       # Package initialization
│   ├── app.py           # CLI application
│   ├── core.py          # Core logic
│   └── storage.py       # Storage handling
├── tests/               # Test files
├── .github/workflows/   # CI/CD workflows
├── Dockerfile           # Docker configuration
├── setup.py            # Package configuration
└── requirements.txt     # Dependencies
```

### Running Tests

```bash
# Unit tests
pytest tests/test_core.py -v

# CLI tests  
pytest tests/test_app.py -v

# Integration tests (requires bats)
bats tests/test_integration.bats

# All tests with coverage
pytest --cov=calctl --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- 📖 Documentation: [GitHub Wiki](https://github.com/yourusername/calctl/wiki)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/calctl/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/calctl/discussions)