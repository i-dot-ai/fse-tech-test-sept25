# Receipt Tracker - Interview Demo Application

> [!WARNING]
> This application is designed specifically for technical interviews. 
> This should **NOT** be used in production or for any real-world purpose. 
> If you think you could do better, then we would like to hear from you!

## Overview

This is a Python-based receipt tracking application.

## Features

- **Receipt Upload**: Upload receipt images, PDFs, or text files
- **AI Text Extraction**: Automatically extracts key information
- **Expense Classification**: AI categorizes expenses into categories
- **Multi-user Support**: Email-based user identification 
- **30-Day Summaries**: AI-generated expense summaries with totals and VAT calculations


## Setup Instructions

1. **Install dependencies**:
   ```bash
   make setup
   ```

2. **Configure OpenAI API**:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key to the `.env` file

3. **Run the application**:
   ```bash
   make run
   ```

4. **Access the application**:
   - Open http://localhost:5000 in your browser

## Available Make Commands

- `make setup` - Install dependencies and create .env file
- `make run` - Start the Flask application
- `make clean` - Remove uploads and database files
- `make help` - Show all available commands

## Usage

1. **Upload Receipt**: Enter your email and select a receipt file
2. **View Receipts**: Enter your email to see your uploaded receipts
3. **Generate Summary**: Click the summary button to get AI-powered expense analysis

## Sample Data

The project includes two sample British receipts:
- `receipt1.txt` - Pret A Manger coffee and food (�10.98 total, �1.83 VAT)
- `receipt2.csv` - Currys PC World electronics (�102.47 total, �17.08 VAT)


## License

MIT

