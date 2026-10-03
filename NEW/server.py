"""
Sarathi AI (Cascade India) - Full Stack Backend & Triage Engine
Smart India Hackathon (SIH) Prototype
"""

import os
import json
import time
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
import requests
from dotenv import load_dotenv

# Load local environment
load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')

# Configuration & Runtime State
CONFIG = {
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "PORT": int(os.getenv("PORT", 5000))
}

# In-Memory State for Prototype
STATE = {
    "requester_wallet": {
        "balance_inr": 2500,
        "escrow_locked_inr": 0,
        "upi_id": "shivu@oksbi"
    },
    "workers": [
        {
            "id": "w_1",
            "name": "Aarav Sharma",
            "city": "Bengaluru",
            "tier": "gig",
            "upi_id": "aarav.gig@okhdfc",
            "rating": 4.94,
            "tasks_completed": 48,
            "balance_inr": 1820,
            "specialties": ["Store Calling", "App Testing", "Local Errands"]
        },
        {
            "id": "w_2",
            "name": "Priya Nair, CA Inter",
            "city": "Delhi NCR",
            "tier": "expert",
            "upi_id": "priya.ca@okaxis",
            "rating": 5.0,
            "tasks_completed": 19,
            "balance_inr": 4500,
            "specialties": ["Tax Review", "GST Invoicing", "Legal Drafting"]
        },
        {
            "id": "w_3",
            "name": "Rohan Deshmukh",
            "city": "Pune",
            "tier": "gig",
            "upi_id": "rohan.d@icici",
            "rating": 4.88,
            "tasks_completed": 31,
            "balance_inr": 960,
            "specialties": ["Hindi/Marathi Translation", "Document Verification"]
        }
    ],
    "tasks": [],
    "triage_logs": []
}

def log_triage_decision(task_id, query, tier, reasoning, confidence, latency_ms, quote_inr, source="heuristic"):
    log_entry = {
        "id": f"log_{uuid.uuid4().hex[:6]}",
        "task_id": task_id,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "query": query,
        "tier": tier,
        "reasoning": reasoning,
        "confidence": confidence,
        "latency_ms": latency_ms,
        "quote_inr": quote_inr,
        "source": source
    }
    STATE["triage_logs"].insert(0, log_entry)
    if len(STATE["triage_logs"]) > 50:
        STATE["triage_logs"].pop()
    return log_entry

def save_env_keys():
    """Persist keys to .env file so they survive server restarts."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    try:
        lines = []
        lines.append(f"PORT={CONFIG['PORT']}\n")
        lines.append(f"GEMINI_API_KEY={CONFIG['GEMINI_API_KEY']}\n")
        lines.append(f"GROQ_API_KEY={CONFIG['GROQ_API_KEY']}\n")
        lines.append(f"TELEGRAM_BOT_TOKEN={CONFIG['TELEGRAM_BOT_TOKEN']}\n")
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    except Exception as e:
        print(f"[!] Could not write .env: {e}")

def smart_heuristic_triage(query: str):
    """
    Intelligent dynamic Indian market classifier when API keys are not provided.
    Dynamically analyzes query intent, extracts entities, and generates tailored answers.
    """
    q = query.strip()
    ql = q.lower()
    
    # 1. Tier 3: Expert / Credentialed tasks
    expert_keywords = [
        "legal", "contract", "advocate", "lawyer", "nda", "statutory", "gst",
        "income tax", "itr", "audit", "ca review", "chartered accountant",
        "medical", "prescription", "doctor second opinion", "security audit", "patent", "trademark"
    ]
    for kw in expert_keywords:
        if kw in ql:
            return {
                "tier": "expert",
                "tier_name": "Tier 3: Certified Specialist (CA / Legal)",
                "reasoning": f"Requires verified professional credential/legal liability ({kw}). Routed to vetted Indian CAs/Advocates.",
                "confidence": 0.94,
                "quote_inr": 450,
                "turnaround_mins": 45,
                "skills_required": ["CA/Legal Verification", "Indian Regulatory Compliance"],
                "direct_ai_response": None
            }

    # 2. Tier 2: Gig Worker / Physical / Phone call / Human verification tasks
    gig_keywords = [
        "call", "calling", "phone", "shop", "store", "hsr", "indiranagar", "koramangala",
        "market", "vendor", "test on phone", "android", "device test", "verify",
        "on-ground", "visit", "photo of", "translate to marathi", "translate to tamil",
        "translate to telugu", "translate to kannada", "translate to hindi", "local price",
        "stock check", "buy", "deliver", "physical", "realme", "xiaomi", "jio", "airtel"
    ]
    for kw in gig_keywords:
        if kw in ql:
            quote = 120
            mins = 20
            if any(k in ql for k in ["visit", "on-ground", "photo of", "buy"]):
                quote = 250
                mins = 45
            elif any(k in ql for k in ["translate", "test on phone", "device test"]):
                quote = 90
                mins = 15
                
            return {
                "tier": "gig",
                "tier_name": "Tier 2: Cascade India Gig Network",
                "reasoning": f"Requires real-world human action ({kw}): phone calling, device verification, or localized on-ground execution.",
                "confidence": 0.92,
                "quote_inr": quote,
                "turnaround_mins": mins,
                "skills_required": ["Voice/Local Calling", "Indian Network Testing"],
                "direct_ai_response": None
            }

    # 3. Tier 1: Free AI Tier (Dynamic generative response)
    ai_response = (
        "⚠️ AI Engine Offline (API Failure / High Demand).\n\n"
        "The Google Gemini API is currently experiencing a 503 Service Unavailable error or you have hit a rate limit. "
        "Please wait a moment and try again, or check your API keys."
    )
    
    return {
        "tier": "ai",
        "tier_name": "Tier 1: Instant AI (Offline)",
        "reasoning": "AI Triage failed to connect to Gemini API.",
        "confidence": 0,
        "quote_inr": 0,
        "turnaround_mins": 0,
        "skills_required": ["API Reliability"],
        "direct_ai_response": ai_response
    }

def call_live_gemini_triage(query: str, api_key: str):
    """Call Google Gemini for dynamic live AI triage."""
    models = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"]
    system_prompt = """You are the core Triage Intelligence Engine for Sarathi AI (Cascade India).
Analyze the user's task request and classify it into one of 3 tiers:
1. 'ai' (Cost: ₹0) - Informational, drafting, summarization, coding, scheduling, writing.
2. 'gig' (Cost: ₹50-₹200) - Real-world human actions (calling Indian local shops/vendors, testing apps on real Android phones, translation between regional Indian languages, physical store checks).
3. 'expert' (Cost: ₹300-₹1000) - High-skill certified professionals (CA income tax/GST filing, lawyer legal contract review, medical second opinion, senior security audit).

CRITICAL RULE: NEVER ask clarifying questions. Even if physical location or details are missing, classify it as 'gig' or 'expert' anyway. The human worker will ask the user for details later.

Respond strictly in valid JSON format:
{
  "tier": "ai" | "gig" | "expert",
  "reasoning": "1-2 sentence explanation of why this tier was selected",
  "confidence": 0.95,
  "quote_inr": 0 (for AI) or appropriate integer in INR,
  "turnaround_mins": 0 (for AI) or 15-60 (for human),
  "skills_required": ["skill1", "skill2"],
  "direct_ai_response": "Full detailed, helpful answer to user request if tier is 'ai', else null"
}"""

    last_err = None
    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": system_prompt + "\n\nUser Task: " + query}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}
        }
        
        # Retry loop for 503 High Demand / Rate Limits
        for attempt in range(3):
            try:
                res = requests.post(url, json=payload, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(raw_text)
                    return parsed, model_name
                elif res.status_code in [429, 503]:
                    # Wait and retry on rate limit or high demand
                    print(f"[*] Gemini API {res.status_code} on {model_name}. Retrying ({attempt+1}/3)...")
                    time.sleep(2)
                    last_err = f"{res.status_code}: {res.text}"
                    continue
                else:
                    last_err = f"{res.status_code}: {res.text}"
                    break # Break retry loop for 400/404 errors, try next model
            except Exception as e:
                last_err = str(e)
                time.sleep(1)
            
    raise Exception(f"Gemini API calls failed after retries: {last_err}")

def call_ai_proof_verifier(prompt: str, proof_text: str, proof_type: str, image_base64: str = None, image_mime: str = None):
    """AI Proof Verification Engine: Audits submitted deliverable against initial task prompt."""
    gemini_key = CONFIG.get("GEMINI_API_KEY")
    groq_key = CONFIG.get("GROQ_API_KEY")
    
    sys_prompt = """You are an AI Proof Verification Auditor for Sarathi AI.
Compare the User's Original Task against the Worker's Submitted Proof.
Determine if the worker answered or fulfilled the request accurately.

If the proof does not match the requested task (e.g. they uploaded a student ID card for a car cleaning task), return a low confidence score and set is_verified to false.

Respond strictly in valid JSON format:
{
  "is_verified": true,
  "confidence_score": 98,
  "audit_summary": "1 sentence verdict on proof validity"
}"""

    # Route to Gemini if image provided, since groq model doesn't support vision
    if image_base64 and gemini_key:
        groq_key = None 
        
    if groq_key:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": "openai/gpt-oss-20b",
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"User Task: {prompt}\nWorker Proof ({proof_type}): {proof_text}"}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
            r = requests.post(url, headers=headers, json=payload, timeout=10)
            if r.status_code == 200:
                parsed = json.loads(r.json()["choices"][0]["message"]["content"])
                return parsed
            else:
                print(f"[!] Groq Verification API error: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"[!] Groq Verification Exception: {e}")

    elif gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={gemini_key}"
            parts = [{"text": sys_prompt + f"\n\nUser Task: {prompt}\nWorker Proof ({proof_type}): {proof_text}"}]
            if image_base64:
                parts.append({"inlineData": {"mimeType": image_mime or "image/jpeg", "data": image_base64}})
                
            payload = {
                "contents": [{"parts": parts}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
            }
            
            for attempt in range(3):
                r = requests.post(url, json=payload, timeout=10)
                if r.status_code == 200:
                    parsed = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
                    return parsed
                elif r.status_code in [429, 503]:
                    print(f"[*] AI Proof Verification API {r.status_code}. Retrying ({attempt+1}/3)...")
                    time.sleep(2)
                    continue
                else:
                    print(f"[!] AI Proof Verification API error: {r.status_code} - {r.text}")
                    break
                    
        except Exception as e:
            print(f"[!] AI Proof Verification Exception: {e}")
            
    return {
        "is_verified": False,
        "confidence_score": 0,
        "audit_summary": "⚠️ AI Verification Engine Offline or API failed. Please review proof manually."
    }

def call_live_groq_triage(query: str, api_key: str):
    """Call Groq Cloud (Llama 3.3 70B) for ultra-fast live AI triage."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    system_prompt = """You are the core Triage Intelligence Engine for Sarathi AI (Cascade India).
Analyze the user's task request and classify it into one of 3 tiers:
1. 'ai' (Cost: ₹0) - Informational, drafting, coding, writing.
2. 'gig' (Cost: ₹50-₹200) - Real-world actions (phone calls to vendors, app testing, regional translation).
3. 'expert' (Cost: ₹300-₹1000) - Certified professionals (CA tax, legal review, medical).


CRITICAL RULE: NEVER ask clarifying questions. Even if physical location or details are missing, classify it as 'gig' or 'expert' anyway. The human worker will ask the user for details later.

Respond strictly in valid JSON format:
{
  "tier": "ai" | "gig" | "expert",
  "reasoning": "1-2 sentence explanation",
  "confidence": 0.95,
  "quote_inr": 0 or integer in INR,
  "turnaround_mins": 0 or 15-60,
  "skills_required": ["skill1"],
  "direct_ai_response": "Full detailed answer to user request if tier is 'ai', else null"
}"""
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }
    res = requests.post(url, headers=headers, json=payload, timeout=10)
    res.raise_for_status()
    raw = res.json()["choices"][0]["message"]["content"]
    return json.loads(raw)

# ----------------- Seed Initial Demo Data -----------------
def seed_demo_data():
    sample_tasks = [
        {
            "id": "task_101",
            "created_at": "10:15 AM",
            "query": "Draft a polite follow-up email to HR after 2nd round of interview",
            "tier": "ai",
            "tier_name": "Tier 1: Instant AI (₹0 Free)",
            "quote_inr": 0,
            "status": "AI_ANSWERED",
            "turnaround_mins": 0,
            "reasoning": "Text drafting and professional communication handled fully by AI.",
            "response": "Subject: Following Up: Round 2 Interview - [Your Name]\n\nDear [Interviewer Name],\n\nThank you for the opportunity to speak during the second round of interviews yesterday. I enjoyed learning more about the team's upcoming initiatives. Please let me know if you need any additional portfolio links or references from my end.\n\nBest regards,\n[Your Name]",
            "deliverable": None,
            "worker": None,
            "escrow_locked": False
        },
        {
            "id": "task_102",
            "created_at": "10:40 AM",
            "query": "Call Om Stationary in Koramangala and check if they have A3 drafting boards in stock and price",
            "tier": "gig",
            "tier_name": "Tier 2: Cascade India Gig Network",
            "quote_inr": 120,
            "status": "APPROVED_PAID_OUT",
            "turnaround_mins": 15,
            "reasoning": "Requires phone call to local shopkeeper in Kannada/Hindi to verify real-time stock.",
            "response": None,
            "deliverable": {
                "text": "Called Om Stationary (+91 98450 XXXXX). Spoke with Suresh. They have 4 units of Omega A3 Drafting Boards in stock priced at ₹680 each.",
                "proof_type": "Call Log & Shop Confirmation",
                "submitted_at": "10:52 AM"
            },
            "worker": {
                "name": "Aarav Sharma",
                "upi_id": "aarav.gig@okhdfc"
            },
            "escrow_locked": False,
            "payout_tx_id": "UPI-SETTLE-849204829104"
        }
    ]
    STATE["workers"] = [
        {"id": "w_1", "name": "Aarav Sharma", "city": "Bengaluru", "rating": 4.94, "upi_id": "aarav.gig@okhdfc"},
        {"id": "w_2", "name": "Priya Patel (CA Inter)", "city": "Delhi", "rating": 4.88, "upi_id": "priya.tax@okicici"},
        {"id": "w_3", "name": "Rohan Desai", "city": "Pune", "rating": 4.75, "upi_id": "rohan.d@okaxis"},
        {"id": "w_4", "name": "Shivam", "city": "Panipat", "rating": 4.99, "upi_id": "shivam.dev@okaxis"}
    ]
    STATE["tasks"] = sample_tasks

seed_demo_data()

# ----------------- API Endpoints -----------------

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_tasks = len(STATE["tasks"])
    ai_tasks = sum(1 for t in STATE["tasks"] if t["tier"] == "ai")
    human_tasks = sum(1 for t in STATE["tasks"] if t["tier"] in ["gig", "expert"])
    total_payouts = sum(t["quote_inr"] for t in STATE["tasks"] if t["status"] == "APPROVED_PAID_OUT")
    
    return jsonify({
        "status": "success",
        "wallet": STATE["requester_wallet"],
        "stats": {
            "total_tasks": total_tasks,
            "ai_tasks": ai_tasks,
            "human_tasks": human_tasks,
            "total_payouts_inr": total_payouts,
            "active_escrow_inr": STATE["requester_wallet"]["escrow_locked_inr"],
            "network_workers_online": len(STATE["workers"])
        }
    })

@app.route('/api/triage', methods=['POST'])
def triage_task():
    data = request.json or {}
    query = data.get("query", "")
    tg_chat_id = data.get("telegram_chat_id")
    
    if not query:
        return jsonify({"status": "error", "message": "Query is required"}), 400
        
    start_time = time.time()
    
    # 0. Check for budget constraints
    if STATE["requester_wallet"]["escrow_locked_inr"] > 2000:
        return jsonify({"status": "error", "message": "Escrow limit reached."}), 400

    task_id = f"task_{uuid.uuid4().hex[:6]}"
    
    # 1. Attempt Live AI (Gemini or Groq) if API Key exists, else use dynamic heuristic
    gemini_key = CONFIG.get("GEMINI_API_KEY")
    groq_key = CONFIG.get("GROQ_API_KEY")
    triage_res = None
    source = "heuristic"
    
    if groq_key:
        try:
            triage_res = call_live_groq_triage(query, groq_key)
            source = "groq-llama-3.3-70b"
        except Exception as e:
            print(f"[!] Groq API error: {e}. Falling back to Gemini / Heuristic...")
            if gemini_key:
                try:
                    triage_res, model_used = call_live_gemini_triage(query, gemini_key)
                    source = model_used
                except Exception as ge:
                    print(f"[!] Gemini API error: {ge}")
                    triage_res = smart_heuristic_triage(query)
            else:
                triage_res = smart_heuristic_triage(query)
    elif gemini_key:
        try:
            triage_res, model_used = call_live_gemini_triage(query, gemini_key)
            source = model_used
        except Exception as e:
            print(f"[!] Gemini API error: {e}")
            triage_res = smart_heuristic_triage(query)
    else:
        triage_res = smart_heuristic_triage(query)
        
    latency_ms = int((time.time() - start_time) * 1000)
    
    # 2. Construct Task Object
    tier = triage_res.get("tier", "ai")
    quote_inr = triage_res.get("quote_inr", 0)
    
    # Auto-analyse and enforce reasonable amount if AI returned 0 for a human task
    if tier == "gig" and quote_inr == 0:
        quote_inr = 150 # Standard gig rate
    elif tier == "expert" and quote_inr == 0:
        quote_inr = 800 # Standard expert rate
    
    # Extract requested worker from query
    target_worker = None
    if "shivam" in query.lower():
        target_worker = "Shivam"
    elif "aarav" in query.lower():
        target_worker = "Aarav Sharma"
        
    new_task = {
        "id": task_id,
        "created_at": datetime.now().strftime("%I:%M %p"),
        "query": query,
        "telegram_chat_id": tg_chat_id,
        "tier": tier,
        "tier_name": triage_res.get("tier_name", f"Tier: {tier}"),
        "reasoning": triage_res.get("reasoning", ""),
        "confidence": triage_res.get("confidence", 0.95),
        "quote_inr": quote_inr,
        "target_worker": target_worker,
        "turnaround_mins": triage_res.get("turnaround_mins", 0),
        "skills_required": triage_res.get("skills_required", []),
        "status": "AI_ANSWERED" if tier == "ai" else "QUOTED",
        "response": triage_res.get("direct_ai_response") if tier == "ai" else None,
        "deliverable": None,
        "worker": None,
        "escrow_locked": False,
        "payout_tx_id": None
    }
    
    STATE["tasks"].insert(0, new_task)
    
    # 3. Log Triage for Judge Visualizer
    log_triage_decision(
        task_id=task_id,
        query=query,
        tier=tier,
        reasoning=triage_res.get("reasoning", ""),
        confidence=triage_res.get("confidence", 0.95),
        latency_ms=latency_ms,
        quote_inr=quote_inr,
        source=source
    )
    
    return jsonify({
        "status": "success",
        "task": new_task,
        "latency_ms": latency_ms
    })

@app.route('/api/task/escrow', methods=['POST'])
def lock_escrow():
    data = request.json or {}
    task_id = data.get("task_id")
    
    task = next((t for t in STATE["tasks"] if t["id"] == task_id), None)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404
        
    amount = task["quote_inr"]
    
    # Move funds into escrow
    STATE["requester_wallet"]["balance_inr"] -= amount
    STATE["requester_wallet"]["escrow_locked_inr"] += amount
    
    task["status"] = "ESCROW_LOCKED"
    task["escrow_locked"] = True
    task["escrow_tx_id"] = f"UPI-HOLD-{uuid.uuid4().hex[:8].upper()}"
    
    return jsonify({
        "status": "success",
        "task": task,
        "wallet": STATE["requester_wallet"]
    })

@app.route('/api/worker/feed', methods=['GET'])
def get_worker_feed():
    # Return tasks that are in ESCROW_LOCKED or CLAIMED status
    active_tasks = [t for t in STATE["tasks"] if t["status"] in ["ESCROW_LOCKED", "CLAIMED", "DELIVERED"]]
    return jsonify({
        "status": "success",
        "tasks": active_tasks,
        "workers": STATE["workers"]
    })

@app.route('/api/worker/claim', methods=['POST'])
def claim_task():
    data = request.json or {}
    task_id = data.get("task_id")
    worker_id = data.get("worker_id", "w_1")
    
    task = next((t for t in STATE["tasks"] if t["id"] == task_id), None)
    worker = next((w for w in STATE["workers"] if w["id"] == worker_id), STATE["workers"][0])
    
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404
        
    task["status"] = "CLAIMED"
    task["worker"] = {
        "id": worker["id"],
        "name": worker["name"],
        "city": worker["city"],
        "upi_id": worker["upi_id"],
        "rating": worker["rating"]
    }
    
    # Send Telegram notification that task was claimed
    tg_chat_id = task.get("telegram_chat_id")
    if tg_chat_id and CONFIG.get("TELEGRAM_BOT_TOKEN"):
        msg = (
            f"⚡ *Task Accepted!*\n\n"
            f"Your task is now being worked on by *{worker['name']}*.\n"
            f"Rating: {worker['rating']}\n\n"
            f"Please wait while they complete the task and submit completion proof."
        )
        try:
            url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage"
            requests.post(url, json={"chat_id": tg_chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except Exception as e:
            print(f"[!] Telegram claim notify error: {e}")
    
    return jsonify({
        "status": "success",
        "task": task
    })

@app.route('/api/worker/ask', methods=['POST'])
def worker_ask():
    data = request.json or {}
    task_id = data.get("task_id")
    question = data.get("question")
    
    task = next((t for t in STATE["tasks"] if t["id"] == task_id), None)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404
        
    tg_chat_id = task.get("telegram_chat_id")
    if tg_chat_id and CONFIG.get("TELEGRAM_BOT_TOKEN"):
        msg = (
            f"💬 *Message from Worker ({task['worker']['name']}):*\n\n"
            f"{question}\n\n"
            f"_Reply directly to this message to answer._"
        )
        try:
            url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage"
            requests.post(url, json={"chat_id": tg_chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
            # Add to state so telegram bot knows next message is a reply
            STATE.setdefault("awaiting_reply", {})[tg_chat_id] = task_id
        except Exception as e:
            print(f"Error sending worker question: {e}")
            
    return jsonify({"status": "success"})

@app.route('/api/task/reply', methods=['POST'])
def handle_user_reply():
    data = request.json or {}
    chat_id = data.get("telegram_chat_id")
    text = data.get("text")
    
    if "awaiting_reply" in STATE and chat_id in STATE["awaiting_reply"]:
        task_id = STATE["awaiting_reply"][chat_id]
        task = next((t for t in STATE["tasks"] if t["id"] == task_id), None)
        if task:
            task["query"] = task["query"] + f"\n\n--- User Update ---\n{text}"
            del STATE["awaiting_reply"][chat_id]
            return jsonify({"status": "success", "handled": True})
            
    return jsonify({"status": "success", "handled": False})

@app.route('/api/worker/submit', methods=['POST'])
def submit_work():
    data = request.json or {}
    task_id = data.get("task_id")
    proof_text = data.get("proof_text", "Completed deliverable as requested.")
    proof_type = data.get("proof_type", "Manual Verification")
    img_b64 = data.get("proof_image_base64")
    img_mime = data.get("proof_image_mime")
    
    task = next((t for t in STATE["tasks"] if t["id"] == task_id), None)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404
        
    # Run AI Proof Verification Engine
    audit_res = call_ai_proof_verifier(task["query"], proof_text, proof_type, img_b64, img_mime)
    
    task["status"] = "DELIVERED"
    task["deliverable"] = {
        "text": proof_text,
        "proof_type": proof_type,
        "has_image": bool(img_b64),
        "submitted_at": datetime.now().strftime("%I:%M %p"),
        "ai_verification": audit_res
    }
    
    # Send Notification to Telegram user if chat_id present
    tg_chat_id = task.get("telegram_chat_id")
    if tg_chat_id and CONFIG.get("TELEGRAM_BOT_TOKEN"):
        # Send photo first if available
        if img_b64:
            import base64
            try:
                img_data = base64.b64decode(img_b64)
                files = {"photo": ("proof.jpg", img_data, img_mime or "image/jpeg")}
                requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendPhoto", data={"chat_id": tg_chat_id}, files=files, timeout=10)
            except Exception as e:
                print(f"[!] Telegram photo error: {e}")
                
        msg = (
            f"📦 *Deliverable Submitted for Review!*\n\n"
            f"• *Worker:* {task.get('worker', {}).get('name', 'Worker')}\n"
            f"• *Proof ({proof_type}):* {proof_text}\n"
            f"• *AI Audit Verdict:* {audit_res.get('audit_summary', 'Verified')}\n\n"
            f"Tap below to approve and trigger instant UPI payout:"
        )
        keyboard = {
            "inline_keyboard": [
                [{"text": f"⭐ Approve & Pay ₹{task['quote_inr']}", "callback_data": f"approve_{task['id']}"}]
            ]
        }
        
        # Add Reject button if AI score is low or is_verified is False
        score_val = str(audit_res.get("confidence_score", 100)).replace("%", "").strip()
        try:
            score = float(score_val)
        except:
            score = 100
            
        is_verified = audit_res.get("is_verified", True)
            
        if score < 80 or not is_verified:
            keyboard["inline_keyboard"][0].append(
                {"text": "❌ Reject Proof", "callback_data": f"reject_proof_{task['id']}"}
            )
            
        try:
            url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage"
            requests.post(url, json={"chat_id": tg_chat_id, "text": msg, "parse_mode": "Markdown", "reply_markup": keyboard}, timeout=5)
        except Exception as e:
            print(f"[!] Telegram deliverable notify error: {e}")

    return jsonify({
        "status": "success",
        "task": task,
        "ai_verification": audit_res
    })

@app.route('/api/task/approve', methods=['POST'])
def approve_and_payout():
    data = request.json or {}
    task_id = data.get("task_id")
    
    task = next((t for t in STATE["tasks"] if t["id"] == task_id), None)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404
        
    amount = task["quote_inr"]
    
    # Release from Escrow to Worker
    STATE["requester_wallet"]["escrow_locked_inr"] -= amount
    
    if task.get("worker"):
        w_id = task["worker"].get("id")
        worker_obj = next((w for w in STATE["workers"] if w["id"] == w_id), None)
        if worker_obj:
            worker_obj["balance_inr"] = worker_obj.get("balance_inr", 0) + amount
            worker_obj["tasks_completed"] = worker_obj.get("tasks_completed", 0) + 1
            
    payout_tx = f"UPI-SETTLE-{uuid.uuid4().hex[:10].upper()}"
    task["status"] = "APPROVED_PAID_OUT"
    task["payout_tx_id"] = payout_tx
    task["settled_at"] = datetime.now().strftime("%I:%M %p")
    
    return jsonify({
        "status": "success",
        "task": task,
        "payout_tx_id": payout_tx,
        "wallet": STATE["requester_wallet"]
    })

@app.route('/api/task/negotiate', methods=['POST'])
def negotiate_task():
    data = request.json or {}
    task_id = data.get("task_id")
    proposed_amount = int(data.get("proposed_amount", 0))
    
    task = next((t for t in STATE["tasks"] if t["id"] == task_id), None)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404
        
    # AI-driven Negotiation
    accepted = False
    groq_key = CONFIG.get("GROQ_API_KEY")
    if groq_key:
        sys_prompt = f"""You are a Negotiation AI for a Gig Network. 
The task is: '{task['query']}'. 
The required skills are: {task['skills_required']}.
The original quote was ₹{task['quote_inr']}.
The user is offering ₹{proposed_amount}.
Determine if this counter-offer is fair and reasonable for a human worker in India.
Reply strictly in JSON: {{"accepted": true/false, "reason": "1 short sentence explaining why"}}"""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": "openai/gpt-oss-20b",
                "messages": [{"role": "system", "content": sys_prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
            r = requests.post(url, headers=headers, json=payload, timeout=10)
            res_json = json.loads(r.json()["choices"][0]["message"]["content"])
            accepted = res_json.get("accepted", False)
            reason = res_json.get("reason", "Offer evaluated.")
        except Exception:
            accepted = proposed_amount >= (50 if task["tier"] == "gig" else 300)
            reason = "Offline threshold applied."
    else:
        accepted = proposed_amount >= (50 if task["tier"] == "gig" else 300)
        reason = "System threshold applied."
        
    if accepted:
        task["quote_inr"] = proposed_amount
        
    return jsonify({
        "status": "success",
        "task": task,
        "accepted": accepted,
        "reason": reason
    })

@app.route('/api/task/reject_proof', methods=['POST'])
def reject_deliverable_proof():
    data = request.json or {}
    task_id = data.get("task_id")
    task = next((t for t in STATE["tasks"] if t["id"] == task_id), None)
    if task:
        task["status"] = "CLAIMED"
        task["deliverable"] = None
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 404

@app.route('/api/task/reject', methods=['POST'])
def reject_deliverable():
    data = request.json or {}
    task_id = data.get("task_id")
    feedback = data.get("feedback", "Deliverable did not meet requirements.")
    
    task = next((t for t in STATE["tasks"] if t["id"] == task_id), None)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404
        
    task["status"] = "REVISION_REQUESTED"
    task["revision_feedback"] = feedback
    
    return jsonify({
        "status": "success",
        "task": task
    })

@app.route('/api/tasks', methods=['GET'])
def get_all_tasks():
    return jsonify({
        "status": "success",
        "tasks": STATE["tasks"]
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify({
        "status": "success",
        "logs": STATE["triage_logs"]
    })

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    if request.method == 'POST':
        data = request.json or {}
        if "GEMINI_API_KEY" in data:
            CONFIG["GEMINI_API_KEY"] = data["GEMINI_API_KEY"]
        if "GROQ_API_KEY" in data:
            CONFIG["GROQ_API_KEY"] = data["GROQ_API_KEY"]
        if "TELEGRAM_BOT_TOKEN" in data:
            CONFIG["TELEGRAM_BOT_TOKEN"] = data["TELEGRAM_BOT_TOKEN"]
            
        save_env_keys()
            
        return jsonify({
            "status": "success",
            "message": "Settings updated and saved to .env",
            "has_gemini": bool(CONFIG["GEMINI_API_KEY"]),
            "has_groq": bool(CONFIG["GROQ_API_KEY"]),
            "has_telegram": bool(CONFIG["TELEGRAM_BOT_TOKEN"])
        })
    else:
        return jsonify({
            "has_gemini": bool(CONFIG["GEMINI_API_KEY"]),
            "has_groq": bool(CONFIG["GROQ_API_KEY"]),
            "has_telegram": bool(CONFIG["TELEGRAM_BOT_TOKEN"]),
            "gemini_masked": f"***{CONFIG['GEMINI_API_KEY'][-4:]}" if CONFIG["GEMINI_API_KEY"] else "Not set",
            "groq_masked": f"***{CONFIG['GROQ_API_KEY'][-4:]}" if CONFIG["GROQ_API_KEY"] else "Not set",
            "telegram_masked": f"***{CONFIG['TELEGRAM_BOT_TOKEN'][-4:]}" if CONFIG["TELEGRAM_BOT_TOKEN"] else "Not set"
        })

@app.route('/api/reset', methods=['POST'])
def reset_demo():
    STATE["requester_wallet"] = {
        "balance_inr": 2500,
        "escrow_locked_inr": 0,
        "upi_id": "shivu@oksbi"
    }
    STATE["triage_logs"] = []
    seed_demo_data()
    return jsonify({"status": "success", "message": "Demo data reset successfully."})

@app.route('/')
def serve_index():
    return send_from_directory('public', 'index.html')

@app.route('/worker')
@app.route('/worker.html')
def serve_worker():
    return send_from_directory('public', 'worker.html')

if __name__ == '__main__':
    port = CONFIG["PORT"]
    print(f">> Sarathi AI Server running on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
