#!/usr/bin/env python3
"""
Add sample data to database for testing
"""

import sys
from datetime import datetime
from src.database import db
from src.models import Financier, EntityMapping, ActiveStatus

def add_sample_data():
    """Add sample financiers and entity mappings"""
    
    print("Adding sample data to database...")
    print()
    
    # Sample financiers
    financiers_data = [
        {
            "name": "PT Sumber Makmur Indah",
            "email": "finance@smi.co.id",
            "entities": ["SMI", "PT SMI", "Sumber Makmur"]
        },
        {
            "name": "PT Perdana Bangun Sejahtera",
            "email": "accounting@pbs.co.id",
            "entities": ["PBS", "PT PBS", "Perdana Bangun"]
        },
        {
            "name": "CV Mitra Usaha Bersama",
            "email": "admin@mub.co.id",
            "entities": ["MUB", "CV MUB", "Mitra Usaha"]
        }
    ]
    
    try:
        with db.get_session() as session:
            for data in financiers_data:
                # Check if financier already exists
                existing = session.query(Financier).filter_by(email_address=data["email"]).first()
                
                if existing:
                    print(f"⚠️  Financier already exists: {data['name']} ({data['email']})")
                    financier = existing
                else:
                    # Create financier
                    financier = Financier(
                        name=data["name"],
                        email_address=data["email"],
                        active_status=ActiveStatus.ACTIVE
                    )
                    session.add(financier)
                    session.flush()  # Get the ID
                    print(f"✅ Added financier: {data['name']} ({data['email']})")
                
                # Add entity mappings
                for entity_name in data["entities"]:
                    existing_mapping = session.query(EntityMapping).filter_by(
                        entity_name=entity_name,
                        financier_id=financier.financier_id
                    ).first()
                    
                    if existing_mapping:
                        print(f"   ⚠️  Mapping already exists: {entity_name} -> {data['name']}")
                    else:
                        mapping = EntityMapping(
                            entity_name=entity_name,
                            financier_id=financier.financier_id,
                            authorized_date=datetime.utcnow()
                        )
                        session.add(mapping)
                        print(f"   ✅ Mapped entity: {entity_name} -> {data['name']}")
            
            # Commit happens automatically when exiting context manager
        
        print()
        print("="*60)
        print("🎉 Sample data added successfully!")
        print("="*60)
        print()
        print("Summary:")
        print(f"  - {len(financiers_data)} financiers")
        print(f"  - {sum(len(f['entities']) for f in financiers_data)} entity mappings")
        print()
        print("You can now test the system with:")
        print("  python main.py run")
        print()
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    add_sample_data()
