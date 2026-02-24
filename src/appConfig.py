import xml.etree.ElementTree as ET
import sys

def read_values_from_xml(file_path, parent_tag="OIL_ESTIMATOR_CONFIG"):
    # Parse XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Locate parent tag
    if root.tag != parent_tag:
        parent = root.find(parent_tag)
        if parent is None:
            raise ValueError(f"Parent tag '{parent_tag}' not found.")
    else:
        parent = root

    results = {}

    # Iterate over direct children
    for child in parent:
        value = child.get("value")
        if value is not None:
            results[child.tag] = value

    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_xml_values.py <xml_file>")
        sys.exit(1)

    xml_file = sys.argv[1]
    extracted = read_values_from_xml(xml_file)

    # Print dictionary contents
    for tag, value in extracted.items():
        print(f"{tag}: {value}")