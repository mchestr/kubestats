"""
Change detection logic for comparing repository states
"""

from typing import Any

from kubestats.models import KubernetesResource

from .models import ChangeSet, ResourceChange, ResourceData


class ChangeDetector:
    """Detects changes between current database state and filesystem state"""

    def detect_changes(
        self,
        current: dict[str, KubernetesResource],
        filesystem: dict[str, ResourceData],
    ) -> ChangeSet:
        """Detect all types of changes between current state and filesystem"""

        changes = ChangeSet()

        # Find created resources (in filesystem but not in DB)
        for resource_key, resource_data in filesystem.items():
            if resource_key not in current:
                changes.created.append(
                    ResourceChange(
                        type="CREATED",
                        resource_data=resource_data,
                        file_hash_after=resource_data.file_hash,
                    )
                )

        # Find deleted resources (in DB but not in filesystem)
        for resource_key, resource in current.items():
            if resource_key not in filesystem:
                changes.deleted.append(
                    ResourceChange(
                        type="DELETED",
                        existing_resource=resource,
                        file_hash_before=resource.file_hash,
                    )
                )

        # Find modified resources (different file hash)
        for resource_key, resource_data in filesystem.items():
            if resource_key in current:
                existing = current[resource_key]
                if existing.file_hash != resource_data.file_hash:
                    # Detailed change analysis
                    detailed_changes = self.analyze_detailed_changes(
                        existing.spec, resource_data.spec
                    )

                    changes.modified.append(
                        ResourceChange(
                            type="MODIFIED",
                            existing_resource=existing,
                            resource_data=resource_data,
                            file_hash_before=existing.file_hash,
                            file_hash_after=resource_data.file_hash,
                            detailed_changes=detailed_changes,
                        )
                    )

        return changes

    def analyze_detailed_changes(
        self, old_spec: dict[str, Any], new_spec: dict[str, Any]
    ) -> list[str]:
        """Analyze detailed changes between resource specifications"""
        changes = []

        def compare_nested(old_dict, new_dict, path="spec"):
            """Recursively compare nested dictionaries"""
            all_keys = set(old_dict.keys()) | set(new_dict.keys())

            for key in all_keys:
                current_path = f"{path}.{key}"

                if key not in old_dict:
                    changes.append(f"{current_path} (added)")
                elif key not in new_dict:
                    changes.append(f"{current_path} (removed)")
                elif old_dict[key] != new_dict[key]:
                    if isinstance(old_dict[key], dict) and isinstance(
                        new_dict[key], dict
                    ):
                        compare_nested(old_dict[key], new_dict[key], current_path)
                    else:
                        changes.append(current_path)

        compare_nested(old_spec, new_spec)
        return changes
