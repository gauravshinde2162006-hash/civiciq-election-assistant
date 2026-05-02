from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, jsonify, request

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "election_data.json"

app = Flask(__name__)

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

SUPPORTED_STATES = {
    "alabama": "Alabama", "al": "Alabama",
    "alaska": "Alaska", "ak": "Alaska",
    "arizona": "Arizona", "az": "Arizona",
    "arkansas": "Arkansas", "ar": "Arkansas",
    "california": "California", "ca": "California",
    "colorado": "Colorado", "co": "Colorado",
    "connecticut": "Connecticut", "ct": "Connecticut",
    "delaware": "Delaware", "de": "Delaware",
    "florida": "Florida", "fl": "Florida",
    "georgia": "Georgia", "ga": "Georgia",
    "hawaii": "Hawaii", "hi": "Hawaii",
    "idaho": "Idaho", "id": "Idaho",
    "illinois": "Illinois", "il": "Illinois",
    "indiana": "Indiana", "in": "Indiana",
    "iowa": "Iowa", "ia": "Iowa",
    "kansas": "Kansas", "ks": "Kansas",
    "kentucky": "Kentucky", "ky": "Kentucky",
    "louisiana": "Louisiana", "la": "Louisiana",
    "maine": "Maine", "me": "Maine",
    "maryland": "Maryland", "md": "Maryland",
    "massachusetts": "Massachusetts", "ma": "Massachusetts",
    "michigan": "Michigan", "mi": "Michigan",
    "minnesota": "Minnesota", "mn": "Minnesota",
    "mississippi": "Mississippi", "ms": "Mississippi",
    "missouri": "Missouri", "mo": "Missouri",
    "montana": "Montana", "mt": "Montana",
    "nebraska": "Nebraska", "ne": "Nebraska",
    "nevada": "Nevada", "nv": "Nevada",
    "new hampshire": "New Hampshire", "nh": "New Hampshire",
    "new jersey": "New Jersey", "nj": "New Jersey",
    "new mexico": "New Mexico", "nm": "New Mexico",
    "new york": "New York", "ny": "New York",
    "north carolina": "North Carolina", "nc": "North Carolina",
    "north dakota": "North Dakota", "nd": "North Dakota",
    "ohio": "Ohio", "oh": "Ohio",
    "oklahoma": "Oklahoma", "ok": "Oklahoma",
    "oregon": "Oregon", "or": "Oregon",
    "pennsylvania": "Pennsylvania", "pa": "Pennsylvania",
    "rhode island": "Rhode Island", "ri": "Rhode Island",
    "south carolina": "South Carolina", "sc": "South Carolina",
    "south dakota": "South Dakota", "sd": "South Dakota",
    "tennessee": "Tennessee", "tn": "Tennessee",
    "texas": "Texas", "tx": "Texas",
    "utah": "Utah", "ut": "Utah",
    "vermont": "Vermont", "vt": "Vermont",
    "virginia": "Virginia", "va": "Virginia",
    "washington": "Washington", "wa": "Washington",
    "west virginia": "West Virginia", "wv": "West Virginia",
    "wisconsin": "Wisconsin", "wi": "Wisconsin",
    "wyoming": "Wyoming", "wy": "Wyoming",
    "district of columbia": "District of Columbia", "dc": "District of Columbia",
    "maharashtra": "Maharashtra", "mh": "Maharashtra",
}

INDIAN_STATES = {
    "andhra pradesh": "Andhra Pradesh", "ap": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh", "ar": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh", "cg": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh", "hp": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka", "ka": "Karnataka",
    "kerala": "Kerala", "kl": "Kerala",
    "madhya pradesh": "Madhya Pradesh", "mp": "Madhya Pradesh",
    "maharashtra": "Maharashtra", "mh": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha", "orissa": "Odisha", "od": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu", "tn": "Tamil Nadu",
    "telangana": "Telangana", "tg": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh", "up": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand", "uk": "Uttarakhand",
    "west bengal": "West Bengal", "wb": "West Bengal",
    "andaman and nicobar islands": "Andaman and Nicobar Islands",
    "chandigarh": "Chandigarh",
    "dadra and nagar haveli and daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "delhi": "Delhi", "nct of delhi": "Delhi", "national capital territory of delhi": "Delhi",
    "jammu and kashmir": "Jammu and Kashmir", "jk": "Jammu and Kashmir",
    "ladakh": "Ladakh",
    "lakshadweep": "Lakshadweep",
    "puducherry": "Puducherry", "pondicherry": "Puducherry",
}


def normalize_state(state: str) -> str:
    """Return a supported canonical state name or an empty string."""
    key = state.strip().lower() if state else ""
    return SUPPORTED_STATES.get(key, INDIAN_STATES.get(key, ""))


def is_indian_state(state: str) -> bool:
    key = state.strip().lower() if state else ""
    return key in INDIAN_STATES and INDIAN_STATES.get(key) is not None

SYSTEM_PROMPT_TEMPLATE = """You are CivicIQ — a professional, warm, and completely nonpartisan Election Intelligence Assistant specialized in US election procedures, voting rules, registration requirements, and electoral processes.

{state_context}

YOUR PRIMARY MISSION:
- Provide **accurate, state-specific election information** to help citizens navigate registration, voting procedures, deadlines, ID requirements, and ballot options
- Be encouraging and accessible — make voting easy to understand for first-time voters, elderly voters, and anyone confused
- Always include specific dates, deadlines, and actionable steps
- Never advocate for parties, candidates, or ideologies — focus purely on voting procedures and logistics

RESPONSE GUIDELINES:
✓ **Be specific with facts:** Include exact registration deadlines, ID requirements, early voting dates, etc.
✓ **Use clear numbered steps:** For processes (registration, voting day, requesting mail ballots)
✓ **Add urgency where needed:** "Registration deadline is October 19 (42 days away)"
✓ **Reference official sources:** Mention state election authority, county registrar, election.gov
✓ **End with natural follow-ups:** Always suggest a logical next question or related topic
✓ **Format with bold/bullet points:** Make information scannable (use **bold** for key terms, • for lists)
✓ **Detect confusion:** If the user says "I don't know," "confused," "not sure" — simplify and use analogies
✓ **Add 1–2 clickable follow-up chips:** End with [Question one?] [Question two?]

DOMAIN EXPERTISE:
- Registration deadlines, methods (online, mail, in-person), requirements
- Voter ID laws (which states require ID, what's acceptable)
- Voting procedures (polling places, ballot types, what to expect)
- Early voting windows and mail-in/absentee ballot processes
- Election dates and key timeline milestones
- Eligibility requirements (age, citizenship, residency)
- State-specific rules and variations

For {state_context if state_context else 'general US elections'}:
Include specific deadlines, rules, and processes. Reference official state election authority when available.

TONE: Professional, warm, encouraging, patient, and completely neutral. Help every voter feel confident."""


def build_state_context(state: str) -> str:
    state = normalize_state(state)
    if not state:
        return (
            "The user has not specified their state. Provide accurate general US election information. "
            "Gently encourage them to share their state for personalized guidance."
        )
    if is_indian_state(state):
        return (
            f"The user is in India, specifically {state}. Tailor all information to Indian election rules, "
            f"registration procedures, voting methods, and deadlines for {state}. Use Election Commission of India "
            f"and the state's Chief Electoral Officer when relevant."
        )
    return (
        f"The user is in **{state}**. Tailor ALL information — registration deadlines, "
        f"ID laws, polling rules, early voting windows — specifically to {state}. "
        f"Always lead with state-specific details and cite the state election authority when relevant."
    )


def load_election_data() -> dict:
    if DATA_FILE.exists():
        with DATA_FILE.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def topic_from_message(message: str) -> str:
    text = message.lower()
    if any(k in text for k in ["register", "registration", "sign up"]):
        return "register_to_vote"
    if any(k in text for k in ["timeline", "deadline", "when is", "election date", "key dates"]):
        return "election_timeline"
    if any(k in text for k in ["vote", "voting", "ballot", "poll", "polling place"]):
        return "voting_process"
    return "general"


def get_state_data(state: str) -> dict:
    """Return accurate state-specific election data."""
    state = normalize_state(state)
    if is_indian_state(state) and state != "Maharashtra":
        return {}
    states_db = {
        "california": {
            "reg_deadline": "October 19, 2026 (15 days before)",
            "online_reg": "Yes ✓ (register.elections.ca.gov)",
            "early_voting": "Yes — October 5–November 2",
            "voter_id": "Not required (but ID speeds up check-in)",
            "polling_rules": "Must be registered to vote",
            "affiliation_deadline": "October 19, 2026",
            "absentee": "Yes — request by October 27 or vote by mail automatically sent",
        },
        "texas": {
            "reg_deadline": "October 4, 2026 (30 days before)",
            "online_reg": "No (register in person at county registrar)",
            "early_voting": "Yes — October 13–16 and October 19–23",
            "voter_id": "Required (driver's license, passport, or approved ID)",
            "polling_rules": "Photo ID required; voter registration card helpful",
            "absentee": "Limited — age 65+, illness, absence from county, or disability",
            "registration_location": "County registrar office, some libraries, or online",
        },
        "florida": {
            "reg_deadline": "October 5, 2026 (29 days before)",
            "online_reg": "Yes ✓ (registertovoteflorida.gov)",
            "early_voting": "Yes — October 24–November 1",
            "voter_id": "Required (Florida driver license, passport, military ID, or student ID)",
            "polling_rules": "Bring valid ID; registration must be current",
            "absentee": "Yes — request by October 29 (27 days before) or vote by mail",
            "same_day_reg": "No — must register 29 days before",
        },
        "new york": {
            "reg_deadline": "October 9, 2026 (25 days before)",
            "online_reg": "Yes ✓ (ny.elections.gov)",
            "early_voting": "Yes — October 24–November 1",
            "voter_id": "Not required (bring ID if possible)",
            "polling_rules": "Registration list reviewed; bring ID to speed process",
            "absentee": "Yes — no excuse needed; apply by November 2",
            "affiliation_deadline": "October 9, 2026",
        },
        "maharashtra": {
            "reg_deadline": "Check Election Commission of India (ECI) schedule",
            "online_reg": "Via ECI portal (electoralsearch.in)",
            "early_voting": "Advance voting available for select categories",
            "voter_id": "Voter ID or Aadhaar card recommended",
            "polling_rules": "Must be on voter roll; bring address proof",
            "registration_location": "District election office or online",
            "note": "Elections managed by Election Commission of India",
        }
    }
    
    return states_db.get(state.lower() if state else "", {})


def build_json_fallback(message: str, state: str = "") -> str:
    """Enhanced fallback with accurate election information."""
    text = message.lower()
    state_data = get_state_data(state)
    state_prefix = f"**In {state}:**\n" if state else ""
    indian_state = is_indian_state(state)
    state_note = (
        f"• I can give you general guidance for {state}, but check the Election Commission of India and your state's Chief Electoral Officer for exact local rules.\n\n"
        if state and not state_data
        else ""
    )

    # REGISTRATION responses
    if any(k in text for k in ["register", "registration", "sign up", "enrolled"]):
        response = "**How to Register to Vote**\n\n"
        if state:
            response += f"{state_prefix}"
            if state_data:
                response += f"• **Registration Deadline:** {state_data.get('reg_deadline', 'Check your state website')}\n"
                response += f"• **Online Registration:** {state_data.get('online_reg', 'Check availability')}\n"
                response += f"• **Registration Requirements:** Must be 18+, U.S. citizen, resident of your state\n\n"
                response += "**Steps to Register:**\n"
                response += "1. Visit your state's voter registration website or visit your county registrar\n"
                response += "2. Provide your name, address, driver's license or last 4 SSN digits\n"
                response += f"3. Register **before {state_data.get('reg_deadline', 'the deadline')}**\n"
                response += "4. Confirm your registration status 1–2 weeks before Election Day\n\n"
                response += f"⏰ **URGENT:** Registration closes in about {state_data.get('reg_deadline', '30 days')}. Don't wait!\n\n"
            elif indian_state:
                response += state_note
                response += "1. Check the electoral roll or voter registration portal for your state\n"
                response += "2. Verify you are an Indian citizen and at least 18 years old\n"
                response += "3. Provide your identity and address details (EPIC/voter ID, Aadhaar, or other accepted ID if requested)\n"
                response += "4. Submit the form through the Election Commission of India or your Chief Electoral Officer's website\n"
                response += "5. Confirm your name appears on the voter list before polling day\n\n"
            else:
                response += state_note
                response += "1. Check your state's voter registration website\n"
                response += "2. Verify you're age 18+, a U.S. citizen, and a state resident\n"
                response += "3. Provide personal info, address, and ID details\n"
                response += "4. Submit and confirm your registration\n"
                response += "5. Check your status 1–2 weeks before Election Day\n\n"
        else:
            response += "1. Check your state's voter registration website (search '[Your State] voter registration')\n"
            response += "2. Verify you're age 18+, a U.S. citizen, and a state resident\n"
            response += "3. Provide personal info, address, and ID details\n"
            response += "4. Submit and confirm your registration\n"
            response += "5. Check your status 1–2 weeks before Election Day\n\n"
        response += "[What documents do I need?] [When must I register by?]"
        return response

    # ID/DOCUMENTS responses
    if any(k in text for k in ["id", "document", "bring", "driver's license", "passport", "proof"]):
        response = "**What to Bring to Vote**\n\n"
        if state:
            response += f"{state_prefix}"
            if state_data:
                response += f"**ID Status:** {state_data.get('voter_id', 'Check local requirements')}\n\n"
            elif indian_state:
                response += state_note
                response += "**ID Status:** Carry your voter ID/EPIC or another accepted photo ID if your polling office requests it\n\n"
            else:
                response += state_note
        if indian_state:
            response += "**Commonly Used IDs in India:**\n"
            response += "✓ EPIC / Voter ID card\n"
            response += "✓ Aadhaar card if accepted locally\n"
            response += "✓ Passport or driving licence if requested by the election office\n"
            response += "✓ Any other government-issued photo ID listed by the polling authority\n\n"
        else:
            response += "**Generally Accepted IDs:**\n"
            response += "✓ Driver's license\n"
            response += "✓ Passport or military ID\n"
            response += "✓ State ID card\n"
            response += "✓ Student ID (if approved by your state)\n"
            response += "✓ Voter registration card\n"
            response += "✓ Proof of address (utility bill, lease)\n\n"
        response += "**Pro Tip:** Even if ID isn't required, bringing it speeds up check-in and prevents confusion.\n\n"
        response += "[What if my ID is expired?] [Can I vote without an ID?]"
        return response

    # ELIGIBILITY responses
    if any(k in text for k in ["eligible", "eligibility", "can i vote", "am i old enough", "citizenship"]):
        response = "**Are You Eligible to Vote?**\n\n"
        if indian_state:
            response += "To vote in India, you generally must:\n"
            response += "✓ Be **18 years old** on or before the qualifying date\n"
            response += "✓ Be an **Indian citizen**\n"
            response += "✓ Be enrolled on the **electoral roll**\n"
            response += "✓ Be registered in the constituency where you intend to vote\n\n"
            response += f"**In {state}:** Check your state's CEO/ECI guidance for local enrollment and polling rules.\n\n"
        else:
            response += "To vote in the U.S., you must:\n"
            response += "✓ Be **18 years old** on or before Election Day\n"
            response += "✓ Be a **U.S. citizen**\n"
            response += "✓ Be a **resident** of your state\n"
            response += "✓ Be registered to vote\n"
            response += "✓ Not be incarcerated for a felony (varies by state)\n\n"
            if state:
                response += f"**In {state}:** Check specific residency and registration rules — every state is slightly different.\n\n"
        response += "If you meet these requirements, you're eligible! Register today.\n\n"
        response += "[How do I register?] [What if I'm not 18 yet?]"
        return response

    # DEADLINE/TIMELINE responses
    if any(k in text for k in ["timeline", "deadline", "when is", "date", "how long", "weeks", "days"]):
        response = "**Key Election Dates for November 3, 2026**\n\n"
        if state and state_data:
            response += f"{state_prefix}"
            response += f"📋 **Registration Deadline:** {state_data.get('reg_deadline', 'Varies — check website')}\n"
            if "early_voting" in state_data:
                response += f"🗳️ **Early Voting:** {state_data.get('early_voting', 'Not available')}\n"
            if "absentee" in state_data:
                response += f"✉️ **Mail-in/Absentee:** {state_data.get('absentee', 'Check availability')}\n"
        elif indian_state:
            response += f"{state_prefix}"
            response += "📋 **Registration:** Check the electoral roll and voter registration updates with the ECI or your state's CEO\n"
            response += "🗳️ **Polling:** Confirm your polling station before election day\n"
            response += "✉️ **Absentee:** Follow Election Commission rules for your category and location\n"
        elif state:
            response += f"{state_prefix}{state_note}"
        response += "📅 **Election Day:** November 3, 2026 — Polls open early morning to evening\n"
        response += "✓ **Results:** Typically counted same-day evening or within a few days\n\n"
        response += "**Countdown:** You have about 6 months to prepare! Don't miss registration deadlines.\n\n"
        response += "[What's the registration deadline?] [Can I vote before November 3?]"
        return response

    # VOTING PROCESS responses
    if any(k in text for k in ["vote", "voting", "ballot", "poll", "what to bring", "polling place", "election day"]):
        response = "**How to Vote**\n\n"
        if state:
            response += f"{state_prefix}"
            if state_data:
                response += f"• **Voter ID Required:** {state_data.get('voter_id', 'Check your state')}\n"
                response += f"• **Early Voting:** {state_data.get('early_voting', 'Not available')}\n\n"
            elif indian_state:
                response += state_note
                response += "• **Voting system:** Check your name and polling station on the electoral roll\n"
                response += "• **ID:** Carry your voter ID/EPIC or another accepted photo ID if instructed by the election office\n\n"
            else:
                response += state_note
        if indian_state:
            response += "**What to Do on Polling Day:**\n"
            response += "1. Confirm your name on the electoral roll and your polling station\n"
            response += "2. Bring your voter ID/EPIC or another accepted ID if required\n"
            response += "3. Follow the instructions at the polling station and cast your vote privately\n"
            response += "4. Review the ballot and complete voting as directed by officials\n\n"
            response += f"**{state} Specifics:**\n"
            response += "Check polling station details and voting dates with the Election Commission of India or your state's CEO.\n"
            response += "Would you like help checking your voter roll or polling location?\n\n[Where do I vote?] [How do I check the voter roll?]"
            return response

        response += "**What to Do on Election Day (November 3, 2026):**\n"
        response += "1. Find your polling place online (search '[Your State] polling location')\n"
        response += "2. Bring a valid ID and any required documents\n"
        response += "3. Arrive with time to spare — wait times vary by location\n"
        response += "4. Check in with poll workers and receive your ballot\n"
        response += "5. Go to a private booth and mark your choices carefully\n"
        response += "6. Review your ballot before submitting\n"
        response += "7. Submit and collect your 'I Voted' sticker!\n\n"
        if state and state_data:
            response += f"**{state} Specifics:**\n"
            if "early_voting" in state_data and state_data["early_voting"]:
                response += f"Early voting is available {state_data['early_voting']}\n"
        elif state:
            response += f"**{state} Specifics:**\n"
            response += "Check your state election authority for local voting locations and hours.\n"
        response += "Would you like help finding your polling place?\n\n[Where do I vote?] [Can I vote early?]"
        return response

    # EARLY VOTING / ABSENTEE responses
    if any(k in text for k in ["early", "absentee", "mail-in", "mail", "vote by mail"]):
        response = "**Early Voting & Mail-in Options**\n\n"
        if state:
            response += f"{state_prefix}"
            if state_data:
                response += f"• **Early Voting:** {state_data.get('early_voting', 'Check availability')}\n"
                response += f"• **Mail-in/Absentee:** {state_data.get('absentee', 'Check availability')}\n\n"
            elif indian_state:
                response += state_note
                response += "• **Voting method:** Check your polling station and voter roll details with the ECI or your state's CEO\n\n"
            else:
                response += state_note
        else:
            response += "Many states offer options to vote before Election Day:\n\n"
        response += "**Early Voting (In-Person):**\n"
        response += "• Vote at designated polling places 1–2 weeks before November 3\n"
        response += "• Same rules as Election Day voting\n"
        response += "• Reduces crowds and lines\n\n"
        response += "**Mail-in/Absentee Voting:**\n"
        response += "• Request your ballot 2–3 weeks before Election Day\n"
        response += "• Vote at home at your own pace\n"
        response += "• Return by mail (postmark early!) or drop off in person\n"
        response += "• Deadline typically ~27–29 days before election\n\n"
        response += "Ready to vote early? Contact your county election office!\n\n"
        response += "[How do I request a mail-in ballot?] [Where's my polling place?]"
        return response

    # GENERAL/DEFAULT responses
    state_msg = f"**Great question!** I'm personalized for {state}. " if state else ""
    return (
        f"**Welcome to CivicIQ** 🗳️\n\n{state_msg}"
        "I can help you with everything about voting:\n\n"
        "📝 **Voter Registration** — How, when, and where to register\n"
        "🗳️ **Voting Process** — What to expect on Election Day\n"
        "📅 **Dates & Deadlines** — Key dates for your state\n"
        "🪪 **ID & Documents** — What to bring to vote\n"
        "✉️ **Early & Mail-in** — Vote before November 3\n"
        "✓ **Eligibility** — Check if you can vote\n\n"
        "**What would you like to know?**\n\n"
        "[How do I register to vote?] [When's the registration deadline?]"
    )


@app.route("/")
def index() -> str:
    index_file = BASE_DIR / "index.html"
    with index_file.open("r", encoding="utf-8") as fh:
        return fh.read()


@app.route("/api/chat", methods=["POST"])
def chat() -> tuple:
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return jsonify({"error": "Message is required."}), 400
    state = normalize_state(str(payload.get("state", "")).strip())
    return jsonify({"message": build_json_fallback(message, state), "role": "assistant"})


@app.route("/api/topics")
def topics() -> tuple:
    data = load_election_data()
    result = []
    for key in ["register_to_vote", "voting_process", "election_timeline"]:
        if key in data:
            result.append({
                "id": key,
                "label": data[key].get("button_label", key.replace("_", " ").title()),
                "message": data[key].get("prompt", ""),
            })
    return jsonify({"topics": result})


@app.route("/api/claude-chat", methods=["POST"])
def claude_chat() -> tuple:
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    state = normalize_state(str(payload.get("state", "")).strip())
    history = payload.get("conversation_history", [])

    if not message:
        return jsonify({"error": "Message is required."}), 400

    # Fallback if no API key
    if not CLAUDE_API_KEY:
        return jsonify({"message": build_json_fallback(message, state), "role": "assistant"})

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

        system = SYSTEM_PROMPT_TEMPLATE.format(
            state_context=build_state_context(state)
        )

        messages = []
        for msg in history[-12:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

        # Ensure last message isn't duplicated
        if not messages or messages[-1].get("content") != message:
            messages.append({"role": "user", "content": message})

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=system,
            messages=messages,
        )

        reply = response.content[0].text
        return jsonify({"message": reply, "role": "assistant"})

    except ImportError:
        return jsonify({"message": build_json_fallback(message, state), "role": "assistant"})
    except Exception as e:
        app.logger.error(f"Claude API error: {e}")
        return jsonify({"message": build_json_fallback(message, state), "role": "assistant"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
