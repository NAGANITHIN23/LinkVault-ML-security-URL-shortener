# LinkVault Pro

Production URL shortener with ML-based phishing detection, Redis caching, and FastAPI backend.

## Features

- High-performance backend handling 688 req/sec with P95 latency of 176ms
- ML phishing detection analyzing 18 URL features with 95% accuracy
- Redis cache-aside pattern for 100x latency reduction (5ms → 0.05ms)
- PostgreSQL with B-tree indexing for O(log n) queries
- Real-time statistics and QR code generation
- Docker containerization for easy deployment

## Tech Stack

**Backend:** FastAPI, Python 3.12, PostgreSQL, Redis  
**DevOps:** Docker Compose, AWS EC2  
**Testing:** Apache Bench (10K requests, zero failures)

## Quick Start
```bash
git clone https://github.com/NAGANITHIN23/LinkVault-ML-security-URL-shortener.git
cd LinkVault-ML-security-URL-shortener
cp .env.example .env
docker-compose up -d
```

Visit `http://localhost:8000`

## Performance Metrics

- Throughput: 688 req/sec
- P95 Latency: 176ms
- Cache Hit Rate: 99%
- Success Rate: 100%

## Architecture

FastAPI → Redis Cache → PostgreSQL Database  
↓  
ML Phishing Detection → Web UI

## License

MIT License
