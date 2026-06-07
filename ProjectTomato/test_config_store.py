from config_store import ConfigStore

def TestConfigStore():
    """
    Simple smoke test:
    Loads Hero + Cernium and dumps results to console.
    """

    # Make sure these keys exist in your project
    class_choice = "Hero"
    area_choice = "Odium"

    # IMPORTANT: ensure map key exists
    # (adjust if your actual mapping differs)
    store = ConfigStore()

    # Load data
    store.load_map(area_choice)
    store.load_class(class_choice, area_choice)

    # Dump everything
    print("\n===== CONFIG STORE DUMP =====")
    print("MAP DATA:")
    print(store.get_map_data())

    print("\nROTATION DATA:")
    print(store.get_rotation_data())

    print("\nSETUP INFO:")
    print(store.get_setup_info())

    print("\nCLASS KEY:")
    print(store.get_class_key())

    print("\nAREA KEY:")
    print(store.get_area_key())

    print("\nLOADED MAP:")
    print(store.get_loaded_map())

    print("=============================\n")

    assert True

if __name__ == "__main__":
	TestConfigStore()
