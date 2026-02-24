"""
Advanced Compatibility Demo

This script demonstrates schema evolution scenarios in detail.
Shows what happens when schemas change over time.
"""

import sys
from pathlib import Path

# Try to import protobuf
try:
    import user_pb2
    PROTOBUF_AVAILABLE = True
except ImportError:
    PROTOBUF_AVAILABLE = False
    print("⚠️  Protocol Buffers not available. Run setup.sh first.")
    print("   This demo requires generated protobuf code.")
    sys.exit(1)


def scenario_1_add_field():
    """Scenario 1: Adding a new field (backward compatible)"""
    print("="*80)
    print("SCENARIO 1: Adding a New Field (Backward Compatible)")
    print("="*80)
    
    print("\n📝 Situation:")
    print("   - Version 1: User has {id, name}")
    print("   - Version 2: User has {id, name, email}")
    print("   - Question: Can new code read old data?")
    
    # Simulate old data (no email field)
    old_user = user_pb2.User()
    old_user.id = 1
    old_user.name = "Alice"
    # email is not set (old schema didn't have it)
    
    old_data = old_user.SerializeToString()
    print(f"\n   Old data written: {len(old_data)} bytes")
    print(f"   Fields: id={old_user.id}, name='{old_user.name}'")
    
    # New code reads old data
    new_user = user_pb2.User()
    new_user.ParseFromString(old_data)
    
    print("\n✅ New code reading old data:")
    print(f"   id: {new_user.id}")
    print(f"   name: '{new_user.name}'")
    print(f"   email: '{new_user.email}' (empty - default value)")
    print("\n   ✓ SUCCESS: Backward compatible!")
    print("   Reason: New fields get default values (empty string for strings)")


def scenario_2_remove_field():
    """Scenario 2: Removing a field (forward compatible if done right)"""
    print("\n" + "="*80)
    print("SCENARIO 2: Removing a Field (Forward Compatible)")
    print("="*80)
    
    print("\n📝 Situation:")
    print("   - Version 1: User has {id, name, age}")
    print("   - Version 2: User has {id, name} (age removed)")
    print("   - Question: Can old code read new data?")
    
    # Simulate new data (no age field - it was removed)
    new_user = user_pb2.User()
    new_user.id = 2
    new_user.name = "Bob"
    # age is not set (new schema removed it)
    
    new_data = new_user.SerializeToString()
    print(f"\n   New data written: {len(new_data)} bytes")
    print(f"   Fields: id={new_user.id}, name='{new_user.name}'")
    
    # Old code reads new data (simulate by checking if age exists)
    old_code_user = user_pb2.User()
    old_code_user.ParseFromString(new_data)
    
    print("\n✅ Old code reading new data:")
    print(f"   id: {old_code_user.id}")
    print(f"   name: '{old_code_user.name}'")
    print(f"   age: {old_code_user.age} (0 - default value for int32)")
    print("\n   ✓ SUCCESS: Forward compatible!")
    print("   Reason: Missing fields get default values")
    print("   ⚠️  WARNING: Old code must handle default values correctly!")


def scenario_3_change_field_number():
    """Scenario 3: Changing field number (BREAKS compatibility!)"""
    print("\n" + "="*80)
    print("SCENARIO 3: Changing Field Number (BREAKS COMPATIBILITY!)")
    print("="*80)
    
    print("\n📝 Situation:")
    print("   - Version 1: User has {id=1, name=2}")
    print("   - Version 2: User has {id=1, name=3} (changed name from 2 to 3)")
    print("   - Question: What happens?")
    
    print("\n❌ DISASTER:")
    print("   - Old data has name at field number 2")
    print("   - New code expects name at field number 3")
    print("   - Result: Name field is lost or corrupted!")
    print("\n   ⚠️  NEVER CHANGE FIELD NUMBERS!")
    print("   This is a BREAKING CHANGE that cannot be fixed easily.")


def scenario_4_optional_vs_required():
    """Scenario 4: Understanding proto3 optional fields"""
    print("\n" + "="*80)
    print("SCENARIO 4: Optional Fields in proto3")
    print("="*80)
    
    print("\n📝 Key Point:")
    print("   In proto3, ALL fields are optional by default!")
    print("   This is different from proto2 where fields could be required.")
    
    user1 = user_pb2.User()
    user1.id = 1
    # name is not set
    
    user2 = user_pb2.User()
    user2.id = 2
    user2.name = "Alice"
    
    print("\n   User 1: id=1, name='' (empty - default)")
    print("   User 2: id=2, name='Alice'")
    print("\n   Both are valid! Missing fields get default values:")
    print("   - strings: '' (empty string)")
    print("   - numbers: 0")
    print("   - booleans: false")
    print("   - repeated: [] (empty list)")


def scenario_5_nested_messages():
    """Scenario 5: Evolution with nested messages"""
    print("\n" + "="*80)
    print("SCENARIO 5: Nested Message Evolution")
    print("="*80)
    
    print("\n📝 Situation:")
    print("   - User has nested UserMetadata")
    print("   - Metadata evolves independently")
    
    # Create user with metadata
    user = user_pb2.User()
    user.id = 3
    user.name = "Charlie"
    user.metadata.created_at = "2024-01-01"
    user.metadata.last_login = "2024-01-15"
    # settings not set (could be added later)
    
    data = user.SerializeToString()
    
    # Read back
    user2 = user_pb2.User()
    user2.ParseFromString(data)
    
    print("\n✅ Nested message handling:")
    print(f"   User: id={user2.id}, name='{user2.name}'")
    print(f"   Metadata: created_at='{user2.metadata.created_at}'")
    print(f"   Metadata: last_login='{user2.metadata.last_login}'")
    print(f"   Settings: {dict(user2.metadata.settings)} (empty - can add later)")
    print("\n   ✓ Nested messages evolve independently")


def main():
    """Run all compatibility scenarios."""
    print("\n" + "="*80)
    print("PROTOCOL BUFFERS: ADVANCED COMPATIBILITY DEMO")
    print("="*80)
    print("\nThis demo shows real-world schema evolution scenarios.")
    print("You'll see what works, what breaks, and why.\n")
    
    scenario_1_add_field()
    scenario_2_remove_field()
    scenario_3_change_field_number()
    scenario_4_optional_vs_required()
    scenario_5_nested_messages()
    
    print("\n" + "="*80)
    print("COMPATIBILITY RULES SUMMARY")
    print("="*80)
    print("""
✅ SAFE CHANGES (Maintain Compatibility):
   1. Add new field with new field number
   2. Remove optional field (if old code handles defaults)
   3. Change field name (keep same field number)

❌ BREAKING CHANGES (Lose Compatibility):
   1. Change field number
   2. Change field type (int32 → string)
   3. Make optional field required (proto2 only)

⚠️  REQUIRES MIGRATION:
   1. Remove required field
   2. Change field semantics significantly
   3. Rename field (use aliases if possible)

🔑 GOLDEN RULE:
   Field numbers are the identity of fields.
   Once assigned, NEVER change them!
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
