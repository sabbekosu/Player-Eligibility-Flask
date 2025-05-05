# seed_clubs.py
from db import SessionLocal
from models import Club

# List of clubs extracted from index.html JavaScript
# Exclude 'Other' as it's not a real club for allocation
CLUB_NAMES = [
    "Archery Club", "Badminton Club", "Baseball Club", "Cycling Club",
    "Disc Golf Club", "Dodgeball Club", "Equestrain Dressage Club",
    "Equestrian Event", "Equestrian Hunter-Jumper", "Equestrian Polo Club",
    "Fishing Club", "Gymnastics Club", "Indoor Rock Climbing",
    "Intercollegiate Horse Show Association", # Note: Typo 'Assosiation' kept if that's the official name used
    "Judo Club", "Karate Club", "Kendo Club", "Marksmanship Club",
    "Men's Lacrosse Club", "Men's Rugby Club", "Men's Soccer Club",
    "Men's Ultimate Disc Club", "Men's Volleyball Club", "Men's Water Polo Club",
    "Pistol Club", "Racquetball Club", "Rifle Club", "Running Club",
    "Sailing Club", "Stock Horse Club", "Swim Club", "Table Tennis Club",
    "Tennis Club", "Triathlon Club", "Women's Lacrosse Club",
    "Women's Rugby Club", "Women's Soccer Club", "Women's Ultimate Disc Club",
    "Women's Volleyball Club", "Women's Water Polo Club"
]

def seed_initial_clubs():
    """Adds the initial list of clubs to the database if they don't exist."""
    print("Seeding initial sports clubs...")
    added_count = 0
    skipped_count = 0
    with SessionLocal() as db:
        existing_clubs = {c.name.lower() for c in db.query(Club.name).all()} # Get existing names (lowercase)

        for name in CLUB_NAMES:
            if name.lower() not in existing_clubs:
                new_club = Club(name=name, is_active=True)
                db.add(new_club)
                print(f"  Adding: {name}")
                added_count += 1
            else:
                # print(f"  Skipping (already exists): {name}")
                skipped_count += 1

        if added_count > 0:
            try:
                db.commit()
                print(f"✅ Successfully added {added_count} new clubs.")
            except Exception as e:
                db.rollback()
                print(f"❌ Error committing new clubs: {e}")
        else:
            print(f"✅ No new clubs to add ({skipped_count} already exist).")

if __name__ == "__main__":
    # Ensure tables exist first (models.py should handle this on import)
    # import models # noqa
    seed_initial_clubs()

