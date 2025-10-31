"""Test that new Routing and Batch Configuration tabs load correctly."""
import sys
from PySide6.QtWidgets import QApplication
from enhanced_gui import EnhancedNetworkGUI

def test_new_tabs():
    """Test that new tabs exist in EnhancedNetworkGUI."""
    app = QApplication(sys.argv)
    gui = EnhancedNetworkGUI()
    
    # Check tab count
    tab_count = gui.tab_widget.count()
    print(f"Total tabs: {tab_count}")
    assert tab_count == 5, f"❌ Expected 5 tabs, got {tab_count}"
    print("✅ GUI has 5 tabs")
    
    # Check tab titles
    tab_titles = []
    for i in range(tab_count):
        title = gui.tab_widget.tabText(i)
        tab_titles.append(title)
        print(f"  Tab {i}: {title}")
    
    # Check that routing and batch tabs exist
    assert hasattr(gui, 'routing_tab'), "❌ Routing tab not found"
    print("✅ Routing tab exists")
    
    assert hasattr(gui, 'batch_tab'), "❌ Batch configuration tab not found"
    print("✅ Batch configuration tab exists")
    
    # Check tab names contain expected text
    tab_text = " ".join(tab_titles).lower()
    assert 'routing' in tab_text, "❌ 'Routing' not in tab titles"
    assert 'batch' in tab_text or 'configuration' in tab_text, "❌ 'Batch' or 'Configuration' not in tab titles"
    
    print("\n✅ All new tabs are present!")
    print("✅ v2.0.0 now has Advanced Routing and Batch Configuration in GUI!")
    
    return True

if __name__ == "__main__":
    try:
        test_new_tabs()
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
