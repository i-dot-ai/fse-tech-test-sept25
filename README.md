# Receipt Tracker - Interview Demo Application

> [!WARNING]
> This application is designed specifically for technical interviews. 
> This should **NOT** be used in production or for any real-world purpose. 
> If you think you could do better, then we would like to hear from you!


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



## License

MIT

