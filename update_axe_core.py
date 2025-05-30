from pathlib import Path
from urllib.request import urlopen

def main():
    print("Update Axe-Core Javascript...")
    axe_location = "https://unpkg.com/axe-core@latest/axe.min.js"
    axe_file = Path(__file__).parent / "src" / "axe-core" / "axe.min.js"


    # download the axe.min.js file
    try:
        response = urlopen(axe_location)
        with open(axe_file, "wb") as file:
            file.write(response.read())
        print(f"Axe-Core updated successfully at {axe_file}")
    except Exception as e:
        print(f"Failed to update Axe-Core: {e}")
        return


if __name__ == "__main__":
    main()
