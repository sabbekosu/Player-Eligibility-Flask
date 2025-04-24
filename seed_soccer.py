# seed_soccer.py
from datetime import date
from db import SessionLocal
from models import League, Task

# ── helper ───────────────────────────────────────────────────────────────────
def add_task(lst, lid, cat):
    for _id, title, due_str, instr in lst:
        mm = due_str.split()[0] if due_str[0].isdigit() else None
        task = Task(
            id=_id,
            league_id=lid,
            title=title,
            category=cat,
            due=None,        # store text date in instructions or add parser
            order=_id,       # simple alpha order
            instructions=f"(Due {due_str}) — {instr}",
        )
        yield task

pre = [
    ("review_reports","Review previous year's summary reports","1 week before registration opens",
     "Locate last year's summary reports in the shared drive, read key findings, and write down 2-3 improvement goals."),
    ("email_officials","Email past officials and new applicants","4 weeks before officials training",
     "Send the invitation email template to returning & prospective officials."),
    ("hire_officials","Hire desired officials","4 weeks before first games",
     "Confirm hiring decisions in IMLeagues and send offer letters."),
    ("create_goals","Create goals on new summary report","3 weeks before event",
     "Open blank summary report and fill measurable goals."),
    ("schedule_pac","Communicate with instructor & schedule PAC appearance","3 weeks before reg deadline",
     "Email PAC213 instructor to book 10-minute class pitch."),
    ("check_facilities","Coordinate with facilities/ops staff","2 weeks before reg deadline",
     "Verify field lining and lights schedule."),
    ("mazevo_reserve","Reserve space in Mazevo","2 weeks before officials training",
     "Ensure every match slot in Mazevo matches IMLeagues."),
    ("confirm_clinic","Confirm officials clinic details","2 weeks before officials training",
     "Verify room booking and remind presenters."),
    ("setup_zoom","Set up Zoom manager's meeting link","2 weeks before reg deadline",
     "Create Zoom and paste link in IMLeagues."),
    ("equipment","Ensure we have all equipment","2 weeks before games start",
     "Inventory balls, cones; raise PO if needed."),
    ("rules_review","Review & upload rules","1 week before officials training",
     "Update rule tweaks, upload PDF to IMLeagues."),
    ("attend_pac","Attend and present to PAC class(es)","End of week 1",
     "Deliver 10-minute presentation & collect interest list."),
    ("schedule_spas","Schedule SPAs","End of week 1","Create shifts in WhenToWork."),
    ("message_past","Message past participants","End of week 1","Bulk-message last year's teams."),
    ("managers_ppt","Create manager's meeting powerpoint","Friday of week 1",
     "Duplicate last term's deck, update dates."),
    ("reminder_managers","Send reminder of manager's meeting","Day before meeting",
     "Send one-click email in IMLeagues."),
    ("club_check","Run Sport Club participation check","Registration deadline",
     "Use club eligibility checker tool."),
    ("meet_spas","Meet SPAs at fields/courts","Registration deadline",
     "Walk SPAs through setup and teardown."),
]

post = [
    ("shirts_photos","Distribute champ shirts & take photos","After final","Hand shirts, shoot photo, upload to Flickr."),
    ("equip_needs","Notify Macer/Tony of equipment needs","After final","Email replacement list."),
    ("post_photos","Post playoff & champ photos on Flickr","After final","Tag and add to album."),
    ("add_marketing","Add champ photos to Marketing folder","After final","Copy originals to Marketing/Champions/<term>."),
    ("update_tracker","Update Champion T-Shirt Tracker","After final","Update Google Sheet quantities."),
    ("collect_jerseys","Collect officials' jerseys","After final","Check-in list; invoice missing jerseys."),
    ("summary_report","Complete the summary report","After final","Finish summary and share with supervisor."),
]

with SessionLocal() as db:
    if db.get(League, "soccer"):
        print("Soccer League already exists – abort seeding.")
        exit()

    soccer = League(id="soccer", name="Soccer League")
    soccer.tasks = [
        *add_task(pre, "soccer", "Pre-League"),
        *add_task(post, "soccer", "Post-League"),
    ]
    db.add(soccer)
    db.commit()
    print("✅ Soccer League seeded with", len(soccer.tasks), "tasks.")
