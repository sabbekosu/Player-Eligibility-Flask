# seed_clubs.py
from db import SessionLocal
from models import Club
from sqlalchemy.exc import IntegrityError

# Define the list of clubs with their active status
# True = Active, False = Inactive
clubs_to_seed = [
    # --- Active Clubs (Based on user list) ---
    {"name": "Archery Club", "is_active": True},
    {"name": "Badminton Club", "is_active": True}, # Added
    {"name": "Baseball Club", "is_active": True},
    {"name": "Cycling Club", "is_active": True},
    {"name": "Disc Golf Club", "is_active": True}, # Renamed
    {"name": "Dodgeball Club", "is_active": True}, # Renamed
    {"name": "Equestrain Dressage Club", "is_active": True}, # Renamed (Note: Typo in 'Equestrian'?)
    {"name": "Equestrian Event", "is_active": True}, # Renamed
    {"name": "Equestrian Hunter-Jumper", "is_active": True}, # Renamed
    {"name": "Equestrian Polo Club", "is_active": True}, # Renamed
    {"name": "Fishing Club", "is_active": True}, # Renamed (was Bass Fishing)
    {"name": "Gymnastics Club", "is_active": True},
    {"name": "Indoor Rock Climbing", "is_active": True},
    {"name": "Intercollegiate Horse Show Association", "is_active": True}, # Renamed (was IHSA Equestrian)
    {"name": "Judo Club", "is_active": True},
    {"name": "Karate Club", "is_active": True}, # Added
    {"name": "Kendo Club", "is_active": True}, # Renamed
    {"name": "Marksmanship Club", "is_active": True}, # Added
    {"name": "Men's Lacrosse Club", "is_active": True}, # Renamed
    {"name": "Men's Rugby Club", "is_active": True}, # Renamed
    {"name": "Men's Soccer Club", "is_active": True}, # Renamed
    {"name": "Men's Ultimate Disc Club", "is_active": True},
    {"name": "Men's Volleyball Club", "is_active": True}, # Renamed
    {"name": "Men's Water Polo Club", "is_active": True},
    {"name": "Pistol Club", "is_active": True}, # Renamed
    {"name": "Racquetball Club", "is_active": True},
    {"name": "Rifle Club", "is_active": True},
    {"name": "Running Club", "is_active": True},
    {"name": "Sailing Club", "is_active": True},
    {"name": "Sport Club Program", "is_active": True}, # Kept from previous update
    {"name": "Stock Horse Club", "is_active": True}, # Renamed
    {"name": "Swim Club", "is_active": True}, # Added
    {"name": "Table Tennis Club", "is_active": True},
    {"name": "Taekwondo Club", "is_active": True},
    {"name": "Tennis Club", "is_active": True}, # Kept separate active one
    {"name": "Triathlon Club", "is_active": True},
    {"name": "Women's Lacrosse Club", "is_active": True}, # Renamed
    {"name": "Women's Rugby Club", "is_active": True}, # Renamed
    {"name": "Women's Soccer Club", "is_active": True}, # Renamed
    {"name": "Women's Ultimate Disc Club", "is_active": True}, # Renamed (was Women's Ultimate)
    {"name": "Women's Volleyball Club", "is_active": True}, # Renamed
    {"name": "Women's Water Polo Club", "is_active": True}, # Renamed (was Women's Water Polo)

    # --- Inactive Clubs (Based on previous request) ---
    {"name": "Bowling Club", "is_active": False},
    {"name": "Equestrian Drill", "is_active": False},
    {"name": "OSU Tennis Club", "is_active": False}, # Kept separate inactive one

]

def seed_clubs():
    """Seeds the database with the defined list of clubs and their active status."""
    print("Seeding clubs...")
    with SessionLocal() as db:
        added_count = 0
        updated_count = 0
        skipped_count = 0

        # Get existing clubs to check for updates
        existing_clubs = {club.name: club for club in db.query(Club).all()}
        # Keep track of names in the seed list to potentially deactivate others
        seeded_club_names = {club_data["name"] for club_data in clubs_to_seed}

        for club_data in clubs_to_seed:
            club_name = club_data["name"]
            is_active = club_data["is_active"]

            if club_name in existing_clubs:
                # Club exists, check if status needs updating
                existing_club = existing_clubs[club_name]
                if existing_club.is_active != is_active:
                    print(f"  Updating status for '{club_name}' to {'Active' if is_active else 'Inactive'}")
                    existing_club.is_active = is_active
                    updated_count += 1
                else:
                    # print(f"  Skipping '{club_name}' - already exists with correct status.")
                    skipped_count += 1
            else:
                # Club does not exist, add it
                print(f"  Adding new club: '{club_name}' (Status: {'Active' if is_active else 'Inactive'})")
                new_club = Club(name=club_name, is_active=is_active)
                db.add(new_club)
                added_count += 1

        # Optional: Deactivate clubs in DB that are NOT in the new seed list
        # for existing_name, existing_club_obj in existing_clubs.items():
        #     if existing_name not in seeded_club_names and existing_club_obj.is_active:
        #         print(f"  Deactivating club '{existing_name}' (not in current seed list).")
        #         existing_club_obj.is_active = False
        #         updated_count += 1 # Count this as an update


        try:
            db.commit()
            print(f"Club seeding complete. Added: {added_count}, Updated: {updated_count}, Skipped: {skipped_count}")
        except IntegrityError as e:
            db.rollback()
            print(f"Error during club seeding commit: {e}")
            print("Rolling back changes.")
        except Exception as e:
            db.rollback()
            print(f"An unexpected error occurred during club seeding: {e}")
            print("Rolling back changes.")

if __name__ == "__main__":
    seed_clubs()
