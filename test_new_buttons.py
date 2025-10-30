"""Quick test to verify new Undo and Enable/Disable adapter buttons are present."""
import sys
from PySide6.QtWidgets import QApplication
from enhanced_gui import OriginalNetworkTab

def test_new_buttons():
    """Test that new buttons exist in OriginalNetworkTab."""
    app = QApplication(sys.argv)
    tab = OriginalNetworkTab()
    
    # Check that buttons exist
    assert hasattr(tab, 'undo_btn'), "❌ Undo button not found"
    print("✅ Undo button exists")
    
    assert hasattr(tab, 'enable_adapter_btn'), "❌ Enable adapter button not found"
    print("✅ Enable adapter button exists")
    
    assert hasattr(tab, 'disable_adapter_btn'), "❌ Disable adapter button not found"
    print("✅ Disable adapter button exists")
    
    # Check button texts (should be English by default)
    undo_text = tab.undo_btn.text()
    print(f"  Undo button text: '{undo_text}'")
    assert undo_text, "❌ Undo button has no text"
    
    enable_text = tab.enable_adapter_btn.text()
    print(f"  Enable button text: '{enable_text}'")
    assert enable_text, "❌ Enable button has no text"
    
    disable_text = tab.disable_adapter_btn.text()
    print(f"  Disable button text: '{disable_text}'")
    assert disable_text, "❌ Disable button has no text"
    
    print("\n✅ All new buttons are present and have text!")
    print("✅ v2.0.0 GUI now has Undo and Enable/Disable adapter features!")
    
    return True

if __name__ == "__main__":
    try:
        test_new_buttons()
        print("\n🎉 Test passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
