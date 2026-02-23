
try:
    import azure.communication.callautomation as callautomation
    print("Direct exports:", dir(callautomation))
    
    # Check if inside models submodule
    import azure.communication.callautomation.models as models
    print("\nModels exports:", dir(models))

    from azure.communication.callautomation import TeamsMeetingLinkLocator
    print("Import successful!")
except ImportError as e:
    print(f"\nImport failed: {e}")
    
    # Try to find where it is
    import pkgutil
    import azure.communication.callautomation
    print("\nPackage path:", azure.communication.callautomation.__path__)
    
    # Check if there is a 'teams_meeting_link_locator' or similar
    
except Exception as e:
    print(f"Other error: {e}")
