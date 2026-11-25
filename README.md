# 🤖 AI Code Reviewer

An AI-powered pull request reviewer built with Python, the OpenAI API, Docker, and GitHub Actions.

When a pull request is opened, it reads the code changes, asks an AI model to review them
for bugs, security issues, and performance problems, and posts the review as a PR comment.

## Run locally with Docker
1. Copy `.env.example` to `.env` and fill in your values
2. Run the tests: `docker compose run --rm tests`
3. Run the reviewer: `docker compose run --rm reviewer`