# seed_templates.py
from db import SessionLocal
from models import ChecklistTemplate, TemplateTask

# ─── helper ───────────────────────────────────────────────────────────────────

def add_tasks(template_id, tasks, category):
    for order, (tid, title, due, instr) in enumerate(tasks, start=1):
        yield TemplateTask(
            id=f"{template_id}_{tid}",
            template_id=template_id,
            title=title,
            category=category,
            relative_due=due,
            instructions=instr,
            order=f"{order:02}",
        )

# Task tuples: (id, title, relative_due, instructions)
off_league_pre = [
    ("review_reports", "Review previous year’s summary reports", "D-7", ""),
    ("email_officials", "Email past officials and new applicants", "D-28", ""),
    ("hire_officials", "Hire desired officials", "D-28", ""),
    ("create_goals", "Create goals on new summary report", "D-21", ""),
    ("schedule_pac", "Communicate with instructor and schedule PAC class appearance", "D-21", ""),
    ("coordinate_facilities", "Coordinate with any facilities/operations staff as needed", "D-14", ""),
    ("check_facility_reservation", "Check that all facility space is reserved in Mazevo and matches IMLeagues offerings", "D-14", ""),
    ("confirm_clinic", "Confirm officials clinic dates, times, and facilities", "D-14", ""),
    ("setup_zoom", "Set up Zoom manager’s meeting link and add to IMLeagues", "D-14", ""),
    ("check_equipment", "Make sure we have all equipment", "D-14", "Purchase right away if necessary."),
    ("review_rules", "Review rules and suggest changes", "D-7", "Submit to Macer/Tony. Upload to IMLeagues."),
    ("present_pac", "Attend and present to PAC class(es)", "D-23", ""),
    ("schedule_spas", "Schedule SPAs", "D-23", ""),
    ("message_participants", "Message past IM participants", "D-23", ""),
    ("create_meeting_slides", "Create manager’s meeting powerpoint", "D-23t:present_pac", ""),
    ("remind_meeting", "Send out reminder of manager’s meeting", "D+6t:create_meeting_slides", ""),
    ("check_sportclub_participation", "Run Sport Club participation in league check", "D+1t:remind_meeting", ""),
    ("meet_spas", "Meet with SPAs working League", "D+1t:remind_meeting", "Go over setup, teardown, and rules.")
]

off_league_post = [
    ("shirts_photos", "Distribute IM champs t-shirts, take photos of the championship teams", "D+1e", ""),
    ("notify_equipment", "Notify Macer/Tony of equipment that needs to be purchased", "D+1t:shirts_photos", ""),
    ("upload_photos", "Post playoff and champ photos on Flickr", "D+1t:shirts_photos", ""),
    ("add_photos_marketing", "Add champion photos to the Marketing folder", "D+1t:upload_photos", ""),
    ("update_tracker", "Update the Champion T-Shirts Tracker excel workbook", "D+1t:add_photos_marketing", ""),
    ("collect_jerseys", "Collect officials’ jerseys", "D+1t:update_tracker", "Submit names of people who didn’t return jersey to Macer."),
    ("summary_report", "Complete the summary report", "D+1t:collect_jerseys", "")
]

nonoff_league_pre = [
    ("review_reports", "Review previous year’s summary reports", "D-7", ""),
    ("schedule_pac", "Communicate with instructor and schedule PAC class appearance", "D-21", ""),
    ("coordinate_facilities", "Coordinate with any facilities/operations staff as needed", "D-14", ""),
    ("setup_zoom", "Set up Zoom manager’s meeting link and add to IMLeagues", "D-14", ""),
    ("check_facility_reservation", "Check that all facility space is reserved in Mazevo and it matches IMLeagues offerings", "D-14", ""),
    ("check_equipment", "Make sure we have all equipment", "D-14", "Purchase right away if necessary."),
    ("review_rules", "Review rules and suggest changes", "D-7", "Submit to Macer/Tony. Upload to IMLeagues."),
    ("present_pac", "Attend and present to PAC class(es)", "D-23", ""),
    ("schedule_spas", "Schedule SPAs", "D-23", ""),
    ("message_participants", "Message past IM participants", "D-23", ""),
    ("create_meeting_slides", "Create manager’s meeting powerpoint", "D-23t:present_pac", ""),
    ("remind_meeting", "Send out reminder of manager’s meeting", "D+6t:create_meeting_slides", ""),
    ("check_sportclub_participation", "Run Sport Club participation in league check", "D+1t:remind_meeting", ""),
    ("meet_spas", "Meet with SPAs working League at fields", "D+1t:remind_meeting", "Go over setup, teardown, and rules.")
]

nonoff_league_post = off_league_post[:-1] + [("summary_report", "Complete the summary report", "D+1t:update_tracker", "")]

off_event_pre = [
    ("review_reports", "Review previous year’s summary reports", "D-28", ""),
    ("email_officials", "Email past officials and new applicants", "D-28", ""),
    ("schedule_clinic", "Schedule officials’ clinic date and time and reserve a facility", "D-21", ""),
    ("schedule_pac", "Communicate with instructor and schedule PAC class appearance", "D-21", ""),
    ("coordinate_facilities", "Coordinate with any facilities/operations staff as needed", "D-14", ""),
    ("check_equipment", "Make sure we have all equipment", "D-14", "Purchase right away if necessary."),
    ("review_rules", "Review rules and suggest changes", "D-14", "Submit to Macer/Tony. Upload to IMLeagues."),
    ("schedule_spas", "Schedule SPAs", "D-14", ""),
    ("present_pac", "Attend and present to PAC class(es)", "D-7", ""),
    ("message_participants", "Message past IM participants", "D-7", ""),
    ("check_sportclub_participation", "Run Sport Club participation in league check", "D+1t:message_participants", "")
]

off_event_post = off_league_post

nonoff_event_pre = [
    ("review_reports", "Review previous year’s summary reports", "D-28", ""),
    ("create_goals", "Create Goals for your event on new summary report", "D-21", ""),
    ("schedule_pac", "Communicate with instructor and schedule PAC class appearance", "D-21", ""),
    ("coordinate_facilities", "Coordinate with any facilities/operations staff as needed", "D-14", ""),
    ("check_equipment", "Make sure we have all equipment", "D-14", "Purchase right away if necessary."),
    ("review_rules", "Review rules and suggest changes", "D-14", "Submit to Macer/Tony. Upload to IMLeagues."),
    ("schedule_spas", "Schedule SPAs", "D-14", ""),
    ("present_pac", "Attend and present to PAC class(es)", "D-7", ""),
    ("message_participants", "Message past IM participants", "D-7", ""),
    ("check_sportclub_participation", "Run Sport Club participation in league check", "D+1t:message_participants", "")
]

nonoff_event_post = nonoff_league_post

TEMPLATES = {
    "officiated_league":  ("Officiated League Checklist",    off_league_pre,  off_league_post),
    "nonofficiated_league":("Non-officiated League Checklist", nonoff_league_pre, nonoff_league_post),
    "officiated_event":   ("Officiated Event Checklist",     off_event_pre,   off_event_post),
    "nonofficiated_event":("Non-officiated Event Checklist", nonoff_event_pre, nonoff_event_post),
}

with SessionLocal() as db:
    for tid, (name, pre, post) in TEMPLATES.items():
        if db.get(ChecklistTemplate, tid):
            print(f"Template {tid} already exists → skip")
            continue
        tmpl = ChecklistTemplate(id=tid, name=name)
        tmpl.tasks = [
            *add_tasks(tid, pre,  "Pre-League" if "league" in tid else "Pre-Event"),
            *add_tasks(tid, post, "Post-League" if "league" in tid else "Post-Event"),
        ]
        db.add(tmpl)
        print("Inserted", name, "with", len(tmpl.tasks), "tasks")
    db.commit()
