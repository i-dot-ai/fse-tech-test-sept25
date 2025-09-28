import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from markitdown import MarkItDown
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
app.secret_key = 'simple-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize MarkItDown
markitdown = MarkItDown()

class ReceiptInfo(BaseModel):
    total: Optional[float] = None
    tax: Optional[float] = None
    currency: Optional[str] = None
    vendor: Optional[str] = None
    date: Optional[str] = None
    expense_code: Optional[str] = None

class ExpenseSummary(BaseModel):
    total_with_tax: Optional[float] = None
    total_without_tax: Optional[float] = None
    total_tax: Optional[float] = None
    receipt_count: Optional[int] = None
    summary_text: Optional[str] = None

def init_db():
    conn = sqlite3.connect('receipts.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            extracted_text TEXT,
            total_amount REAL,
            tax_amount REAL,
            currency TEXT,
            vendor TEXT,
            date TEXT,
            raw_ai_response TEXT,
            user_email TEXT NOT NULL,
            expense_code TEXT
        )
    ''')
    conn.commit()
    conn.close()

def extract_receipt_info(text):
    prompt = f"""
    Extract the following information from this receipt text:
    - Total amount (just the number)
    - Tax/VAT amount (just the number)  
    - Currency (e.g., USD, EUR, GBP)
    - Vendor/Store name
    - Date (if available)
    - Expense code: Categorise this expense into one of these categories:
      * CENTRAL
      * DISCRETIONARY
      * APPROVED
      * OTHER - for anything else that doesn't fit the above

    Receipt text:
    {text}
    """
    
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format=ReceiptInfo,
            temperature=0
        )
        
        receipt_info = completion.choices[0].message.parsed
        print(f"Extracted info: {receipt_info}")
        
        return {
            "total": receipt_info.total,
            "tax": receipt_info.tax,
            "currency": receipt_info.currency,
            "vendor": receipt_info.vendor,
            "date": receipt_info.date,
            "expense_code": receipt_info.expense_code
        }
    except Exception as e:
        print(f"AI extraction error: {e}")
        return {"total": None, "tax": None, "currency": None, "vendor": None, "date": None}

def generate_expense_summary(receipts_data):
    """Use AI to generate a summary of expenses from receipt data"""
    prompt = f"""
    Analyze the following receipt data and provide a comprehensive expense summary for the last 30 days:

    Receipt Data:
    {receipts_data}

    Please calculate and provide:
    1. Total amount with tax/VAT
    2. Total amount without tax/VAT (subtract tax from total)
    3. Total tax/VAT amount
    4. Number of receipts processed
    5. A brief summary of spending patterns (which vendors, categories, etc.)

    Make sure to handle different currencies appropriately and provide accurate calculations.
    """
    
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format=ExpenseSummary,
            temperature=0
        )
        
        summary = completion.choices[0].message.parsed
        print(f"Generated summary: {summary}")
        return summary
    except Exception as e:
        print(f"AI summary error: {e}")
        return ExpenseSummary(
            total_with_tax=0.0,
            total_without_tax=0.0, 
            total_tax=0.0,
            receipt_count=0,
            summary_text="Error generating summary"
        )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    if 'email' not in request.form or not request.form['email']:
        flash('Email is required')
        return redirect(url_for('index'))
    
    file = request.files['file']
    user_email = request.form['email']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Extract text using markitdown
        try:
            result = markitdown.convert(file_path)
            extracted_text = result.text_content
        except Exception as e:
            extracted_text = f"Error extracting text: {str(e)}"
        
        # Extract information using AI
        ai_info = extract_receipt_info(extracted_text)
        
        # Store in database
        conn = sqlite3.connect('receipts.db')
        c = conn.cursor()
        # VULNERABLE: String concatenation allows SQL injection
        query = f"""
            INSERT INTO receipts (filename, extracted_text, total_amount, tax_amount, 
                                currency, vendor, date, raw_ai_response, user_email)
            VALUES ('{filename}', '{extracted_text}', {ai_info['total'] or 'NULL'}, {ai_info['tax'] or 'NULL'}, 
                    '{ai_info['currency'] or ''}', '{ai_info['vendor'] or ''}', '{ai_info['date'] or ''}', 
                    '{json.dumps(ai_info)}', '{user_email}')
        """
        c.execute(query)
        conn.commit()
        conn.close()
        
        flash('Receipt uploaded and processed successfully!')
        return redirect(url_for('view_receipts', email=user_email))

@app.route('/receipts')
def view_receipts():
    user_email = request.args.get('email')
    
    conn = sqlite3.connect('receipts.db')
    c = conn.cursor()
    
    if user_email:
        # VULNERABLE: String concatenation allows SQL injection
        query = f"SELECT * FROM receipts WHERE user_email = '{user_email}' ORDER BY upload_date DESC"
        c.execute(query)
    else:
        receipts = []
        conn.close()
        return render_template('receipts.html', receipts=receipts)
    
    receipts = c.fetchall()
    conn.close()
    return render_template('receipts.html', receipts=receipts)

@app.route('/summary', methods=['POST'])
def expense_summary():
    user_email = request.form.get('email')
    
    if not user_email:
        flash('Email is required')
        return redirect(url_for('view_receipts'))
    
    # Get receipts from last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    conn = sqlite3.connect('receipts.db')
    c = conn.cursor()
    # VULNERABLE: String concatenation allows SQL injection  
    query = f"SELECT * FROM receipts WHERE user_email = '{user_email}' AND upload_date >= '{thirty_days_ago.isoformat()}' ORDER BY upload_date DESC"
    c.execute(query)
    
    receipts = c.fetchall()
    conn.close()
    
    if not receipts:
        flash('No receipts found in the last 30 days')
        return redirect(url_for('view_receipts', email=user_email))
    
    # Format receipt data for AI
    receipts_data = []
    for receipt in receipts:
        receipt_info = {
            'filename': receipt[1],
            'upload_date': receipt[2],
            'total_amount': receipt[4],
            'tax_amount': receipt[5],
            'currency': receipt[6],
            'vendor': receipt[7],
            'date': receipt[8]
        }
        receipts_data.append(receipt_info)
    
    # Generate AI summary
    summary = generate_expense_summary(json.dumps(receipts_data, indent=2))
    
    return render_template('summary.html', summary=summary, email=user_email, receipt_count=len(receipts))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)