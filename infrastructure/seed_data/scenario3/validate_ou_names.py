"""LZA Configuration Validator - Validates OU names against AWS Organizations.

This script reads accounts-config.yaml and verifies that all referenced
organizational unit names exist in the AWS Organization.
"""

import sys
import yaml
import boto3


def get_all_ou_names():
    """Retrieve all organizational unit names from AWS Organizations."""
    client = boto3.client("organizations")
    ou_names = []

    try:
        # Get the root
        roots = client.list_roots()["Roots"]
        if not roots:
            print("ERROR: No organization root found")
            sys.exit(1)

        root_id = roots[0]["Id"]

        # Recursively get all OUs
        def list_ous(parent_id, prefix=""):
            paginator = client.get_paginator(
                "list_organizational_units_for_parent"
            )
            for page in paginator.paginate(ParentId=parent_id):
                for ou in page["OrganizationalUnits"]:
                    full_name = f"{prefix}{ou['Name']}" if prefix else ou["Name"]
                    ou_names.append(full_name)
                    list_ous(ou["Id"], f"{full_name}/")

        list_ous(root_id)

    except Exception as e:
        print(f"ERROR: Failed to retrieve OUs from AWS Organizations: {e}")
        sys.exit(1)

    return ou_names


def get_referenced_ou_names(config_path):
    """Extract all OU names referenced in accounts-config.yaml."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    ou_names = set()

    # Check mandatory accounts
    for account in config.get("mandatoryAccounts", []):
        if "organizationalUnit" in account:
            ou_names.add(account["organizationalUnit"])

    # Check workload accounts
    for account in config.get("workloadAccounts", []):
        if "organizationalUnit" in account:
            ou_names.add(account["organizationalUnit"])

    return ou_names


def main():
    """Validate OU names in accounts-config.yaml against AWS Organizations."""
    config_path = "accounts-config.yaml"

    print(f"Reading configuration from {config_path}...")
    referenced_ous = get_referenced_ou_names(config_path)
    print(f"Found referenced OUs: {referenced_ous}")

    print("Retrieving organizational units from AWS Organizations...")
    valid_ous = get_all_ou_names()
    print(f"Valid OUs in organization: {valid_ous}")

    # Check for invalid OU references
    invalid_ous = []
    for ou in referenced_ous:
        if ou not in valid_ous:
            invalid_ous.append(ou)

    if invalid_ous:
        print("\n" + "=" * 60)
        print("VALIDATION FAILED: Invalid organizational unit references found")
        print("=" * 60)
        for ou in invalid_ous:
            print(f"  ERROR: OU '{ou}' does not exist in the organization")
        print(f"\nValid organizational units are: {valid_ous}")
        print("\nPlease update accounts-config.yaml with valid OU names.")
        sys.exit(1)
    else:
        print("\nVALIDATION PASSED: All OU references are valid.")


if __name__ == "__main__":
    main()
