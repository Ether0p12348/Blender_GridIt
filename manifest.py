import tomllib
import pathlib
from dataclasses import dataclass
from typing import List, Dict, Optional

MANIFEST_PATH = pathlib.Path(__file__).parent / "blender_manifest.toml"

@dataclass(frozen=True)
class BuildSettings:
    paths: Optional[List[str]] = None
    paths_exclude_pattern: Optional[List[str]] = None

@dataclass(frozen=True)
class Manifest:
    id: str
    version: str
    name: str
    tagline: str
    maintainer: str
    type: str
    blender_version_min: str
    license: List[str]
    permissions: Dict[str, str]

    tags: Optional[List[str]] = None
    website: Optional[str] = None
    copyright: Optional[List[str]] = None
    blender_version_max: Optional[str] = None
    platforms: Optional[List[str]] = None
    wheels: Optional[List[str]] = None
    build: Optional[BuildSettings] = None


    @classmethod
    def from_toml(cls, path: pathlib.Path) -> "Manifest":
        with path.open("rb") as f:
            data = tomllib.load(f)

        build_data = data.get("build")
        build = BuildSettings(
            paths=build_data.get("paths", []),
            paths_exclude_pattern=build_data.get("paths_exclude_pattern", [])
        ) if build_data else None

        return cls(
            id=data["id"],
            version=data["version"],
            name=data["name"],
            tagline=data["tagline"],
            maintainer=data["maintainer"],
            type=data["type"],
            blender_version_min=data["blender_version_min"],
            license=data.get("license", []),
            permissions=data.get("permissions", {}),
            tags=data.get("tags", []),
            website=data.get("website"),
            copyright=data.get("copyright", []),
            wheels=data.get("wheels", []),
            build=build,

        )

manifest = Manifest.from_toml(MANIFEST_PATH)