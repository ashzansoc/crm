import frappe
import requests
import json
from frappe.utils import get_safe_filters, now_datetime

SYSTEM_PROMPT = """
You are an AI assistant for Frappe CRM. You have access to the CRM data via tools.
You can list, read, create, update, and delete records.

Current Date and Time: {current_datetime}

Common DocTypes and their purposes:
- CRM Lead: Potential customers.
    - Required Fields: first_name, status (Default: New).
    - Key Fields: lead_name (Full Name), last_name, salutation, email, mobile_no, phone, organization, website, annual_revenue, industry, territory, lead_owner, source, no_of_employees, gender, job_title.
    - Read-Only/System Fields: sla, sla_status, total, net_total.
    - Rules:
        - ALWAYS create a 'CRM Lead' record for leads.
        - 'first_name' is MANDATORY. Split full names into first_name/last_name.
        - 'status' options: New, Contacted, Nurture, Qualified, Unqualified, Junk.

- CRM Deal: Sales opportunities.
    - Required Fields: status (Default: Qualification).
    - Key Fields: organization, deal_name (mapped to organization), probability (%), annual_revenue, website, next_step, lead (Link to CRM Lead), deal_owner, email, mobile_no, territory, source, no_of_employees, industry, currency, deal_value, expected_deal_value, expected_closure_date, closed_date.
    - Conditional Fields:
        - 'lost_reason' is MANDATORY if status is 'Lost'.
        - 'lost_notes' is MANDATORY if lost_reason is 'Other'.
    - Rules:
        - Deals are often linked to an Organization or Lead.
        - 'status' options: Qualification, Demo/Making, Proposal/Quotation, Negotiation, Ready to Close, Won, Lost.

 - CRM Organization: Companies/Organizations.
      - Key Fields: organization_name (Unique), website, annual_revenue, no_of_employees (1-10, 11-50, etc.), industry (Link: CRM Industry), territory (Link: CRM Territory), currency, address (Link: Address).
      - Rules:
          - 'organization_name' is required.
          - Use 'industry' and 'territory' links if available.
 
 - Contact: People contacts.
     - Key Fields: first_name, last_name, email_id, mobile_no, phone, company_name, designation, department, salutation, gender, status (Passive, Open, Replied), user (Link to User), address (Link to Address).
     - Child Tables:
         - email_ids: List of email addresses.
         - phone_nos: List of phone numbers.
         - links: Dynamic links to other documents (e.g., Customer, Supplier).
     - Rules:
         - Use this DocType for general contacts or when explicitly asked.
         - 'first_name' is highly recommended.
         - 'links' table is used to associate the contact with other records.

  - FCRM Note: Notes on records.
      - Key Fields: title (Reqd), content (Text), reference_doctype, reference_docname.
      - Rules:
          - Use this for adding notes to Leads, Deals, etc.
          - Link to the parent record using reference_doctype/docname.

  - CRM Task: Tasks assigned to users.
      - Key Fields: title (Reqd), status (Backlog, Todo, In Progress, Done, Canceled), priority (Low, Medium, High), due_date, description, assigned_to (User), reference_doctype, reference_docname.
      - Rules:
          - Default status is 'Todo' or 'Backlog'.
          - Link to parent record if applicable.

  - CRM Call Log: Logs of phone calls.
      - Key Fields: type (Incoming/Outgoing), status (Completed, Missed, etc.), start_time, duration, from, to, recording_url, note (Link: FCRM Note), reference_doctype, reference_docname.
      - Rules:
          - 'type', 'from', 'to', 'status' are required.
          - Use 'Manual' for telephony_medium if not specified.

  - Event: Calendar events and meetings.
      - Key Fields: subject (Reqd), starts_on (Datetime), ends_on (Datetime), description, status (Open, Cancelled, Closed), all_day (Check), event_participants (Table: email).
      - Rules:
          - 'starts_on' is required.
          - Use 'event_participants' to add attendees.

When a user asks to create a record, try to infer the necessary fields. If critical information is missing, ask the user.
Always use the 'get_list' tool to search for records before assuming they don't exist.

IMPORTANT RULES FOR DATA HANDLING:
1. Automatic Salutations: Always try to infer a Salutation (Mr, Ms, Dr, etc.) for the lead based on the name or context. If not provided, use a reasonable default or ask, but prefer inferring.
2. Fuzzy Matching: When a user provides a value for a field (like Industry or Territory) that might be a typo or abbreviation (e.g., 'tech' for 'Technology', 'Mumai' for 'Mumbai'), try to match it to the closest valid option available in the system. Use `get_list` to check existing values.
3. Range Mapping: For fields requiring a range (like 'no_of_employees'), if the user provides a specific number (e.g., 10), map it to the correct range option (e.g., '1-10').
4. Auto-creation: If a user specifies a value for a Link field (like 'Territory') that does not exist, CREATE that record first using `create_doc`, and then use it in the main record creation.

CONTENT GENERATION RULES:
1. Concise Descriptions: When creating records (like Events, Tasks, Notes), generate concise, professional titles and descriptions based on the user's intent.
2. No Verbatim Copying: Do NOT copy the user's prompt verbatim into fields like 'description' or 'subject'.
3. Example: If User says "Schedule a meeting with Acme", Subject should be "Meeting with Acme Corp", NOT "Schedule a meeting with Acme".
"""

@frappe.whitelist()
def get_user_chat_history():
    return frappe.get_list("CRM AI Chat", 
        filters={"user": frappe.session.user}, 
        fields=["name", "title", "modified"], 
        order_by="modified desc"
    )

@frappe.whitelist()
def get_chat_session(name):
    doc = frappe.get_doc("CRM AI Chat", name)
    if doc.user != frappe.session.user:
        frappe.throw("Not authorized")
    return doc.messages

@frappe.whitelist()
def delete_chat_session(name):
    doc = frappe.get_doc("CRM AI Chat", name)
    if doc.user != frappe.session.user:
        frappe.throw("Not authorized")
    doc.delete()
    return "Deleted"

@frappe.whitelist()
def chat(message, history=None, chat_id=None):
    print(f"DEBUG: Received message: {message}")
    print(f"DEBUG: Received history type: {type(history)}")
    print(f"DEBUG: Received history: {history}")
    print(f"DEBUG: Received chat_id: {chat_id}")

    # TODO: Move API key to site config or settings
    api_key = "AIzaSyA5VS8vWejFeZTsLTSYBbtCrRdpjSJ_kG0"
    model = "gemini-3-pro-preview"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    
    # Format System Prompt with Current Date/Time
    current_time = now_datetime().strftime("%Y-%m-%d %H:%M:%S")
    formatted_system_prompt = SYSTEM_PROMPT.format(current_datetime=current_time)
    
    # Define Tools
    tools = [
        {
            "function_declarations": [
                {
                    "name": "get_list",
                    "description": "Get a list of records for a given DocType. Use this to find leads, deals, etc. Always use this to search for records.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "doctype": {"type": "STRING", "description": "The DocType to query (e.g., 'CRM Lead', 'CRM Deal', 'Contact', 'CRM Organization')"},
                            "filters": {"type": "OBJECT", "description": "Filters to apply (e.g., {'status': 'Nurture', 'email': 'test@example.com'})"},
                            "fields": {
                                "type": "ARRAY", 
                                "description": "List of fields to fetch (e.g., ['name', 'lead_name', 'status'])",
                                "items": {"type": "STRING"}
                            },
                            "limit": {"type": "INTEGER", "description": "Max number of records to return (default 10)"}
                        },
                        "required": ["doctype"]
                    }
                },
                {
                    "name": "get_doc",
                    "description": "Get full details of a specific record by name.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "doctype": {"type": "STRING", "description": "The DocType of the record"},
                            "name": {"type": "STRING", "description": "The name/ID of the record"}
                        },
                        "required": ["doctype", "name"]
                    }
                },
                {
                    "name": "create_doc",
                    "description": "Create a new record.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "doctype": {"type": "STRING", "description": "The DocType to create"},
                            "data": {"type": "OBJECT", "description": "The data for the new record"}
                        },
                        "required": ["doctype", "data"]
                    }
                },
                {
                    "name": "update_doc",
                    "description": "Update an existing record.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "doctype": {"type": "STRING", "description": "The DocType to update"},
                            "name": {"type": "STRING", "description": "The name/ID of the record"},
                            "data": {"type": "OBJECT", "description": "The data to update"}
                        },
                        "required": ["doctype", "name", "data"]
                    }
                },
                {
                    "name": "delete_doc",
                    "description": "Delete a record.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "doctype": {"type": "STRING", "description": "The DocType to delete"},
                            "name": {"type": "STRING", "description": "The name/ID of the record"}
                        },
                        "required": ["doctype", "name"]
                    }
                },
                {
                    "name": "get_meta",
                    "description": "Get metadata (fields) for a DocType to understand its schema and available fields.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "doctype": {"type": "STRING", "description": "The DocType to get metadata for"}
                        },
                        "required": ["doctype"]
                    }
                }
            ]
        }
    ]

    # Handle Chat Session Persistence
    stored_messages = []
    chat_doc = None
    
    if chat_id:
        try:
            chat_doc = frappe.get_doc("CRM AI Chat", chat_id)
            if chat_doc.user != frappe.session.user:
                frappe.throw("Not authorized")
            
            if chat_doc.messages:
                stored_messages = json.loads(chat_doc.messages)
        except Exception as e:
            print(f"Error loading chat session: {e}")
            # Fallback to new chat if ID invalid (shouldn't happen normally)
            chat_id = None

    # Append user message to stored messages
    stored_messages.append({"role": "user", "content": message})
    
    # Prepare history for AI (everything before the current message)
    # If it's a new chat, history is empty.
    # If it's an existing chat, history is the stored messages minus the last one.
    history_for_ai = stored_messages[:-1]

    # Initial Conversation History with System Prompt
    contents = [
        {
            "role": "user",
            "parts": [{"text": formatted_system_prompt}]
        },
        {
            "role": "model",
            "parts": [{"text": "Understood. I am ready to help with Frappe CRM tasks."}]
        }
    ]

    # Append history
    for msg in history_for_ai:
        role = "model" if msg.get("role") == "assistant" else "user"
        contents.append({
            "role": role,
            "parts": [{"text": msg.get("content")}]
        })

    # Append current message
    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    # Agent Loop (Max 15 turns to prevent infinite loops)
    final_response_text = ""
    
    for _ in range(15):
        payload = {
            "contents": contents,
            "tools": tools
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if not response.ok:
                print(f"Gemini API Error Response: {response.text}") # Print to stdout for debugging
                error_msg = f"Gemini API Error: {response.status_code} - {response.text}"
                frappe.log_error(message=error_msg, title="Gemini API Error")
                final_response_text = f"Error from AI provider: {response.status_code} - {response.text}"
                break

            result = response.json()
            
            if 'candidates' not in result or not result['candidates']:
                final_response_text = "I couldn't generate a response."
                break

            candidate = result['candidates'][0]
            content = candidate.get('content', {})
            parts = content.get('parts', [])

            if not parts:
                final_response_text = "Empty response from AI."
                break

            # Check for function calls
            function_calls = [part.get('functionCall') for part in parts if 'functionCall' in part]
            
            if function_calls:
                # Append model's response (function call) to history
                contents.append(content)
                
                # Execute function calls
                function_responses = []
                for fc in function_calls:
                    func_name = fc['name']
                    func_args = fc['args']
                    
                    func_result = execute_tool(func_name, func_args)
                    
                    function_responses.append({
                        "functionResponse": {
                            "name": func_name,
                            "response": {"result": func_result}
                        }
                    })
                
                # Append function results to history
                contents.append({
                    "role": "function",
                    "parts": function_responses
                })
                
                # Loop continues to send function results back to model
                continue
            else:
                # No function call, return the text response
                final_response_text = parts[0].get('text', '')
                break

        except Exception as e:
            print(f"Gemini Agent Exception: {str(e)}")
            frappe.log_error(message=f"Gemini Agent Exception: {str(e)}", title="Gemini Agent Exception")
            final_response_text = f"Error: {str(e)}"
            break
    
    if not final_response_text:
        final_response_text = "I reached the maximum number of steps without a final answer."

    # Append AI response to stored messages
    stored_messages.append({"role": "assistant", "content": final_response_text})
    
    # Save to DB
    if not chat_id:
        # Create new session
        # Generate title (simple truncation for now, can be improved)
        title = message[:50] + "..." if len(message) > 50 else message
        
        try:
            chat_doc = frappe.get_doc({
                "doctype": "CRM AI Chat",
                "user": frappe.session.user,
                "title": title,
                "messages": json.dumps(stored_messages)
            })
            chat_doc.insert(ignore_permissions=True)
            chat_id = chat_doc.name
            
            # Generate better title asynchronously or here
            # For now, let's try to generate a title if it's the first message
            # We can use a separate call to Gemini for title generation
            try:
                title_prompt = f"Generate a very short summary title (max 5 words) for this chat message: '{message}'"
                title_payload = {
                    "contents": [{"role": "user", "parts": [{"text": title_prompt}]}]
                }
                title_response = requests.post(url, headers=headers, json=title_payload)
                if title_response.ok:
                    title_result = title_response.json()
                    if 'candidates' in title_result and title_result['candidates']:
                        generated_title = title_result['candidates'][0]['content']['parts'][0]['text'].strip()
                        # Remove quotes if present
                        generated_title = generated_title.replace('"', '').replace("'", "")
                        chat_doc.title = generated_title
                        chat_doc.save(ignore_permissions=True)
            except Exception as e:
                print(f"Title generation failed: {e}")

        except Exception as e:
            print(f"Error creating chat session: {e}")
            # If table doesn't exist, we might fail here. 
            # But we return the response anyway so the user sees something.
            pass
    else:
        # Update existing session
        if chat_doc:
            chat_doc.messages = json.dumps(stored_messages)
            chat_doc.save(ignore_permissions=True)

    return {
        "response": final_response_text,
        "chat_id": chat_id
    }

def execute_tool(name, args):
    try:
        if name == "get_list":
            return tool_get_list(**args)
        elif name == "get_doc":
            return tool_get_doc(**args)
        elif name == "create_doc":
            return tool_create_doc(**args)
        elif name == "update_doc":
            return tool_update_doc(**args)
        elif name == "delete_doc":
            return tool_delete_doc(**args)
        elif name == "get_meta":
            return tool_get_meta(**args)
        else:
            return f"Error: Unknown function {name}"
    except Exception as e:
        return f"Error executing {name}: {str(e)}"

# Tool Implementations
def tool_get_list(doctype, filters=None, fields=None, limit=10):
    try:
        if filters:
            filters = get_safe_filters(filters)
        
        if not fields:
            fields = ["name"]
            
        docs = frappe.get_list(doctype, filters=filters, fields=fields, limit_page_length=limit)
        return frappe.as_json(docs)
    except Exception as e:
        return f"Error fetching list: {str(e)}"

def tool_get_doc(doctype, name):
    try:
        doc = frappe.get_doc(doctype, name)
        return frappe.as_json(doc.as_dict())
    except Exception as e:
        return f"Error fetching doc: {str(e)}"

def tool_create_doc(doctype, data):
    try:
        doc = frappe.get_doc({"doctype": doctype, **data})
        doc.insert(ignore_permissions=True)
        return f"Created {doctype}: {doc.name}"
    except Exception as e:
        return f"Error creating doc: {str(e)}"

def tool_update_doc(doctype, name, data):
    try:
        doc = frappe.get_doc(doctype, name)
        doc.update(data)
        doc.save(ignore_permissions=True)
        return f"Updated {doctype}: {doc.name}"
    except Exception as e:
        return f"Error updating doc: {str(e)}"

def tool_delete_doc(doctype, name):
    try:
        frappe.delete_doc(doctype, name, ignore_permissions=True)
        return f"Deleted {name}"
    except Exception as e:
        return f"Error deleting doc: {str(e)}"

def tool_get_meta(doctype):
    try:
        meta = frappe.get_meta(doctype)
        fields = []
        for df in meta.fields:
            fields.append({
                "fieldname": df.fieldname,
                "fieldtype": df.fieldtype,
                "label": df.label,
                "reqd": df.reqd,
                "options": df.options
            })
        return frappe.as_json(fields)
    except Exception as e:
        return f"Error fetching meta: {str(e)}"
