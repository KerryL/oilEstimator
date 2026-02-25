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
            if child.tag == 'TO_EMAIL':
                if child.tag not in results.keys():
                    results[child.tag] = []
                results[child.tag].append(value)
            else:
                results[child.tag] = value

    return results

def write_to_xml(file_path, value,
                         parent_tag="OIL_ESTIMATOR_DATES",
                         child_tag="LAST_EMAIL_SENT"):

    # Create parent element
    parent = ET.Element(parent_tag)

    # Create child element with value attribute
    child = ET.SubElement(parent, child_tag)
    child.set("value", str(value))

    # Create tree and write to file
    tree = ET.ElementTree(parent)
    tree.write(file_path, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_xml_values.py <xml_file>")
        sys.exit(1)

    xml_file = sys.argv[1]
    extracted = read_values_from_xml(xml_file)

    # Print dictionary contents
    for tag, value in extracted.items():
        print(f"{tag}: {value}")