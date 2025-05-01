# seed_templates.py
from db import SessionLocal
from models import ChecklistTemplate, TemplateTask

# ─── helper ───────────────────────────────────────────────────────────────────

def add_tasks(template_id, tasks_data, category):
    """
    Adds TemplateTask objects to be yielded.
    tasks_data is now a list of dictionaries, where each dict contains
    all necessary fields for a TemplateTask.
    """
    for order, task_dict in enumerate(tasks_data, start=1):
        # Ensure required fields are present
        if not all(k in task_dict for k in ['task_ref_id', 'title', 'relative_due']):
            print(f"Skipping task in {template_id} due to missing required fields: {task_dict}")
            continue

        # Construct the full TemplateTask ID
        full_template_task_id = f"{template_id}_{task_dict['task_ref_id']}"

        yield TemplateTask(
            id=full_template_task_id, # Use combined ID
            template_id=template_id,
            task_ref_id=task_dict['task_ref_id'], # Store the reference ID
            title=task_dict['title'],
            category=category,
            relative_due=task_dict['relative_due'],
            instructions=task_dict.get('instructions', None), # Use .get for optional fields
            order=f"{order:02}",

            # Add ALL new fields, using .get() for safety
            link_1_url=task_dict.get('link_1_url'),
            link_1_label=task_dict.get('link_1_label'),
            link_2_url=task_dict.get('link_2_url'),
            link_2_label=task_dict.get('link_2_label'),
            notes=task_dict.get('notes'),
            contact_info=task_dict.get('contact_info'),
            email_template_subject=task_dict.get('email_template_subject'),
            email_template_body=task_dict.get('email_template_body'),
            email_recipient_source=task_dict.get('email_recipient_source'),
            email_target_address=task_dict.get('email_target_address'),
            previous_report_link=task_dict.get('previous_report_link'),
            improvement_goals=task_dict.get('improvement_goals'),
            imleagues_staff_link=task_dict.get('imleagues_staff_link'),
            offer_letter_template=task_dict.get('offer_letter_template'),
            report_template_link=task_dict.get('report_template_link'),
            pac_instructor_contact=task_dict.get('pac_instructor_contact'),
            facilities_contact=task_dict.get('facilities_contact'),
            facilities_booking_link=task_dict.get('facilities_booking_link'),
            facilities_email_templates=task_dict.get('facilities_email_templates'),
            imleagues_schedule_link=task_dict.get('imleagues_schedule_link'),
            clinic_booking_link=task_dict.get('clinic_booking_link'),
            zoom_meeting_link=task_dict.get('zoom_meeting_link'),
            imleagues_paste_location_link=task_dict.get('imleagues_paste_location_link'),
            inventory_list_link=task_dict.get('inventory_list_link'),
            equipment_notes=task_dict.get('equipment_notes'),
            rules_doc_link=task_dict.get('rules_doc_link'),
            imleagues_rules_upload_link=task_dict.get('imleagues_rules_upload_link'),
            presentation_slides_link=task_dict.get('presentation_slides_link'),
            interest_list_link=task_dict.get('interest_list_link'),
            whentowork_link=task_dict.get('whentowork_link'),
            imleagues_messaging_link=task_dict.get('imleagues_messaging_link'),
            participant_message_templates=task_dict.get('participant_message_templates'),
            slides_template_link=task_dict.get('slides_template_link'),
            captain_quiz_link=task_dict.get('captain_quiz_link'),
            imleagues_email_link=task_dict.get('imleagues_email_link'),
            spa_meeting_docs_link=task_dict.get('spa_meeting_docs_link'),
            shirt_tracker_link=task_dict.get('shirt_tracker_link'),
            flickr_link=task_dict.get('flickr_link'),
            marketing_folder_link=task_dict.get('marketing_folder_link'),
            jersey_checkin_link=task_dict.get('jersey_checkin_link'),
            summary_report_template_link=task_dict.get('summary_report_template_link'),
            summary_report_draft=task_dict.get('summary_report_draft'),
        )

# ─── Task Data (Now as dictionaries) ─────────────────────────────────────────
# Define common values
DEFAULT_IMLEAGUES_LOGIN = "https://imleagues.com/Login" # Example placeholder
DEFAULT_MAZEVO_LOGIN = "https://osu.mazevo.com/" # Example placeholder
DEFAULT_WHENTOWORK_LOGIN = "https://whentowork.com/logins.htm" # Example placeholder
DEFAULT_FLICKR_UPLOAD = "https://www.flickr.com/photos/oregonstateurecsports/albums" # Example
DEFAULT_SHIRT_TRACKER = "S:\\Facility & Equipment\\Equipment Inventory\\SP\\Champion T-Shirt Tracker.xlsx" # Example S: drive path
DEFAULT_MARKETING_FOLDER = "S:\\Marketing\\Program Pictures\\Intramural Sports Photos\\{YEAR}" # Example S: drive path with placeholder
MACER_TONY_EMAIL = "macer.tony@example.com" # Replace with actual email
PAC_INSTRUCTOR_EMAIL = "pac.instructor@example.com" # Replace with actual email
FACILITIES_CONTACT_EMAIL = "facilities.contact@example.com" # Replace with actual email

# --- Officiated League ---
off_league_pre = [
    {'task_ref_id': "review_reports", 'title': "Review previous year’s summary reports", 'relative_due': "D-7", 'instructions': "Locate report on S: drive, note 2-3 goals.", 'previous_report_link': "S:\\Path\\To\\Reports\\{YEAR-1}\\{LeagueName}_Summary.docx", 'improvement_goals': "1. \n2. \n3. "},
    {'task_ref_id': "email_officials", 'title': "Email past officials and new applicants", 'relative_due': "D-28", 'instructions': "Use template to invite returning & new officials.", 'email_recipient_source': "Handshake Applicants / Past Official List (S:\\...)", 'email_template_subject': "Officiating Opportunity: {LeagueName} {Season}", 'email_template_body': "Hi [Official Name],\n\nWe're looking for officials for the upcoming {LeagueName} season...\n\n[Link to application/interest form]\n\nThanks,\n[Your Name]"},
    {'task_ref_id': "hire_officials", 'title': "Hire desired officials", 'relative_due': "D-28", 'instructions': "Confirm in IMLeagues, send offer letters.", 'imleagues_staff_link': DEFAULT_IMLEAGUES_LOGIN, 'offer_letter_template': "Congratulations...\nYou have been selected...\n[Details]..."},
    {'task_ref_id': "create_goals", 'title': "Create goals on new summary report", 'relative_due': "D-21", 'instructions': "Fill in measurable goals section.", 'report_template_link': "S:\\Path\\To\\Templates\\Summary_Report_Template.docx"},
    {'task_ref_id': "schedule_pac", 'title': "Communicate with instructor and schedule PAC class appearance", 'relative_due': "D-21", 'instructions': "Email instructor to book 10-min pitch.", 'pac_instructor_contact': f"Instructor Name ({PAC_INSTRUCTOR_EMAIL})", 'email_template_subject': "Request to Present to PAC Class - IM {LeagueName}", 'email_template_body': "Hi [Instructor Name],\n\nCould I please schedule a brief 10-minute presentation about the upcoming Intramural {LeagueName} season in your PAC class?\n\nAvailable dates/times...\n\nThanks,\n[Your Name]"},
    {'task_ref_id': "coordinate_facilities", 'title': "Coordinate with facilities/operations staff as needed", 'relative_due': "D-14", 'instructions': "Verify field lining, lights, setup needs.", 'facilities_contact': f"Facilities Dept ({FACILITIES_CONTACT_EMAIL})", 'facilities_booking_link': DEFAULT_MAZEVO_LOGIN, 'facilities_email_templates': "Subject: Field Lining Request - {LeagueName}\nBody:...\n---\nSubject: Light Schedule Check - {LeagueName}\nBody:..."},
    {'task_ref_id': "check_facility_reservation", 'title': "Check Mazevo reservations match IMLeagues offerings", 'relative_due': "D-14", 'instructions': "Verify all game slots match.", 'facilities_booking_link': DEFAULT_MAZEVO_LOGIN, 'imleagues_schedule_link': DEFAULT_IMLEAGUES_LOGIN},
    {'task_ref_id': "confirm_clinic", 'title': "Confirm officials clinic dates, times, and facilities", 'relative_due': "D-14", 'instructions': "Verify room booking, remind presenters.", 'clinic_booking_link': DEFAULT_MAZEVO_LOGIN, 'email_template_subject': "Confirmation: Officials Clinic for {LeagueName}", 'email_template_body': "Hi [Presenter Name],\n\nJust confirming the details for the {LeagueName} officials clinic:\nDate: [Date]\nTime: [Time]\nLocation: [Location]\n\nThanks,\n[Your Name]"},
    {'task_ref_id': "setup_zoom", 'title': "Set up Zoom manager’s meeting link and add to IMLeagues", 'relative_due': "D-14", 'instructions': "Create meeting, paste link in IMLeagues description.", 'imleagues_paste_location_link': DEFAULT_IMLEAGUES_LOGIN, 'notes': "Remember to set waiting room/passcode."},
    {'task_ref_id': "check_equipment", 'title': "Make sure we have all equipment", 'relative_due': "D-14", 'instructions': "Inventory items, create PO if needed.", 'inventory_list_link': "S:\\Path\\To\\Inventory\\{Sport}_Inventory.xlsx", 'email_target_address': MACER_TONY_EMAIL, 'email_template_subject': "Purchase Request - {LeagueName} Equipment", 'email_template_body': "Hi Macer/Tony,\n\nWe need the following equipment for {LeagueName}:\n- [Item 1] (Quantity: [Num])\n- [Item 2] (Quantity: [Num])\n\nThanks,\n[Your Name]", 'equipment_notes': "Check condition of [Specific Item]."},
    {'task_ref_id': "review_rules", 'title': "Review rules and suggest changes", 'relative_due': "D-7", 'instructions': "Update rules doc, submit changes, upload PDF to IMLeagues.", 'rules_doc_link': "S:\\Path\\To\\Rules\\{Sport}_Rules.docx", 'imleagues_rules_upload_link': DEFAULT_IMLEAGUES_LOGIN, 'notes': "Submit suggested changes to Macer/Tony."},
    {'task_ref_id': "present_pac", 'title': "Attend and present to PAC class(es)", 'relative_due': "D-23", 'instructions': "Deliver 10-min presentation, collect interest list.", 'presentation_slides_link': "S:\\Path\\To\\Presentations\\PAC_Pitch_{Season}.pptx", 'interest_list_link': "[Link to Google Form/Sheet]"},
    {'task_ref_id': "schedule_spas", 'title': "Schedule SPAs", 'relative_due': "D-23", 'instructions': "Create shifts in WhenToWork.", 'whentowork_link': DEFAULT_WHENTOWORK_LOGIN},
    {'task_ref_id': "message_participants", 'title': "Message past IM participants", 'relative_due': "D-23", 'instructions': "Use IMLeagues marketing tool.", 'imleagues_messaging_link': DEFAULT_IMLEAGUES_LOGIN, 'participant_message_templates': "Subject: Get Ready for {LeagueName}!\nBody: Sign up now for..."},
    {'task_ref_id': "create_meeting_slides", 'title': "Create manager’s meeting powerpoint", 'relative_due': "D-23t:present_pac", 'instructions': "Duplicate last term's deck, update dates/quiz link.", 'slides_template_link': "S:\\Path\\To\\Presentations\\Managers_Meeting_Template.pptx", 'captain_quiz_link': "[Link to Captain Quiz]"},
    {'task_ref_id': "remind_meeting", 'title': "Send out reminder of manager’s meeting", 'relative_due': "D+6t:create_meeting_slides", 'instructions': "One-click email in IMLeagues.", 'imleagues_email_link': DEFAULT_IMLEAGUES_LOGIN, 'email_template_subject': "Reminder: {LeagueName} Manager's Meeting Tomorrow!", 'email_template_body': "Hi Captains,\n\nJust a reminder about the mandatory manager's meeting tomorrow at [Time] via Zoom: [Zoom Link]\n\nSee you there,\n[Your Name]"},
    {'task_ref_id': "check_sportclub_participation", 'title': "Run Sport Club participation check", 'relative_due': "D+1t:remind_meeting", 'instructions': "Use eligibility checker tool.", 'link_1_url': "/eligibility", 'link_1_label': "Open Eligibility Checker"}, # Link to internal tool
    {'task_ref_id': "meet_spas", 'title': "Meet with SPAs working League", 'relative_due': "D+1t:remind_meeting", 'instructions': "Go over setup, teardown, and rules.", 'whentowork_link': DEFAULT_WHENTOWORK_LOGIN, 'spa_meeting_docs_link': "S:\\Path\\To\\SPA\\Checklists\\{Sport}_Checklist.docx"}
]

off_league_post = [
    {'task_ref_id': "shirts_photos", 'title': "Distribute IM champs t-shirts, take photos", 'relative_due': "D+1e", 'instructions': "Hand out shirts, take photos, upload to Flickr.", 'shirt_tracker_link': DEFAULT_SHIRT_TRACKER, 'flickr_link': DEFAULT_FLICKR_UPLOAD},
    {'task_ref_id': "notify_equipment", 'title': "Notify Macer/Tony of equipment needs", 'relative_due': "D+1t:shirts_photos", 'instructions': "Email replacement list based on season notes.", 'email_target_address': MACER_TONY_EMAIL, 'email_template_subject': "Equipment Needs Post-Season - {LeagueName}", 'email_template_body': "Hi Macer/Tony,\n\nBased on the {LeagueName} season, we should order/replace:\n- [Item from equipment_notes]\n\nThanks,\n[Your Name]"},
    {'task_ref_id': "upload_photos", 'title': "Post playoff & champ photos on Flickr", 'relative_due': "D+1t:shirts_photos", 'instructions': "Tag photos and add to album.", 'flickr_link': DEFAULT_FLICKR_UPLOAD},
    {'task_ref_id': "add_photos_marketing", 'title': "Add champion photos to Marketing folder", 'relative_due': "D+1t:upload_photos", 'instructions': "Copy originals to Marketing/Champions/<term>.", 'marketing_folder_link': DEFAULT_MARKETING_FOLDER},
    {'task_ref_id': "update_tracker", 'title': "Update Champion T-Shirts Tracker", 'relative_due': "D+1t:add_photos_marketing", 'instructions': "Update Google Sheet/Excel quantities.", 'shirt_tracker_link': DEFAULT_SHIRT_TRACKER},
    {'task_ref_id': "collect_jerseys", 'title': "Collect officials’ jerseys", 'relative_due': "D+1t:update_tracker", 'instructions': "Use check-in list; submit non-returners to Macer.", 'jersey_checkin_link': "[Link to Check-in Form/Sheet]", 'email_target_address': MACER_TONY_EMAIL, 'email_template_subject': "Unreturned Jerseys - {LeagueName}", 'email_template_body': "Hi Macer,\n\nThe following officials have not returned their jerseys for {LeagueName}:\n- [Name 1]\n- [Name 2]\n\nThanks,\n[Your Name]"},
    {'task_ref_id': "summary_report", 'title': "Complete the summary report", 'relative_due': "D+1t:collect_jerseys", 'instructions': "Fill out report using template and season data.", 'summary_report_template_link': "S:\\Path\\To\\Templates\\Summary_Report_Template.docx", 'summary_report_draft': "# Summary Report Snippets\n## Goals:\n{improvement_goals}\n## Equipment Notes:\n{equipment_notes}\n## Challenges:\n[Enter challenges]\n## Recommendations:\n[Enter recommendations]"}
]

# --- Non-Officiated League ---
# (Starts similar to officiated, remove official-specific tasks)
nonoff_league_pre = [
    t for t in off_league_pre if t['task_ref_id'] not in [
        "email_officials", "hire_officials", "confirm_clinic"
    ]
]
# Adjust dependencies if needed (e.g., if a removed task was a dependency)
# Example: create_meeting_slides depends on present_pac (kept) - OK
# Example: remind_meeting depends on create_meeting_slides (kept) - OK
# Example: check_sportclub... depends on remind_meeting (kept) - OK
# Example: meet_spas depends on remind_meeting (kept) - OK

nonoff_league_post = [
    t for t in off_league_post if t['task_ref_id'] not in ["collect_jerseys"]
]
# Adjust dependencies: summary_report depended on collect_jerseys (removed)
# Find the task before collect_jerseys: update_tracker
for task in nonoff_league_post:
    if task['task_ref_id'] == 'summary_report':
        task['relative_due'] = 'D+1t:update_tracker' # Adjust dependency


# --- Officiated Event ---
# (Similar to Officiated League, but timings might differ, fewer tasks)
off_event_pre = [
    {'task_ref_id': "review_reports", 'title': "Review previous year’s summary reports", 'relative_due': "D-28", 'instructions': "Locate report, note goals.", 'previous_report_link': "S:\\Path\\To\\Reports\\{YEAR-1}\\{EventName}_Summary.docx"},
    {'task_ref_id': "email_officials", 'title': "Email past officials and new applicants", 'relative_due': "D-28", 'instructions': "Invite officials.", 'email_recipient_source': "Past Official List", 'email_template_subject': "Officiating Opportunity: {EventName}", 'email_template_body': "..." }, # Shortened body
    {'task_ref_id': "schedule_clinic", 'title': "Schedule officials’ clinic date/time & reserve facility", 'relative_due': "D-21", 'instructions': "Book room via Mazevo.", 'clinic_booking_link': DEFAULT_MAZEVO_LOGIN},
    {'task_ref_id': "schedule_pac", 'title': "Communicate with instructor and schedule PAC class appearance", 'relative_due': "D-21", 'instructions': "Email instructor.", 'pac_instructor_contact': f"Instructor ({PAC_INSTRUCTOR_EMAIL})", 'email_template_subject': "Request to Present to PAC Class - IM {EventName}", 'email_template_body': "..."},
    {'task_ref_id': "coordinate_facilities", 'title': "Coordinate with facilities/operations staff", 'relative_due': "D-14", 'instructions': "Confirm setup needs.", 'facilities_contact': f"Facilities ({FACILITIES_CONTACT_EMAIL})", 'facilities_booking_link': DEFAULT_MAZEVO_LOGIN},
    {'task_ref_id': "check_equipment", 'title': "Make sure we have all equipment", 'relative_due': "D-14", 'instructions': "Inventory, request purchase if needed.", 'inventory_list_link': "S:\\...", 'email_target_address': MACER_TONY_EMAIL, 'email_template_subject': "Purchase Request - {EventName}", 'email_template_body': "..."},
    {'task_ref_id': "review_rules", 'title': "Review rules and suggest changes", 'relative_due': "D-14", 'instructions': "Update doc, submit, upload PDF.", 'rules_doc_link': "S:\\...", 'imleagues_rules_upload_link': DEFAULT_IMLEAGUES_LOGIN, 'notes': "Submit changes to Macer/Tony."},
    {'task_ref_id': "schedule_spas", 'title': "Schedule SPAs", 'relative_due': "D-14", 'instructions': "Create shifts in WhenToWork.", 'whentowork_link': DEFAULT_WHENTOWORK_LOGIN},
    {'task_ref_id': "present_pac", 'title': "Attend and present to PAC class(es)", 'relative_due': "D-7", 'instructions': "Deliver presentation.", 'presentation_slides_link': "S:\\..."},
    {'task_ref_id': "message_participants", 'title': "Message past IM participants", 'relative_due': "D-7", 'instructions': "Use IMLeagues marketing tool.", 'imleagues_messaging_link': DEFAULT_IMLEAGUES_LOGIN, 'participant_message_templates': "Sign up for {EventName}!"},
    {'task_ref_id': "check_sportclub_participation", 'title': "Run Sport Club participation check", 'relative_due': "D+1t:message_participants", 'instructions': "Use eligibility checker.", 'link_1_url': "/eligibility", 'link_1_label': "Open Eligibility Checker"}
]
off_event_post = off_league_post # Same post-tasks for officiated event

# --- Non-Officiated Event ---
nonoff_event_pre = [
    t for t in off_event_pre if t['task_ref_id'] not in [
        "email_officials", "schedule_clinic"
    ]
]
# Adjust dependencies: check_sportclub depended on message_participants (kept) - OK

nonoff_event_post = nonoff_league_post # Same post-tasks for non-officiated event


# --- Template Definitions ---
TEMPLATES = {
    # ID: (Name, Pre Tasks List, Post Tasks List)
    "officiated_league":    ("Officiated League Checklist",    off_league_pre,  off_league_post),
    "nonofficiated_league": ("Non-officiated League Checklist", nonoff_league_pre, nonoff_league_post),
    "officiated_event":     ("Officiated Event Checklist",     off_event_pre,   off_event_post),
    "nonofficiated_event":  ("Non-officiated Event Checklist", nonoff_event_pre, nonoff_event_post),
}

# --- Seeding Logic ---
with SessionLocal() as db:
    existing_templates = {t.id for t in db.query(ChecklistTemplate.id).all()}
    existing_tasks = {t.id for t in db.query(TemplateTask.id).all()}
    added_count = 0
    task_added_count = 0

    for tid, (name, pre, post) in TEMPLATES.items():
        if tid not in existing_templates:
            tmpl = ChecklistTemplate(id=tid, name=name)
            db.add(tmpl)
            print(f"Adding Template: {name} ({tid})")
            added_count += 1
        else:
            # Optionally update the name if it changed
            # db.query(ChecklistTemplate).filter_by(id=tid).update({"name": name})
            # print(f"Template {tid} already exists.")
            pass # Silently skip if exists

        # Determine categories based on template ID
        pre_cat = "Pre-Event" if "event" in tid else "Pre-League"
        post_cat = "Post-Event" if "event" in tid else "Post-League"

        # Add or update tasks
        for task in add_tasks(tid, pre, pre_cat):
             if task.id not in existing_tasks:
                 db.add(task)
                 task_added_count += 1
             else:
                 # Optionally update existing tasks here if needed
                 # db.merge(task) # Merge can update existing based on PK
                 pass
        for task in add_tasks(tid, post, post_cat):
             if task.id not in existing_tasks:
                 db.add(task)
                 task_added_count += 1
             else:
                 # db.merge(task)
                 pass

    if added_count > 0 or task_added_count > 0:
        try:
            db.commit()
            print(f"✅ Seeding complete. Added {added_count} templates and {task_added_count} tasks.")
        except Exception as e:
            db.rollback()
            print(f"❌ Error during seeding commit: {e}")
    else:
        print("✅ No new templates or tasks to seed.")

